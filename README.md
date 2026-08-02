# HoneypotIntel

> **A live, cloud-hosted SSH honeypot with an automated threat intelligence pipeline — running unattended on AWS, catching real internet attack traffic, and surfacing genuine malware deployment attempts.**

![Status](https://img.shields.io/badge/Status-LIVE-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-AWS-orange)

📄 **[Read the case study: catching a live malware deployment attempt →](./CASE_STUDY.md)**

---

## Table of Contents

- [Overview](#overview)
- [Live Results](#live-results)
- [Featured Finding: Malware Deployment Attempt](#featured-finding-malware-deployment-attempt)
- [Architecture](#architecture)
- [Dashboard](#dashboard)
- [Pipeline Phases](#pipeline-phases)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Technologies](#technologies)
- [Roadmap](#roadmap)
- [Author](#author)

---

## Overview

**HoneypotIntel** is a Security Operations Center (SOC) platform built around a real, internet-facing SSH honeypot. It's not a simulation or a course exercise — it's a live decoy server on AWS that has been catching genuine attack traffic from strangers scanning the internet, continuously, for weeks.

- ✅ Cloud infrastructure deployment (AWS EC2)
- ✅ Live threat capture (Cowrie SSH honeypot)
- ✅ Automated threat intelligence enrichment (AbuseIPDB API)
- ✅ Custom detection rule development
- ✅ Automated incident response playbooks
- ✅ Executive-level threat reporting
- ✅ Custom real-time dashboard (Flask + Plotly)
- ✅ Fully automated pipeline — no manual intervention required

---

## Live Results

Real numbers, captured by the honeypot, updated automatically every night:

| Metric | Value |
|---|---|
| Connections logged | 2,000+ |
| Unique attacker IPs | 950+ |
| Scored critical (AbuseIPDB 90–100) | 85.5% |
| Cumulative abuse reports across all IPs | 229,000+ |
| Origin countries | 28 |
| Interactive command sessions (past automated scanning) | 16 |
| Honeypot uptime | 18+ days and counting |

Most traffic is automated background noise — bots trying default credentials and moving on. The small fraction that goes further is where things get interesting. See the [case study](./CASE_STUDY.md) for the full breakdown.

---

## Featured Finding: Malware Deployment Attempt

On **July 18**, an attacker at `47.237.30.186` went past credential-stuffing and attempted a real, multi-stage payload deployment: a probing command, a `curl`/`wget` download of a binary with a fallback strategy, `chmod +x` and execution, a staged credential file, and UPX-packing artifacts consistent with antivirus evasion.

Because it ran inside Cowrie's simulated shell, nothing was actually compromised — but every command was logged in full.

**[→ Full technical breakdown with the actual logged commands](./CASE_STUDY.md)**

---

## Architecture

                INTERNET ATTACKERS
                        ↓
              AWS EC2 (ap-south-1)
               3.110.222.106:2222
                        ↓
              Cowrie SSH Honeypot
                        ↓
     JSON attack logs (/opt/cowrie/var/log/cowrie/)
                        ↓
      ┌───────────────────────────────────┐
      │   cron (daily, 2:00 AM UTC)       │
      │   → enrichment.py                 │
      │     • Parses all rotated logs     │
      │     • Queries AbuseIPDB per IP    │
      │     • Writes enriched_attacks.csv │
      └───────────────────────────────────┘
                        ↓
      ┌───────────────────────────────────┐
      │   Flask dashboard (local/live)    │
      │   → auto-fetches over SSH         │
      │     (paramiko), 5-min cache       │
      │   → renders charts + top offenders│
      │     table + live command feed     │
      └───────────────────────────────────┘
                        ↓
     detection_rules.py → automation.py → reporting.py
     (pattern detection → incident playbooks → exec report)
     The entire loop — capture, enrichment, and dashboard refresh — runs unattended. No manual `scp` or script triggering required.

---

## Dashboard
<img width="1763" height="4655" alt="image" src="https://github.com/user-attachments/assets/81b1d039-b6c6-4271-b12f-df929db10a94" />


A custom-built Flask + Plotly dashboard visualizes the honeypot's data in real time: connection volume over time, threat-confidence distribution, origin countries, event composition, a ranked top-offenders table, and a live feed of interactive attacker sessions.

*(Add a screenshot of the dashboard here — this is one of the most convincing things a visitor can see in 3 seconds.)*

---

## Pipeline Phases

| Phase | Component | What it does |
|---|---|---|
| 1 | Honeypot Deployment | Cowrie SSH honeypot on AWS EC2, capturing real internet reconnaissance |
| 2 | Threat Intelligence | `enrichment.py` — enriches every unique attacker IP against AbuseIPDB |
| 3 | Detection Engineering | `detection_rules.py` — flags port scans, version probes, brute-force patterns |
| 4 | Automated Response | `automation.py` — executes response playbooks, logs actions, generates incidents |
| 5 | Reporting | `reporting.py` — generates executive summaries and incident reports |
| 6 | Visualization | Custom Flask/Plotly dashboard, auto-synced from the honeypot over SSH |

---

## Installation

### Prerequisites
- Python 3.11+
- AWS account (Free Tier eligible)
- AbuseIPDB API key (free tier)
- Git

### Quick Start

```bash
git clone https://github.com/Eshaan49/HoneypotIntel.git
cd HoneypotIntel
pip install -r requirements.txt
```

Set your AbuseIPDB key as an environment variable (never hardcode it):

```bash
export ABUSEIPDB_API_KEY="your_key_here"
```

Run the pipeline manually, or rely on the included cron schedule for daily automated runs:

```bash
python3 enrichment.py       # Threat intelligence enrichment
python3 detection_rules.py  # Detection engine
python3 automation.py       # Automated incident response
python3 reporting.py        # Executive report generation
```

---

## Project Structure

```
HoneypotIntel/
├── README.md
├── CASE_STUDY.md           # Malware deployment finding — full write-up
├── enrichment.py           # Phase 2: threat intelligence enrichment
├── detection_rules.py      # Phase 3: detection engine
├── automation.py           # Phase 4: automated response
├── reporting.py            # Phase 5: report generation
├── enriched_attacks.csv    # Real attack data (enriched)
├── incidents.json          # Generated incidents
├── EXECUTIVE_REPORT.md     # Auto-generated report
└── wazuh_integration.py    # Early scaffold for a planned SIEM integration (see Roadmap)
```

## Technologies

| Component | Technology | Purpose |
|---|---|---|
| Honeypot | Cowrie | SSH attack capture |
| Cloud | AWS EC2 (t3.micro) | Production deployment |
| Enrichment | AbuseIPDB API | IP reputation scoring |
| Scheduling | cron | Nightly automated enrichment |
| Dashboard | Flask, Plotly, pandas, paramiko | Real-time visualization, auto-sync over SSH |
| Scripting | Python 3.11 | Automation & analysis |

---

## Roadmap

- [ ] **Public dashboard deployment** — currently runs locally, auto-syncing from the honeypot; deploying it publicly is next
- [ ] **Wazuh SIEM integration** — `wazuh_integration.py` is an early scaffold from before the project pivoted to a custom dashboard for faster iteration. Revisiting this is planned as a follow-up to demonstrate correlation-rule-based detection with an industry-standard SIEM.
- [ ] **Multi-service honeypot** — extend beyond SSH to HTTP/FTP/SMTP
- [ ] **Geographic heat map** of attack sources

---

## Author

**Eshaan Pilar**
Final-year Cybersecurity Engineering student · Building toward a SOC Analyst role
[GitHub](https://github.com/Eshaan49) | [LinkedIn](https://linkedin.com/in/eshaanpilar)

---

## License

MIT License — see LICENSE file for details.

---

**Last updated:** July 22, 2026
**Status:** Live, running unattended with daily automated enrichment
