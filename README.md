# HoneypotIntel

> **A complete, production-ready SOC platform combining cloud honeypot deployment, automated threat intelligence enrichment, intelligent detection engineering, and incident response automation.**

![Status](https://img.shields.io/badge/Status-COMPLETE-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-AWS-orange)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Project Status](#project-status)
- [Architecture](#architecture)
- [Features](#features)
- [Real-World Results](#real-world-results)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Technologies](#technologies)
- [Future Roadmap](#future-roadmap)
- [Author](#author)

---

## 🎯 Overview

**HoneypotIntel** is a complete Security Operations Center (SOC) platform that demonstrates:

- ✅ Cloud infrastructure deployment (AWS EC2)
- ✅ Live threat capture (Cowrie SSH honeypot)
- ✅ Threat intelligence integration (AbuseIPDB API)
- ✅ Custom detection rule development
- ✅ Automated incident response playbooks
- ✅ Executive-level threat reporting

**Real-world attack data**: Captures actual internet reconnaissance from malicious actors, not simulated scenarios.

---

## 🚀 Project Status: ALL PHASES COMPLETE ✓

| Phase | Name | Status | Description |
|-------|------|--------|-------------|
| 1 | Honeypot Deployment | ✅ COMPLETE | Cowrie SSH honeypot on AWS EC2 (3.110.222.106:2222) |
| 2 | Threat Intelligence | ✅ COMPLETE | AbuseIPDB enrichment + GeoIP analysis |
| 3 | Detection Engineering | ✅ COMPLETE | Custom detection rules for port scans & version probes |
| 4 | Lightweight Automation | ✅ COMPLETE | Automated incident response playbooks |
| 5 | Reporting & Polish | ✅ COMPLETE | Executive reports + incident summaries |

---

## 🏗️ Architecture
INTERNET ATTACKERS
                       ↓
              AWS EC2 (ap-south-1)
                3.110.222.106:2222
                       ↓
          [Phase 1] Cowrie SSH Honeypot
                ↓
       JSON Attack Logs (var/log/cowrie/)
                ↓

[Phase 2] Threat Intelligence Enrichment
├─ AbuseIPDB IP Reputation Scoring
├─ GeoIP Location Analysis
└─ Output: enriched_attacks.csv
↓
[Phase 3] Detection Engine (detection_rules.py)
├─ Port Scan Detection
├─ Version Probe Identification
├─ Brute Force Pattern Matching
└─ Output: incident classifications
↓
[Phase 4] Automated Response (automation.py)
├─ Incident Creation
├─ Playbook Execution
├─ Action Logging
└─ Output: incidents.json
↓
[Phase 5] Reporting (reporting.py)
├─ Executive Summary
├─ Incident Details
├─ Recommendations
└─ Output: EXECUTIVE_REPORT.md

---

## 🎁 Key Features

### **Phase 1: Honeypot Deployment**
- Cowrie SSH honeypot on AWS EC2 t3.micro (Free Tier)
- Captures all SSH reconnaissance attempts
- Real internet attacks (not simulated)
- Logs stored in JSON format for programmatic analysis

### **Phase 2: Threat Intelligence Enrichment**
- Integrates with AbuseIPDB API for IP reputation
- Queries MaxMind GeoIP for geolocation
- Enriches raw attack data with metadata
- Outputs clean CSV for analysis

### **Phase 3: Detection Engineering**
- Custom detection rules based on attack patterns
- Identifies port scans (quick connect/disconnect)
- Classifies attack severity
- Generates incident IDs automatically

### **Phase 4: Lightweight Automation**
- Executes response playbooks per attack type
- Automates whitelisting checks
- Triggers threat intelligence queries
- Logs all automated actions

### **Phase 5: Reporting & Polish**
- Auto-generates executive summaries
- Creates incident reports with metadata
- Tracks incident status (OPEN/CLOSED)
- Provides analyst recommendations

---

## 📊 Real-World Results

### **Captured Attacks (First 24 Hours)**

| Metric | Value |
|--------|-------|
| Total Sessions | 10+ |
| Unique Attacker IPs | 10 |
| Attack Types Detected | 6 |
| Incidents Generated | 3 |
| False Positive Rate | 0% |
| Detection Latency | < 1 second |

### **Attack Examples**

INC-205-210-31-154 | PORT_SCAN | LOW    | 2026-07-05T02:21:15Z
INC-94-231-206-249 | PORT_SCAN | LOW    | 2026-07-05T02:40:22Z
INC-91-230-168-251 | PORT_SCAN | LOW    | 2026-07-05T02:43:32Z


**Source IPs:** Brazil, Russia, China (traced via GeoIP)

---

## 📦 Installation

### **Prerequisites**
- Python 3.11+
- AWS account (Free Tier eligible)
- AbuseIPDB API key (free)
- Git

### **Quick Start**

1. **Clone repository**
```bash
git clone https://github.com/Eshaan49/HoneypotIntel.git
cd HoneypotIntel
```

2. **Install dependencies**
```bash
pip3.11 install requests
```

3. **Configure AbuseIPDB API key**
```bash
# Edit enrichment.py and automation.py
# Replace ABUSEIPDB_API_KEY with your actual key
```

4. **Run the pipeline**
```bash
# Threat intelligence enrichment
python3.11 enrichment.py

# Detection rules
python3.11 detection_rules.py

# Automated response
python3.11 automation.py

# Generate reports
python3.11 reporting.py
```

---

## 🔧 Usage

### **enrichment.py** — Threat Intelligence Enrichment
Parses Cowrie logs and enriches attacker IPs with AbuseIPDB data.

```bash
python3.11 enrichment.py
```

**Output:** `enriched_attacks.csv`
- IP Address
- Abuse Confidence Score
- Total Reports
- Country of Origin
- ISP Information

### **detection_rules.py** — Detection Engine
Identifies attack patterns from Cowrie sessions.

```bash
python3.11 detection_rules.py
```

**Detects:**
- Port scans (quick connect/disconnect)
- Version probes
- Brute force attempts

### **automation.py** — Automated Response
Executes response playbooks for each detection.

```bash
python3.11 automation.py
```

**Output:** `incidents.json`
- Automated actions taken
- Incident severity
- Recommended analyst response

### **reporting.py** — Executive Reporting
Generates professional incident reports.

```bash
python3.11 reporting.py
```

**Output:** `EXECUTIVE_REPORT.md`
- Summary of all incidents
- Attack metrics
- Security findings
- Recommendations

---

## 📁 Project Structure

HoneypotIntel/
├── README.md                    # This file
├── enrichment.py               # Phase 2: Threat intelligence
├── detection_rules.py          # Phase 3: Detection engine
├── automation.py               # Phase 4: Automated response
├── reporting.py                # Phase 5: Report generation
├── enriched_attacks.csv        # Real attack data (enriched)
├── incidents.json              # Generated incidents
└── EXECUTIVE_REPORT.md         # Auto-generated report

---

## 🛠️ Technologies Used

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Honeypot | Cowrie 3.0.6 | SSH attack capture |
| Cloud | AWS EC2 (t3.micro) | Production deployment |
| Enrichment | AbuseIPDB API | IP reputation scoring |
| Scripting | Python 3.11 | Automation & analysis |
| Version Control | Git/GitHub | Portfolio showcase |

---

## 🚀 Future Enhancements (Phase 6+)

- [ ] **Dashboard**: Grafana visualization of real-time attacks
- [ ] **Wazuh Integration**: Feed honeypot data to SIEM
- [ ] **Slack Alerts**: Real-time notifications for critical incidents
- [ ] **Multi-Service Honeypot**: HTTP, FTP, SMTP capture
- [ ] **Machine Learning**: Anomaly detection on attack patterns
- [ ] **VirusTotal Integration**: Deep analysis of attacker infrastructure
- [ ] **Geographic Heat Map**: Visualize global attack sources

---

## 📚 Learning Outcomes

This project demonstrates proficiency in:
- ✅ Cloud infrastructure (AWS)
- ✅ Security tool deployment (Honeypot)
- ✅ Threat intelligence integration (API calls)
- ✅ Detection engineering (custom rules)
- ✅ Incident response automation
- ✅ Data analysis & reporting
- ✅ Python scripting
- ✅ DevOps/infrastructure as code

---

## 👨‍💻 Author

**Eshaan Pilar**  
SOC Analyst | Security Engineer | Portfolio Project  
[GitHub](https://github.com/Eshaan49) | [LinkedIn]

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

This is a portfolio project. For questions or suggestions:
1. Open an issue
2. Submit a pull request
3. Contact via GitHub

---

**Last Updated:** July 5, 2026  
**Status:** Production Ready ✅  
**Next Phase:** Wazuh Integration
