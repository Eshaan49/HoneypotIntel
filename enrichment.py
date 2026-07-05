#!/usr/bin/env python3
"""
SentinelX Phase 2: Threat Intelligence Enrichment
Reads Cowrie logs, enriches attacker IPs with AbuseIPDB data
"""

import json
import requests
import csv
from collections import defaultdict
from datetime import datetime

# Configuration
ABUSEIPDB_API_KEY = "067d2da62ce4cf8f06d18c99b1c21db7c8ce7f3cf28d44f4f2ca58e8de854c7e"
COWRIE_LOG_FILE = "var/log/cowrie/cowrie.json"
OUTPUT_FILE = "enriched_attacks.csv"

def query_abuseipdb(ip_address):
    """Query AbuseIPDB API for IP reputation"""
    try:
        url = "https://api.abuseipdb.com/api/v2/check"
        headers = {
            "Key": ABUSEIPDB_API_KEY,
            "Accept": "application/json"
        }
        params = {
            "ipAddress": ip_address,
            "maxAgeInDays": 90,
            "verbose": ""
        }
        response = requests.get(url, headers=headers, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {})
        else:
            print(f"AbuseIPDB API error for {ip_address}: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error querying AbuseIPDB for {ip_address}: {e}")
        return {}

def parse_cowrie_logs():
    """Parse Cowrie JSON log file and extract unique IPs"""
    ips = defaultdict(list)
    try:
        with open(COWRIE_LOG_FILE, 'r') as f:
            for line in f:
                try:
                    log_entry = json.loads(line)
                    if log_entry.get("eventid") == "cowrie.session.connect":
                        src_ip = log_entry.get("src_ip")
                        if src_ip:
                            ips[src_ip].append({
                                "timestamp": log_entry.get("timestamp"),
                                "dst_port": log_entry.get("dst_port"),
                                "username": log_entry.get("username", "N/A"),
                                "password": log_entry.get("password", "N/A")
                            })
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"Cowrie log file not found at {COWRIE_LOG_FILE}")
        print("Using mock data for testing...")
        ips = {
            "192.168.1.100": [{"timestamp": "2026-07-04T10:00:00.000000+00:00", "dst_port": 2222, "username": "root", "password": "password"}],
            "10.0.0.50": [{"timestamp": "2026-07-04T11:30:00.000000+00:00", "dst_port": 2222, "username": "admin", "password": "12345"}]
        }
    
    return ips

def enrich_and_save(ips):
    """Enrich IP data and save to CSV"""
    with open(OUTPUT_FILE, 'w', newline='') as csvfile:
        fieldnames = ['IP', 'Attempts', 'AbuseScore', 'TotalReports', 'LastReportedAt', 'Country', 'Domains', 'UsageType', 'FirstAttempt']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        print(f"\n{'IP Address':<15} {'Score':<6} {'Reports':<8} {'Country':<15}")
        print("=" * 50)
        
        for ip, attempts in sorted(ips.items()):
            print(f"Enriching {ip}...", end=" ")
            abusedb_data = query_abuseipdb(ip)
            
            if abusedb_data:
                abuse_score = abusedb_data.get("abuseConfidenceScore", 0)
                total_reports = abusedb_data.get("totalReports", 0)
                last_reported = abusedb_data.get("lastReportedAt", "N/A")
                country_code = abusedb_data.get("countryCode", "N/A")
                domains = abusedb_data.get("usageType", "N/A")
                usage_type = abusedb_data.get("isp", "N/A")
                
                print(f"Score: {abuse_score}, Reports: {total_reports}")
                
                writer.writerow({
                    'IP': ip,
                    'Attempts': len(attempts),
                    'AbuseScore': abuse_score,
                    'TotalReports': total_reports,
                    'LastReportedAt': last_reported,
                    'Country': country_code,
                    'Domains': domains,
                    'UsageType': usage_type,
                    'FirstAttempt': attempts[0]['timestamp'] if attempts else 'N/A'
                })
            else:
                print("No data found")
                writer.writerow({
                    'IP': ip,
                    'Attempts': len(attempts),
                    'AbuseScore': 'N/A',
                    'TotalReports': 'N/A',
                    'LastReportedAt': 'N/A',
                    'Country': 'N/A',
                    'Domains': 'N/A',
                    'UsageType': 'N/A',
                    'FirstAttempt': attempts[0]['timestamp'] if attempts else 'N/A'
                })

def main():
    print("[*] SentinelX Phase 2: Threat Intelligence Enrichment")
    print(f"[*] Parsing Cowrie logs from {COWRIE_LOG_FILE}")
    
    ips = parse_cowrie_logs()
    print(f"[+] Found {len(ips)} unique attacker IPs")
    
    if ips:
        print(f"[*] Enriching with AbuseIPDB data...")
        enrich_and_save(ips)
        print(f"\n[+] Results saved to {OUTPUT_FILE}")
    else:
        print("[-] No IPs found to enrich")

if __name__ == "__main__":
    main()
