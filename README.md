# Comparative Evaluation of Open-Source SOAR Tools with FortiGate and Honeypot Integration

Master's Thesis in Cybersecurity (EXD630, 60 HE credits) — Högskolan Väst, Trollhättan, Sweden  
**Authors:** Filmon Mehari Gebrezghi & Alphonse Joseph  
**Supervisor:** Robert Andersson  
**Examiner:** Vira Shendryk  
**Year:** 2026

---

## Overview

This repository contains all configuration files, playbooks, pipeline definitions, and scripts used in the empirical comparison of two open-source SOAR platforms using **real-world attack data** collected over 33 days from a T-Pot 24.04 honeypot and a FortiGate 50G next-generation firewall.

| Platform | Role |
|---|---|
| **Shuffle** | Dedicated visual SOAR orchestrator |
| **Wazuh + Cortex + TheHive** | Integrated detection, enrichment, and case management stack |

Both platforms receive **identical log streams** split from a single Logstash pipeline, ensuring a fair head-to-head comparison across six operational metrics.

---

## Key Results

| Metric | Shuffle | Wazuh+Cortex+TheHive |
|---|---|---|
| Avg response latency | 2.5 s | 0.387 s |
| FortiGate block latency | 4.0 s | 0.288 s |
| Playbook success rate | 100% (50/50) | 100% (verified) |
| False positive rate | N/A (webhook-triggered) | 60% (broad monitoring scope) |
| Integration effort | 14.5 h / 141 config lines | 13.5 h / 195 config lines |
| Baseline RAM | 74% (11 GB / 15 GB) | 74% (11 GB / 15 GB) |
| Baseline CPU | 2.6% | 2.6% |
| Cohen's Kappa (labelling) | — | 0.87 (almost perfect) |

**Key finding:** Wazuh is 6.3× faster on average due to direct OS process execution vs Shuffle's Docker container spawning per execution.

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
   │  Beats TCP   │ Syslog UDP 514
   └──────┬───────┘
          ▼
   [SOAR Machine — 193.10.203.151]
   ┌──────────────┐
   │   Logstash   │ ← single pipeline, dual output
   └──────┬───────┘
          │
    ┌─────┴──────────┐
    ▼                ▼
[Shuffle]     [Wazuh+Cortex+TheHive]
port 3001      port 443 / 9000 / 9001
    │                │
    └────────┬────────┘
             ▼
    [SOAR Proxy — Flask :9090]
    /block · /check · /notify · /case
             │
    ┌────────┼────────┐
    ▼        ▼        ▼
[FortiGate] [TheHive] [AbuseIPDB]
 REST API   port 9000  External API
```

---

## Hardware Configuration

| Component | Role | IP | Spec |
|---|---|---|---|
| Machine 1 (Ubuntu 24.04) | T-Pot 24.04 honeypot | 193.10.203.150 | Physical desktop |
| Machine 2 (Ubuntu 22.04) | Shuffle + Wazuh + Cortex + TheHive | 193.10.203.151 | Physical desktop, 15GB RAM |
| FortiGate 50G (FortiOS 7.6.6) | NGFW, data source, response target | 193.10.203.159 (WAN) | Physical firewall |
| Kali Linux laptop | Controlled attack generation | LAN-connected | Kali Linux 2025.4 |

---

## Repository Structure

```
├── README.md
├── SETUP.md                          # Full deployment guide
├── thesis/
│   └── Final_Report_Master_Thesis.pdf
├── scripts/
│   ├── soar_proxy/
│   │   └── abuseipdb_proxy.py        # Custom Flask proxy (port 9090)
│   ├── wazuh/
│   │   ├── fortigate-block.sh        # WZ-PB1 active response script
│   │   └── custom-thehive            # WZ-PB2/3/4 TheHive integration
│   ├── monitoring/
│   │   └── resource_monitor.sh       # CPU/RAM logging every 60s
│   └── sampling/
│       └── sampling.py               # Random alert sampling (100 per platform)
├── configs/
│   ├── logstash/
│   │   └── logstash.conf             # T-Pot Logstash pipeline with HTTP output
│   ├── wazuh/
│   │   └── ossec.conf                # Wazuh active response + integration config
│   └── netplan/
│       └── 00-installer-config.yaml  # Static IP configuration
├── playbooks/
│   ├── shuffle/
│   │   ├── PB1_IP_Block.json         # FortiGate IP blocking via proxy
│   │   ├── PB2_AbuseIPDB.json        # AbuseIPDB enrichment via proxy
│   │   ├── PB3_TheHive_Notify.json   # TheHive alert creation via proxy
│   │   └── PB4_TheHive_Case.json     # TheHive case creation via proxy
│   └── wazuh/
│       ├── fortigate-block.sh        # Active response IP blocking
│       └── custom-thehive            # TheHive alert + case integration
├── diagrams/
│   └── architecture.png              # Full testbed architecture diagram
└── data/
    └── sample_alerts/
        └── wazuh_sample_100.json     # 100 sampled alerts used for labelling
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
| Wazuh manager | 1516 | 193.10.203.151 | |
| Logstash beats input | 5044 | 193.10.203.151 | Receives T-Pot logs |
| Logstash syslog input | 514/udp | 193.10.203.151 | Receives FortiGate syslog |
| SOAR Proxy | 9090 | 193.10.203.151 | Custom Flask gateway |
| Cortex | 9001 | 193.10.203.151 | |
| Cortex Elasticsearch | 9202 | 193.10.203.151 | |
| TheHive | 9000 | 193.10.203.151 | |
| T-Pot SSH | 64295 | 193.10.203.150 | Management access |
| T-Pot dashboard | 64297 | 193.10.203.150 | Kibana |

