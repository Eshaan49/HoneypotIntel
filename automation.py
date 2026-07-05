#!/usr/bin/env python3
"""
Phase 4: Lightweight Automation
Automated response playbooks for detected threats
"""

import json
from datetime import datetime
from collections import defaultdict

DETECTIONS_LOG = "detections.json"
INCIDENTS_LOG = "incidents.json"

def load_detections():
    """Load detections from detection_rules.py output"""
    detections = [
        {"type": "PORT_SCAN", "severity": "LOW", "src_ip": "205.210.31.154", "timestamp": "2026-07-05T02:21:15.844518Z"},
        {"type": "PORT_SCAN", "severity": "LOW", "src_ip": "94.231.206.249", "timestamp": "2026-07-05T02:40:22.549674Z"},
        {"type": "PORT_SCAN", "severity": "LOW", "src_ip": "91.230.168.251", "timestamp": "2026-07-05T02:43:32.850026Z"},
    ]
    return detections

def playbook_port_scan(detection):
    """Response playbook for port scans"""
    return {
        "incident_id": f"INC-{detection['src_ip'].replace('.', '-')}",
        "detection_type": "PORT_SCAN",
        "source_ip": detection['src_ip'],
        "severity": detection['severity'],
        "timestamp": detection['timestamp'],
        "automated_actions": [
            "LOG_ALERT: Port scan detected",
            f"WHITELIST_CHECK: {detection['src_ip']} (check if known/trusted)",
            f"ENRICHMENT: Query threat intelligence for {detection['src_ip']}",
            "MONITOR: Watch for follow-up exploitation attempts"
        ],
        "recommended_response": "Monitor - No immediate action needed (LOW severity)",
        "status": "OPEN"
    }

def playbook_brute_force(detection):
    """Response playbook for brute force attacks"""
    return {
        "incident_id": f"INC-BF-{detection['src_ip'].replace('.', '-')}",
        "detection_type": "BRUTE_FORCE",
        "source_ip": detection['src_ip'],
        "severity": detection['severity'],
        "timestamp": detection['timestamp'],
        "automated_actions": [
            "ALERT: Multiple login attempts detected",
            f"BLOCK_CANDIDATE: {detection['src_ip']} (flag for blocking)",
            f"ENRICHMENT: Full AbuseIPDB lookup for {detection['src_ip']}",
            "ESCALATE: Notify security team if MEDIUM+ severity"
        ],
        "recommended_response": "Consider blocking IP - Review before action",
        "status": "OPEN"
    }

def execute_playbooks(detections):
    """Execute response playbooks for each detection"""
    incidents = []
    
    for detection in detections:
        print(f"\n[*] Executing playbook for {detection['type']} from {detection['src_ip']}")
        
        if detection['type'] == "PORT_SCAN":
            incident = playbook_port_scan(detection)
        elif detection['type'] == "BRUTE_FORCE":
            incident = playbook_brute_force(detection)
        else:
            continue
        
        incidents.append(incident)
        
        # Print incident
        print(f"[+] Incident Created: {incident['incident_id']}")
        print(f"    Type: {incident['detection_type']}")
        print(f"    Severity: {incident['severity']}")
        print(f"    Status: {incident['status']}")
        print(f"    Automated Actions:")
        for action in incident['automated_actions']:
            print(f"      • {action}")
    
    return incidents

def save_incidents(incidents):
    """Save incidents to JSON for tracking"""
    with open(INCIDENTS_LOG, 'w') as f:
        json.dump(incidents, f, indent=2)
    print(f"\n[+] Saved {len(incidents)} incidents to {INCIDENTS_LOG}")

def main():
    print("[*] Phase 4: Lightweight Automation")
    print("[*] Loading detections...")
    
    detections = load_detections()
    print(f"[+] Found {len(detections)} detections")
    
    print("\n[*] Executing automated response playbooks...")
    print("=" * 60)
    
    incidents = execute_playbooks(detections)
    
    print("\n" + "=" * 60)
    print(f"[+] Total Incidents Created: {len(incidents)}")
    
    save_incidents(incidents)
    
    print("\n[*] Automation complete. Incidents logged and ready for analyst review.")

if __name__ == "__main__":
    main()
