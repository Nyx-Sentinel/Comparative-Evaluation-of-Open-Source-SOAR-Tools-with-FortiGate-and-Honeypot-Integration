# SETUP.md — Full Deployment Guide

Complete setup instructions for reproducing the SOAR testbed used in:

> *Comparative Evaluation of Open-Source SOAR Tools with FortiGate Integration Using Real-World Honeypot Attack Data*  
> Alphonse Joseph & Filmon Mehari Gebrezghi, University West, 2026

---

## Prerequisites

- Two physical machines running Ubuntu 22.04 or 24.04
- FortiGate 50G firewall (or any FortiGate with REST API)
- Public IP addresses for both machines and FortiGate WAN
- Minimum 15GB RAM on SOAR machine
- Internet access from SOAR machine host (not required from Docker containers)

---

## Network Layout

```
Internet
    │
    ▼
[Unfiltered Switch]
    │
┌───┴───┐
▼       ▼
[T-Pot] [FortiGate WAN]
Machine 1   Machine 2 (behind FortiGate LAN)
```

---

## Machine 1 — T-Pot Honeypot

### Install T-Pot

```bash
git clone https://github.com/telekom-security/tpotce
cd tpotce
sudo ./install.sh --type=user
sudo reboot
```

### Configure static IP

```bash
sudo nano /etc/netplan/00-installer-config.yaml
```

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 193.10.203.150/25
      gateway4: 193.10.203.129
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
```

```bash
sudo netplan apply
```

### Configure Logstash to forward to SOAR machine

Edit T-Pot Logstash config inside the container:

```bash
docker exec -it tpot_logstash_1 bash
# Add HTTP output block pointing to SOAR machine Shuffle webhook
```

Or copy `configs/logstash/logstash.conf` and mount it.

---

## Machine 2 — SOAR Server

### Set static IP

```bash
sudo nano /etc/netplan/00-installer-config.yaml
```

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 193.10.203.151/25
      gateway4: 193.10.203.129
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
```

```bash
sudo netplan apply
```

### Install Docker

```bash
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

### Install Shuffle

```bash
git clone https://github.com/Shuffle/Shuffle
cd Shuffle
docker-compose up -d
```

Access at: `http://193.10.203.151:3001`

### Install Wazuh

```bash
curl -sO https://packages.wazuh.com/4.7/wazuh-install.sh
sudo bash wazuh-install.sh -a
```

The Wazuh indexer defaults to port 9200. Move it to 9201 to avoid conflict with Shuffle OpenSearch:

```bash
sudo nano /etc/wazuh-indexer/opensearch.yml
# Change: http.port: 9201
sudo systemctl restart wazuh-indexer
```

Access Wazuh dashboard at: `https://193.10.203.151`

### Install TheHive

```bash
mkdir -p /opt/thehive
cd /opt/thehive
# Copy docker-compose.yml for TheHive + Cassandra
docker-compose up -d
```

Access at: `http://193.10.203.151:9000`

Default login: `admin@thehive.local` / `secret`

### Install Cortex

```bash
mkdir -p /opt/cortex
cd /opt/cortex
# Copy docker-compose.yml for Cortex + Elasticsearch
docker-compose up -d
```

Access at: `http://193.10.203.151:9001`

Connect TheHive to Cortex network:

```bash
docker network connect cortex_default thehive_thehive_1
```

### Deploy SOAR Proxy

```bash
sudo pip3 install flask requests
sudo mkdir -p /opt/scripts
sudo cp scripts/soar_proxy/abuseipdb_proxy.py /opt/scripts/

# Edit API keys in the script
sudo nano /opt/scripts/abuseipdb_proxy.py

# Install as systemd service
sudo cp soar-proxy.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable soar-proxy
sudo systemctl start soar-proxy

# Verify
sudo systemctl status soar-proxy
curl http://localhost:9090/health
```

### Deploy Wazuh Active Response Script

```bash
sudo cp scripts/wazuh/fortigate-block.sh /var/ossec/active-response/bin/
sudo chmod 750 /var/ossec/active-response/bin/fortigate-block.sh
sudo chown root:wazuh /var/ossec/active-response/bin/fortigate-block.sh
```

### Deploy Wazuh TheHive Integration