---

## T-Pot Sensors and Data Collected

| Sensor | Protocol | Attack Category | Events (33 days) |
|---|---|---|---|
| Cowrie | SSH/Telnet (22, 23) | Credential brute-force | 516 sessions |
| Dionaea | SMB, FTP, HTTP | Malware delivery | Archived |
| Suricata | All traffic (IDS) | Signature-based detection | 166,743 alerts |
| Honeytrap | All ports | Network reconnaissance | 304,077 connections |
| Tanner | HTTP (80) | Web application attacks | Archived |
| H0neytr4p | HTTPS (443) | Encrypted traffic | Archived |
| ConPot | SNMP, IEC 104 | ICS/SCADA emulation | Archived |
| **Total** | | | **471,099+** |

### Notable Finding

During the collection period, the SOAR infrastructure itself received unsolicited connection attempts from external internet sources:

| Port | Service | Attempts |
|---|---|---|
| 3001 | Shuffle Frontend | 173,122 |
| 1516 | Wazuh Manager | 891 |
| 1515 | Wazuh Agent | 231 |
| 9000 | TheHive | 23 |

This confirms that SOAR management interfaces must not be exposed to untrusted networks without IP whitelisting, VPN, or additional authentication.

---

## Eight Playbooks

### Shuffle (PB1–PB4) — via SOAR Proxy at 172.19.0.1:9090

| ID | Name | Trigger | Action | Avg Latency |
|---|---|---|---|---|
| PB1 | IP Blocking | Webhook from T-Pot | POST /block → FortiGate REST API | 4.0 s |
| PB2 | AbuseIPDB Enrichment | Webhook from T-Pot | GET /check → AbuseIPDB | 3.0 s |
| PB3 | TheHive Notification | Webhook from T-Pot | POST /notify → TheHive alert | 2.0 s |
| PB4 | TheHive Case Creation | Webhook from T-Pot | POST /case → TheHive case | 1.0 s |

### Wazuh (WZ-PB1–WZ-PB4) — via Active Response and Integration Scripts

| ID | Name | Trigger | Action | Avg Latency |
|---|---|---|---|---|
| WZ-PB1 | IP Blocking | Wazuh rule level 6+ | fortigate-block.sh → FortiGate REST API | 0.288 s |
| WZ-PB2 | AbuseIPDB Enrichment | Any alert with src_ip | custom-thehive → /check proxy | 0.418 s |
| WZ-PB3 | TheHive Alert | Wazuh integratord | custom-thehive → TheHive /api/v1/alert | ~0.4 s |
| WZ-PB4 | TheHive Case | Wazuh integratord | custom-thehive → TheHive /api/v1/case | ~0.4 s |

---

## SOAR Proxy

A custom Flask application running as a systemd service on port 9090 was developed to circumvent university firewall restrictions that blocked Docker container outbound traffic.

```
Shuffle worker containers → 172.19.0.1:9090 → External APIs
```

