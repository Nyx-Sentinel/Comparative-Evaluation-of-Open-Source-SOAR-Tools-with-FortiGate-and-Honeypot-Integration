# Comparative Evaluation of Open-Source SOAR Tools
## with FortiGate Integration Using Real-World Honeypot Attack Data

Master's Thesis in Cybersecurity (EXD630, 15 HE credits) Högskolan Väst Trollhätan
Students: Filmon Mehari Gebrezghi & Alphonse Joseph  
Supervisor: Robert Andersson  
Start year: 2025

---

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
193.10.203.150   Public IP
   │              │
   │  Logs        │ Syslog
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
port 3001      port 443
```

### Hardware

| Component | Role | IP |
|---|---|---|
| Machine 1 (Ubuntu 22.04) | T-Pot 24.04 honeypot | 193.10.203.150 |
| Machine 2 (Ubuntu 22.04) | Shuffle + Wazuh + Cortex + TheHive | 193.10.203.151 |
| FortiGate 50G | NGFW, data source, response target | 193.10.203.x |
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
│       └── thehive-connector.py    # Wazuh → TheHive case creation script
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

| Service | Port | Machine |
|---|---|---|
| Shuffle frontend | 3001 | 193.10.203.151 |
| Shuffle backend | 5001 | 193.10.203.151 |
| Shuffle OpenSearch | 9200 | 193.10.203.151 |
| Wazuh indexer | 9201 | 193.10.203.151 |
| Wazuh dashboard | 443 | 193.10.203.151 |
| Wazuh manager | 1514 | 193.10.203.151 |
| Logstash beats input | 5044 | 193.10.203.151 |
| Logstash syslog input | 514/udp | 193.10.203.151 |
| T-Pot SSH | 64295 | 193.10.203.150 |
| T-Pot dashboard | 64297 | 193.10.203.150 |

---

## T-Pot Sensors Active

| Sensor | Protocol | Attack Category |
|---|---|---|
| Cowrie | SSH/Telnet (22–23) | Brute-force, shell interaction |
| Dionaea | SMB, FTP, HTTP | Malware delivery |
| Honeytrap | All ports | Network reconnaissance |
| Suricata | All traffic (IDS) | Signature-based detection |
| ConPot | SNMP, IEC 104 | ICS/SCADA emulation |
| Tanner | HTTP (80) | Web application attacks |
| H0neytr4p | HTTPS (443) | Encrypted traffic |

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

## Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/FilmonMeharii/Comparative-Evaluation-of-Open-Source-SOAR-Tools-with-FortiGate-and-Honeypot-Integration.git
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

## Current Status (March 2026)

- [x] T-Pot deployed, 128,000+ real attack events collected
- [x] Shuffle installed and receiving live T-Pot data
- [x] Wazuh indexer, manager, dashboard running
- [x] Logstash dual-output pipeline active
- [ ] Playbook configuration in progress
- [ ] 14-day measurement window
- [ ] Results analysis

---

## License

MIT License — see [LICENSE](LICENSE)

## Contact

- Filmon Mehari Gebrezghi — filmon-mehari.gebrezghi@student.hv.se
- Alphonse Joseph — alphonse.joseph@student.hv.se
