#!/usr/bin/env python3
"""
HoneypotIntel Dashboard
Automatically fetches Cowrie logs + AbuseIPDB-enriched attacker data
from the EC2 honeypot over SSH, then serves an interactive dashboard.
"""

import json
import glob
import os
import time
from collections import Counter, defaultdict
from datetime import datetime

import pandas as pd
import paramiko
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Configuration — override any of these with environment variables if needed.
# Defaults match this project's honeypot setup.
# ---------------------------------------------------------------------------
EC2_HOST = os.environ.get("EC2_HOST", "3.110.222.106")
EC2_USER = os.environ.get("EC2_USER", "ec2-user")
EC2_KEY_PATH = os.environ.get("EC2_KEY_PATH", r"C:\Cowrie honeypot\sentinelx-honeypot.pem")
EC2_REMOTE_ENRICHED = os.environ.get(
    "EC2_REMOTE_ENRICHED", "/home/ec2-user/SentinelX-Platform/enriched_attacks.csv"
)
EC2_REMOTE_LOG_DIR = os.environ.get("EC2_REMOTE_LOG_DIR", "/opt/cowrie/var/log/cowrie/")

# How long to trust locally-cached data before re-fetching over SSH (seconds).
CACHE_SECONDS = int(os.environ.get("CACHE_SECONDS", "300"))  # 5 minutes

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
ENRICHED_CSV = os.path.join(DATA_DIR, "enriched_attacks.csv")
COWRIE_LOG_PATTERN = os.path.join(DATA_DIR, "cowrie.json*")

os.makedirs(DATA_DIR, exist_ok=True)

_last_fetch_time = 0
_last_fetch_status = {"ok": None, "message": "Not yet fetched", "when": None}


