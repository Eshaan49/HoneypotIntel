#!/usr/bin/env python3
"""
Phase 3: Detection Engineering
Identifies attack patterns from Cowrie logs
"""

import json
from collections import defaultdict
from datetime import datetime

COWRIE_LOG = "/opt/cowrie/var/log/cowrie/cowrie.json"

def parse_logs():
    """Parse Cowrie logs and extract sessions"""
    sessions = defaultdict(list)
    try:
        with open(COWRIE_LOG) as f:
            for line in f:
                try:
                    event = json.loads(line)
                    session_id = event.get("session")
                    if session_id:
                        sessions[session_id].append(event)
                except:
                    pass
    except FileNotFoundError:
        print(f"Log file not found: {COWRIE_LOG}")
    return sessions

def detect_port_scan(sessions):
    """Detect port scanning: quick connects + closes"""
    detections = []
    for session_id, events in sessions.items():
        if len(events) >= 2:
            connect = next((e for e in events if e.get("eventid") == "cowrie.session.connect"), None)
            close = next((e for e in events if e.get("eventid") == "cowrie.session.closed"), None)
            
            if connect and close:
                duration = close.get("duration_ms", 0)
                src_ip = connect.get("src_ip")
                
                # Port scan = quick connect + disconnect (< 1 second)
                if duration < 1000:
                    detections.append({
                        "type": "PORT_SCAN",
                        "severity": "LOW",
                        "src_ip": src_ip,
                        "duration_ms": duration,
                        "timestamp": connect.get("timestamp"),
                        "reason": "Quick connect + disconnect pattern (version probe)"
                    })
    return detections

def detect_brute_force(sessions):
    """Detect brute force: multiple auth attempts"""
    detections = []
    ip_attempts = defaultdict(int)
    
    for session_id, events in sessions.items():
        for event in events:
            if event.get("eventid") == "cowrie.login.attempt":
                src_ip = event.get("src_ip")
                ip_attempts[src_ip] += 1
    
    for ip, count in ip_attempts.items():
        if count >= 3:
            detections.append({
                "type": "BRUTE_FORCE",
                "severity": "MEDIUM",
                "src_ip": ip,
                "attempt_count": count,
                "reason": f"{count} login attempts detected"
            })
    
    return detections

def main():
    print("[*] Phase 3: Detection Engineering")
    print("[*] Parsing Cowrie logs...")
    
    sessions = parse_logs()
    print(f"[+] Found {len(sessions)} sessions")
    
    # Run detections
    port_scans = detect_port_scan(sessions)
    brute_forces = detect_brute_force(sessions)
    
    all_detections = port_scans + brute_forces
    
    print(f"\n[+] Detections Found: {len(all_detections)}")
    print("=" * 60)
    
    for detection in all_detections:
        print(f"\n[!] {detection['type']} (Severity: {detection['severity']})")
        print(f"    IP: {detection['src_ip']}")
        print(f"    Reason: {detection['reason']}")
        print(f"    Time: {detection.get('timestamp', 'N/A')}")

if __name__ == "__main__":
    main()