```bash
sudo cp scripts/wazuh/custom-thehive /var/ossec/integrations/
sudo chmod 750 /var/ossec/integrations/custom-thehive
sudo chown root:wazuh /var/ossec/integrations/custom-thehive

# Edit TheHive API key inside script
sudo nano /var/ossec/integrations/custom-thehive
```

### Configure Wazuh (ossec.conf)

Add the active response and integration blocks from `configs/wazuh/ossec.conf` to your existing `/var/ossec/etc/ossec.conf`:

```bash
sudo nano /var/ossec/etc/ossec.conf
# Add <command>, <active-response>, and <integration> blocks

sudo systemctl restart wazuh-manager
```

### Deploy Resource Monitor

```bash
sudo cp scripts/monitoring/resource_monitor.sh /opt/scripts/
sudo chmod +x /opt/scripts/resource_monitor.sh

# Create systemd service
sudo tee /etc/systemd/system/resource-monitor.service << EOF
[Unit]
Description=Resource Monitor
After=network.target

[Service]
Type=simple
ExecStart=/bin/bash /opt/scripts/resource_monitor.sh
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable resource-monitor
sudo systemctl start resource-monitor
```

---

## FortiGate 50G Configuration

### Enable syslog

1. Go to **Log & Report → Log Settings**
2. Add syslog server: `193.10.203.151`, port `514`, UDP
3. Set log level to **Information** or above

### Create REST API admin

1. Go to **System → Administrators**
2. Create new administrator: `soar-api`
3. Profile: `Super Admin` (or custom with address management)
4. Trusted Host: `193.10.203.128/255.255.255.128` (subnet)
5. Enable REST API access

### Test API

```bash
curl -k -s \
  -H "Authorization: Bearer YOUR_API_KEY" \
  https://193.10.203.159/api/v2/monitor/system/status \
  | python3 -m json.tool | head -5
```

---

## Shuffle Playbook Import

1. Open Shuffle at `http://193.10.203.151:3001`
2. Go to **Workflows**
3. Click **Import**
4. Import each JSON file from `playbooks/shuffle/`
5. Update webhook URLs and API keys inside each workflow
6. Activate workflows **only during controlled testing** to prevent container spawning

### Important — Container Spawning Prevention

Set in Orborus environment:

```yaml
# In Shuffle docker-compose.yml
orborus:
  environment:
    - CLEANUP=true
    - MAX_WORKER_COUNT=10
```

---

## Verification Checklist

```bash
# Check all services running
docker ps | grep shuffle
sudo systemctl status wazuh-manager
sudo systemctl status wazuh-indexer
sudo systemctl status soar-proxy
docker ps | grep thehive
docker ps | grep cortex

# Test SOAR proxy routes
curl http://localhost:9090/health
curl "http://localhost:9090/check?ip=8.8.8.8"

# Test FortiGate API
curl -k -H "Authorization: Bearer YOUR_KEY" \
  https://193.10.203.159/api/v2/monitor/system/status

# Check Wazuh active response log
tail -f /var/ossec/logs/active-responses.log

# Check TheHive integration log
tail -f /var/ossec/logs/custom-thehive.log

# Check resource monitor
tail -f /opt/scripts/resource_log.csv
```

---

## Port Reference

| Service | Port | Protocol |
|---------|------|----------|
| Shuffle Frontend | 3001 | HTTP |
| Shuffle OpenSearch | 9200 | HTTP |
| Wazuh Dashboard | 443 | HTTPS |
| Wazuh Indexer | 9201 | HTTP |
| Wazuh Manager | 1516 | TCP |
| Logstash Beats | 5044 | TCP |
| Logstash Syslog | 514 | UDP |
| SOAR Proxy | 9090 | HTTP |
| TheHive | 9000 | HTTP |
| Cortex | 9001 | HTTP |
| T-Pot SSH | 64295 | TCP |
| T-Pot Dashboard | 64297 | HTTPS |

---

## Common Issues

| Problem | Solution |
|---------|----------|
| Shuffle containers can't reach internet | Use SOAR proxy at 172.19.0.1:9090 |
| Machines swap IPs after reboot | Configure static IPs via Netplan |
| Wazuh manager fails to start | Check port 1516 is free: `sudo lsof -i:1516` |
| TheHive/Cortex not connected | Run: `docker network connect cortex_default thehive_thehive_1` |
| FortiGate API returns 401 | Check trusted host subnet in FortiGate admin settings |
| Shuffle load average spikes | Set CLEANUP=true in Orborus, keep workflows inactive |