def fetch_remote_data(force=False):
    """
    Connect to the EC2 honeypot over SSH/SFTP and pull down the latest
    enriched_attacks.csv and Cowrie log files. Skips the fetch if the
    local cache is still fresh, unless force=True.
    """
    global _last_fetch_time, _last_fetch_status

    if not force and (time.time() - _last_fetch_time) < CACHE_SECONDS:
        return _last_fetch_status  # cache still fresh, nothing to do

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=EC2_HOST,
            username=EC2_USER,
            key_filename=EC2_KEY_PATH,
            timeout=10,
        )
        sftp = ssh.open_sftp()

        # Pull the enriched CSV
        sftp.get(EC2_REMOTE_ENRICHED, ENRICHED_CSV)

        # Pull every Cowrie log file (today's + all rotated days)
        remote_files = sftp.listdir(EC2_REMOTE_LOG_DIR)
        log_files = [f for f in remote_files if f.startswith("cowrie.json")]
        for fname in log_files:
            remote_path = EC2_REMOTE_LOG_DIR.rstrip("/") + "/" + fname
            local_path = os.path.join(DATA_DIR, fname)
            sftp.get(remote_path, local_path)

        sftp.close()
        ssh.close()

        _last_fetch_time = time.time()
        _last_fetch_status = {
            "ok": True,
            "message": f"Fetched enriched CSV + {len(log_files)} log files",
            "when": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        _last_fetch_status = {
            "ok": False,
            "message": f"Fetch failed: {e}. Showing last known local data.",
            "when": datetime.utcnow().isoformat() + "Z",
        }
        # Don't update _last_fetch_time on failure, so it retries sooner

    return _last_fetch_status


def load_enriched_data():
    if not os.path.exists(ENRICHED_CSV):
        return pd.DataFrame()
    df = pd.read_csv(ENRICHED_CSV)
    for col in ["Attempts", "AbuseScore", "TotalReports"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_cowrie_events():
    events = []
    log_files = sorted(glob.glob(COWRIE_LOG_PATTERN))
    for path in log_files:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def build_dashboard_data():
    df = load_enriched_data()
    events = load_cowrie_events()

    connect_events = [e for e in events if e.get("eventid") == "cowrie.session.connect"]
    day_counts = Counter()
    for e in connect_events:
        ts = e.get("timestamp", "")
        day = ts[:10] if len(ts) >= 10 else "unknown"
        day_counts[day] += 1
    timeline = sorted(day_counts.items())

    event_counts = Counter(e.get("eventid", "unknown") for e in events)
    event_breakdown = event_counts.most_common()

    commands = [
        {
            "input": e.get("input", ""),
            "src_ip": e.get("src_ip", "unknown"),
            "timestamp": e.get("timestamp", ""),
        }
        for e in events
        if e.get("eventid") == "cowrie.command.input"
    ]

    top_offenders = []
    countries = Counter()
    score_buckets = {"critical (90-100)": 0, "elevated (40-89)": 0, "low (1-39)": 0, "clean (0)": 0, "unscored": 0}
    total_reports_sum = 0

    if not df.empty:
        scored = df.dropna(subset=["AbuseScore"])
        for _, row in scored.iterrows():
            score = row["AbuseScore"]
            if score >= 90:
                score_buckets["critical (90-100)"] += 1
            elif score >= 40:
                score_buckets["elevated (40-89)"] += 1
            elif score > 0:
                score_buckets["low (1-39)"] += 1
            else:
                score_buckets["clean (0)"] += 1
        score_buckets["unscored"] = int(df["AbuseScore"].isna().sum())

        for _, row in df.iterrows():
            c = row.get("Country")
            if isinstance(c, str) and c not in ("N/A", ""):
                countries[c] += 1

        total_reports_sum = int(scored["TotalReports"].fillna(0).sum())

        top = df.sort_values(by="TotalReports", ascending=False, na_position="last").head(12)
        for _, row in top.iterrows():
            country_val = row.get("Country")
            isp_val = row.get("UsageType")
            top_offenders.append({
                "ip": row.get("IP", ""),
                "score": None if pd.isna(row.get("AbuseScore")) else int(row.get("AbuseScore")),
                "reports": None if pd.isna(row.get("TotalReports")) else int(row.get("TotalReports")),
                "country": "N/A" if pd.isna(country_val) else country_val,
                "isp": "N/A" if pd.isna(isp_val) else isp_val,
                "attempts": None if pd.isna(row.get("Attempts")) else int(row.get("Attempts")),
            })

    total_ips = int(df.shape[0]) if not df.empty else 0
    scored_count = int(df["AbuseScore"].notna().sum()) if not df.empty else 0
    critical_pct = round((score_buckets["critical (90-100)"] / scored_count) * 100, 1) if scored_count else 0

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "fetch_status": _last_fetch_status,
        "totals": {
            "total_connections": len(connect_events),
            "unique_ips": total_ips,
            "scored_ips": scored_count,
            "critical_pct": critical_pct,
            "total_reports_sum": total_reports_sum,
            "commands_typed": len(commands),
            "countries_seen": len(countries),
        },
        "timeline": timeline,
        "event_breakdown": event_breakdown,
        "top_offenders": top_offenders,
        "countries": countries.most_common(10),
        "score_buckets": score_buckets,
        "commands": commands[:25],
        "recent_connections": [
            {"src_ip": e.get("src_ip"), "timestamp": e.get("timestamp"), "dst_port": e.get("dst_port")}
            for e in connect_events[-12:][::-1]
        ],
    }


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/data")
def api_data():
    fetch_remote_data()  # auto-fetches if cache is stale; instant if still fresh
    data = build_dashboard_data()
    return app.response_class(
        json.dumps(data, allow_nan=False, default=str),
        mimetype="application/json",
    )


@app.route("/api/refresh")
def api_refresh():
    """Manual 'Refresh Now' button hits this — forces an immediate re-fetch."""
    status = fetch_remote_data(force=True)
    payload = {"fetch_status": status, "data": build_dashboard_data()}
    return app.response_class(
        json.dumps(payload, allow_nan=False, default=str),
        mimetype="application/json",
    )


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
