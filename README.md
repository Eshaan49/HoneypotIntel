# SentinelX-Platform

A modular SOC (Security Operations Center) honeypot and threat intelligence platform built for incident response and attack analysis.

## Current Status: Phase 1 & 2 Complete ✓

### Phase 1: Honeypot Deployment (COMPLETE)
- **Cowrie SSH Honeypot** deployed on AWS EC2 (t3.micro, ap-south-1)
- Instance: `3.110.222.106:2222`
- Real attacks being captured
- **9-10 unique attacker IPs** detected in first 24 hours

### Phase 2: Threat Intelligence Enrichment (COMPLETE)
- Python enrichment script (`enrichment.py`) parses Cowrie logs
- Integrates with **AbuseIPDB API** for IP reputation scoring
- Outputs enriched CSV with attacker metadata
- Real attack data: `enriched_attacks.csv`

## Architecture