| Route | Method | Target |
|---|---|---|
| /block | POST | FortiGate REST API (IP blocking) |
| /check | GET | AbuseIPDB (IP reputation lookup) |
| /notify | POST | TheHive (alert creation) |
| /case | POST | TheHive (case creation) |

---

## Evaluation Metrics

| Metric | Definition | Measurement Method |
|---|---|---|
| Playbook success rate | Successful executions / total triggers × 100% | Shuffle execution logs, Wazuh active response logs |
| Response latency | Seconds from alert ingestion to final action | Shuffle execution timestamps, Linux `time` command |
| False positive rate | FP alerts / total sampled alerts × 100% | Manual labelling of 100 random alerts, Cohen's Kappa |
| Integration effort | Person-hours + config lines per platform | Time-logged activity records |
| CPU utilization | Mean % over monitoring period | `top` command, 60s intervals |
| RAM consumption | Mean GB over monitoring period | `free` command, 60s intervals |

---

## Controlled Attack Scenarios

| Day | Tool | Target | Purpose |
|---|---|---|---|
| Day 2 | Nmap (-sV -A) | FortiGate | Port scan, IPS trigger |
| Day 4 | Hydra (SSH) | SOAR machine | SSH brute-force, Wazuh detection |
| Day 6 | Metasploit (SMB) | T-Pot Dionaea | SMB exploitation |
| Day 8 | SQLmap + Nikto | T-Pot Tanner | Web attack |
| Day 10 | curl (manual) | FortiGate IPS | IPS rule trigger |

---

## Technical Challenges and Solutions

| Challenge | Solution |
|---|---|
| Docker containers blocked by university firewall | Custom Flask proxy on host at port 9090 |
| DHCP caused IP address swaps between machines | Static IPs via Netplan on both machines |
| Shuffle spawned unlimited worker containers under load | CLEANUP=true in Orborus + container monitor script |
| Port 1514 conflict between Tenzir and Wazuh | Removed Tenzir, Wazuh moved to port 1516 |
| FortiGate API authentication failed on IP change | Trusted host set to subnet 193.10.203.128/25 |
| Logstash syntax error (HTTP block outside output section) | Extracted config, corrected and reloaded |

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

### 3. Start SOAR proxy
```bash
pip3 install flask requests
cp scripts/soar_proxy/abuseipdb_proxy.py /opt/scripts/
sudo systemctl enable soar-proxy
sudo systemctl start soar-proxy
```

### 4. Configure T-Pot log forwarding
Copy `configs/logstash/logstash.conf` into the T-Pot Logstash container and restart.

### 5. Import Shuffle playbooks
In Shuffle UI → Workflows → Import → select JSON files from `playbooks/shuffle/`

### 6. Configure Wazuh active response
Copy `configs/wazuh/ossec.conf` content into `/var/ossec/etc/ossec.conf` and restart Wazuh manager.

---

## Project Status

- [x] T-Pot deployed — 471,099+ real attack events collected over 33 days
- [x] Shuffle installed and receiving live T-Pot data via webhook
- [x] Wazuh indexer, manager, dashboard running
- [x] Logstash dual-output pipeline active
- [x] FortiGate syslog → Logstash confirmed
- [x] FortiGate REST API integrated for automated IP blocking
- [x] Cortex installed and running (port 9001)
- [x] TheHive installed and running (port 9000)
- [x] TheHive ↔ Cortex connected
- [x] Wazuh → TheHive live alert integration confirmed
- [x] SOAR proxy deployed as systemd service
- [x] All 8 playbooks implemented and tested
- [x] Response latency measured (Shuffle 2.5 s avg, Wazuh 0.387 s avg)
- [x] 100 alerts sampled and labelled (Cohen's Kappa 0.87)
- [x] Resource monitoring completed
- [x] Thesis submitted May 2026

---

## Citation

If you use this work, please cite:

> Joseph, A. & Gebrezghi, F.M. (2026). *Comparative Evaluation of Open-Source SOAR Tools with FortiGate Integration Using Real-World Honeypot Attack Data.* Master Thesis, University West, Sweden.

---

## License

MIT License — see [LICENSE](LICENSE)

---

## Contact

- Filmon Mehari Gebrezghi — filmon-mehari.gebrezghi@student.hv.se
- Alphonse Joseph — alphonse.joseph@student.hv.se
