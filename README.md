# Comparative Evaluation of Open-Source SOAR Tools with FortiGate and Honeypot Integration

Master's Thesis in Cybersecurity (EXD630, 15 HE credits) Högskolan Väst Trollhätan
Students: Filmon Mehari Gebrezghi & Alphonse Joseph  
Supervisor: Robert Andersson  
Start year: 2025

## Overview
 
This repository contains all configuration files, playbooks, pipeline definitions, and scripts used in the empirical comparison of two open-source SOAR platforms:
 
| Platform | Role |
|---|---|
| **Shuffle** | Dedicated visual SOAR orchestrator |
| **Wazuh + Cortex + TheHive** | Integrated detection, enrichment, and case management stack |
 
Both platforms receive **identical log streams** split from a single Logstash pipeline, ensuring a fair head-to-head comparison across six operational metrics.
 
---
 
## Testbed Architecture
 
```
Internet (Attackers)
        │
        ▼
  [Unfiltered Switch]
        │
   ┌────┴────┐
   ▼         ▼
[T-Pot]   [FortiGate 50G]
193.10.203.150   193.10.203.159 (WAN)
   │              │
   │  Logs        │ Syslog UDP 514
   └──────┬───────┘
          ▼
   [SOAR Machine]
   193.10.203.151
   ┌──────────────┐
   │   Logstash   │ ← single pipeline, dual output
   └──────┬───────┘
          │
    ┌─────┴─────┐
    ▼           ▼
[Shuffle]  [Wazuh+Cortex+TheHive]
port 3001      port 443 / 9000 / 9001
```
 
### Hardware
 
| Component | Role | IP |
|---|---|---|
| Machine 1 (Ubuntu 22.04) | T-Pot 24.04 honeypot | 193.10.203.150 |
| Machine 2 (Ubuntu 22.04) | Shuffle + Wazuh + Cortex + TheHive | 193.10.203.151 |
| FortiGate 50G (FortiOS 7.6.6) | NGFW, data source, response target | 193.10.203.159 (WAN) / 192.168.1.99 (LAN) |
| Kali Linux laptop | Controlled attack generation | LAN |
 
---
 
## Repository Structure
 
```
├── config/
│   ├── logstash-tpot.conf          # T-Pot Logstash output config (adds HTTP to Shuffle)
│   ├── logstash-soar.conf          # SOAR machine Logstash pipeline (beats + syslog input)
│   └── wazuh-opensearch.yml        # Wazuh indexer config (port 9201, avoids Shuffle conflict)
│
├── playbooks/
│   ├── shuffle/
│   │   ├── PB1_ip_block.json       # IP blocking via FortiGate REST API
│   │   ├── PB2_enrichment.json     # Alert enrichment via AbuseIPDB
│   │   ├── PB3_notification.json   # Slack notification
│   │   └── PB4_ticket.json         # Case creation in TheHive
│   └── wazuh/
│       ├── active-response.xml     # Wazuh active response config (IP block)
│       ├── ossec-rules.xml         # Custom detection rules
│       └── custom-thehive.py       # Wazuh → TheHive alert forwarding integration script
│
├── scripts/
│   ├── setup_soar_machine.sh       # Full SOAR machine setup script
│   ├── install_wazuh.sh            # Wazuh installation helper
│   ├── sampling.py                 # Random alert sampling (100 per platform)
│   └── resource_monitor.sh        # CPU/RAM monitoring over 24h
│
├── docs/
│   └── port-layout.md              # All services and ports reference
│
└── README.md
```
 
---
 
## Port Layout
 
| Service | Port | Machine | Notes |
|---|---|---|---|
| Shuffle frontend | 3001 | 193.10.203.151 | |
| Shuffle backend | 5001 | 193.10.203.151 | |
| Shuffle OpenSearch | 9200 | 193.10.203.151 | |
| Wazuh indexer | 9201 | 193.10.203.151 | Moved from 9200 to avoid Shuffle conflict |
| Wazuh dashboard | 443 | 193.10.203.151 | |
| Wazuh manager | 1516 | 193.10.203.151 | Moved from 1514 (Tenzir container conflict) |
| Logstash beats input | 5044 | 193.10.203.151 | |
| Logstash syslog input | 514/udp | 193.10.203.151 | FortiGate syslog target |
| Cortex | 9001 | 193.10.203.151 | |
| Cortex Elasticsearch | 9202 | 193.10.203.151 | Moved from 9200/9201 to avoid conflicts |
| TheHive | 9000 | 193.10.203.151 | |
| T-Pot SSH | 64295 | 193.10.203.150 | |
| T-Pot dashboard | 64297 | 193.10.203.150 | |
 
---
 
## T-Pot Sensors Active
 
| Sensor | Protocol | Attack Category | Events Collected |
|---|---|---|---|
| Cowrie | SSH/Telnet (22–23) | Brute-force, shell interaction | 103 sessions |
| Dionaea | SMB, FTP, HTTP | Malware delivery | 18,000+ |
| Honeytrap | All ports | Network reconnaissance | 3+ |
| Suricata | All traffic (IDS) | Signature-based detection | Live stream |
| ConPot | SNMP, IEC 104 | ICS/SCADA emulation | 96,000+ |
| Tanner | HTTP (80) | Web application attacks | 8,000+ |
| H0neytr4p | HTTPS (443) | Encrypted traffic | 6,000+ |
| **Total** | | | **128,000+** |
 
