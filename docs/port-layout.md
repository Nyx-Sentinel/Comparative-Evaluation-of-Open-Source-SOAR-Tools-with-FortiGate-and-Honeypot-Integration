# Port Layout Reference
## SOAR Machine — 193.10.203.151

This document lists all services and their ports on the SOAR machine.
The key design constraint: Shuffle OpenSearch (9200) and Wazuh Indexer (9201)
must not conflict — this is why Wazuh is configured on a non-standard port.

| Service | Port | Protocol | Notes |
|---|---|---|---|
| Shuffle Frontend | 3001 | TCP | Web UI — access via browser |
| Shuffle Backend | 5001 | TCP | API |
| Shuffle OpenSearch | 9200 | TCP | Internal only |
| Wazuh Dashboard | 443 | TCP/HTTPS | Web UI — use https:// |
| Wazuh Indexer | 9201 | TCP | **Non-standard** — moved from 9200 to avoid conflict with Shuffle |
| Wazuh Manager | 1514 | TCP/UDP | Agent communication |
| Wazuh Agent Enrollment | 1515 | TCP | New agent registration |
| Wazuh Cluster | 1516 | TCP | Internal cluster |
| Wazuh API | 55000 | TCP | REST API |
| Logstash Beats | 5044 | TCP | Receives Filebeat from T-Pot |
| Logstash Syslog | 514 | UDP | Receives FortiGate syslog |

## T-Pot Machine — 193.10.203.150

| Service | Port | Protocol | Notes |
|---|---|---|---|
| T-Pot SSH (admin) | 64295 | TCP | Management — not exposed to internet |
| T-Pot Dashboard (Kibana) | 64297 | TCP/HTTPS | Internal access only |
| Cowrie SSH Honeypot | 22, 23 | TCP | Exposed to internet |
| Dionaea SMB Honeypot | 445, 135 | TCP | Exposed to internet |
| Dionaea HTTP | 80 | TCP | Exposed to internet |
| Tanner HTTP | 8080 | TCP | Exposed to internet |
| H0neytr4p HTTPS | 443 | TCP | Exposed to internet |
| ConPot SNMP | 161 | UDP | Exposed to internet |
| Suricata IDS | All ports | Passive | Monitors all traffic |
| Honeytrap | All ports | TCP | Catches uncovered ports |

## FortiGate 50G

| Service | Port | Protocol | Direction |
|---|---|---|---|
| Management HTTPS | 443 | TCP | Admin access |
| REST API | 443 | TCP | SOAR → FortiGate |
| Syslog Export | 514 | UDP | FortiGate → SOAR (193.10.203.151) |

## UFW Rules on SOAR Machine

```bash
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 443/tcp     # Wazuh dashboard
sudo ufw allow 3001/tcp    # Shuffle frontend
sudo ufw allow 5001/tcp    # Shuffle backend
sudo ufw allow 5044/tcp    # Logstash beats
sudo ufw allow 514/udp     # Logstash syslog (FortiGate)
sudo ufw allow 1514/tcp    # Wazuh manager
sudo ufw allow 1515/tcp    # Wazuh enrollment
sudo ufw allow 55000/tcp   # Wazuh API
sudo ufw allow 9200/tcp    # Shuffle OpenSearch
sudo ufw allow 9201/tcp    # Wazuh Indexer
sudo ufw allow 9300/tcp    # Wazuh transport
```