---
 
## Four Playbooks (Identical on Both Platforms)
 
| # | Playbook | Trigger | Action |
|---|---|---|---|
| PB1 | IP Blocking | Any alert with src_ip | FortiGate REST API → create address object → add to deny policy |
| PB2 | Enrichment | Any alert with src_ip | AbuseIPDB API → confidence score attached to alert |
| PB3 | Notification | Alert confidence > 50 | Slack webhook → formatted alert summary |
| PB4 | Case Creation | TP alert confirmed | TheHive case creation with observables |
 
---
 
## Evaluation Metrics
 
| Metric | Definition |
|---|---|
| Playbook success rate | successful executions / total triggers × 100% |
| Response latency | seconds from alert ingestion to final playbook action |
| False positive rate | FP triggers / total triggers × 100% |
| Integration effort | person-hours to configure connectors and build playbooks |
| Average CPU usage | mean % over 24h monitoring window |
| Average RAM usage | mean GB over 24h monitoring window |
 
---
 
## Controlled Attack Schedule
 
| Day | Tool | Target Sensor |
|---|---|---|
| Day 2 | Nmap (-sV -A) | Honeytrap, Suricata |
| Day 4 | Hydra (SSH) | Cowrie |
| Day 6 | Metasploit (SMB) | Dionaea |
| Day 8 | SQLmap + Nikto | Tanner |
| Day 10 | curl (manual) | FortiGate IPS |
 
---
 
## FortiGate REST API
 
The FortiGate 50G REST API is used by both platforms for automated IP blocking (PB1).
 
- **Base URL:** `https://193.10.203.159/api/v2/`
- **Auth:** Bearer token (stored in playbook secrets)
- **API admin user:** `soar-api` (trusted host: 193.10.203.151/32 only)
- **Tested endpoint:** `/api/v2/monitor/system/status` → HTTP 200 ✅
 
### Firewall Policy Rules (in order)
 
| Rule | Source | Destination | Service | Action |
|---|---|---|---|---|
| allow-soar-api | soar (193.10.203.151) | FortiGate | HTTPS | ACCEPT |
| allow-ssh | all | all | SSH | ACCEPT |
| allow-honeypot | honeypot (193.10.203.150) | all | ALL | ACCEPT |
| Deny all | all | all | ALL | DENY |
 
---
 
## Wazuh → TheHive Integration
 
Wazuh forwards alerts to TheHive via a custom Python integration script at `/var/ossec/integrations/custom-thehive`.
 
- Triggers on alerts at **level 3 and above**
- Creates TheHive alerts via REST API (`/api/v1/alert`)
- TheHive org: `thesis` | User: `analyst@thesis.local`
- Status: **Live and confirmed working** ✅
 
---
 
## Quick Start
 
### 1. Clone the repo
```bash
git clone https://github.com/Nyx-Sentinel/Comparative-Evaluation-of-Open-Source-SOAR-Tools-with-FortiGate-and-Honeypot-Integration.git
cd Comparative-Evaluation-of-Open-Source-SOAR-Tools-with-FortiGate-and-Honeypot-Integration
```
 
### 2. Deploy SOAR machine
```bash
chmod +x scripts/setup_soar_machine.sh
./scripts/setup_soar_machine.sh
```
 
### 3. Configure T-Pot log forwarding
Copy `config/logstash-tpot.conf` content into `/etc/logstash/logstash.conf` inside the T-Pot logstash container. See `config/` folder for details.
 
### 4. Import Shuffle playbooks
In Shuffle UI → Workflows → Import → select JSON files from `playbooks/shuffle/`
 
### 5. Configure Wazuh active response
Copy contents of `playbooks/wazuh/active-response.xml` into `/var/ossec/etc/ossec.conf`
 
---
 
## Current Status (April 2026)
 
- [x] T-Pot deployed, 128,000+ real attack events collected
- [x] Shuffle installed and receiving live T-Pot data via webhook
- [x] Wazuh indexer, manager, dashboard running
- [x] Logstash dual-output pipeline active
- [x] FortiGate syslog → Logstash (UDP 514) confirmed
- [x] FortiGate REST API token created and tested
- [x] FortiGate firewall policy rules configured
- [x] Cortex installed and running (port 9001)
- [x] TheHive installed and running (port 9000)
- [x] TheHive ↔ Cortex connected
- [x] Wazuh → TheHive live alert integration confirmed working
- [ ] Cortex analyzers (AbuseIPDB) — in progress
- [ ] Shuffle playbooks (4) — in progress
- [ ] Wazuh/TheHive playbooks (4) — in progress
- [ ] 14-day measurement window
- [ ] Results analysis and thesis write-up
 
---
 
## License
 
MIT License — see [LICENSE](LICENSE)
 
## Contact
 
- Filmon Mehari Gebrezghi — filmon-mehari.gebrezghi@student.hv.se
- Alphonse Joseph — alphonse.joseph@student.hv.se
 
