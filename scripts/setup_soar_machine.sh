#!/bin/bash
# =============================================================
# SOAR Machine Full Setup Script
# Tested on: Ubuntu Server 22.04 LTS
# Machine IP: 193.10.203.151
#
# This script installs and configures:
#   1. Docker + Docker Compose
#   2. Shuffle SOAR
#   3. Wazuh (indexer on port 9201, manager, dashboard)
#   4. Logstash pipeline
#   5. UFW firewall rules
#
# Run as: bash setup_soar_machine.sh
# =============================================================

set -e

echo "========================================================"
echo " SOAR Machine Setup — Thesis Testbed"
echo " University West Cybersecurity Thesis 2026"
echo "========================================================"

# ---- 1. SYSTEM PREP ----
echo "[1/6] System update..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git nano ufw openjdk-17-jre-headless

# ---- 2. DOCKER ----
echo "[2/6] Installing Docker..."
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
sudo systemctl enable docker

# Install Docker Compose plugin
sudo apt install -y docker-compose-plugin

echo "[2/6] Docker installed: $(docker --version)"

# ---- 3. SHUFFLE ----
echo "[3/6] Installing Shuffle SOAR..."
sudo mkdir -p /opt/Shuffle
cd /opt/Shuffle

# Download Shuffle docker-compose
curl -L https://raw.githubusercontent.com/Shuffle/Shuffle/main/docker-compose.yml -o docker-compose.yml

# Required for Shuffle OpenSearch
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf

# Start Shuffle
sudo docker compose up -d

echo "[3/6] Shuffle started — dashboard at http://$(hostname -I | awk '{print $1}'):3001"
echo "      Wait 2 minutes for Shuffle to initialize, then create admin account"

# ---- 4. WAZUH ----
echo "[4/6] Installing Wazuh 4.14.4..."

cd /home/$USER

# Download installer
curl -sO https://packages.wazuh.com/4.9/wazuh-install.sh
curl -sO https://packages.wazuh.com/4.9/config.yml

# Configure with localhost (avoid public IP rejection)
cat > config.yml << 'EOF'
nodes:
  indexer:
    - name: node-1
      ip: "127.0.0.1"
      port: 9201
  server:
    - name: wazuh-1
      ip: "127.0.0.1"
  dashboard:
    - name: dashboard
      ip: "127.0.0.1"
EOF

# Generate certificates
sudo bash wazuh-install.sh --generate-config-files

# Create required log directory (fixes JVM crash)
sudo mkdir -p /var/log/wazuh-indexer
sudo chown -R wazuh-indexer:wazuh-indexer /var/log/wazuh-indexer 2>/dev/null || true

# Kill any processes on ports Wazuh needs (docker-proxy from Shuffle)
for PORT in 1514 1515 9300; do
  PIDS=$(sudo ss -tlnp | grep ":$PORT " | grep -oP 'pid=\K[0-9]+' | sort -u)
  for PID in $PIDS; do
    sudo kill -9 $PID 2>/dev/null || true
  done
done

# Install all Wazuh components
sudo bash wazuh-install.sh --wazuh-indexer node-1
sudo bash wazuh-install.sh --start-cluster
sudo bash wazuh-install.sh --wazuh-server wazuh-1
sudo bash wazuh-install.sh --wazuh-dashboard dashboard

# Change Wazuh indexer port to 9201 (avoid conflict with Shuffle OpenSearch on 9200)
echo "http.port: 9201" | sudo tee -a /etc/wazuh-indexer/opensearch.yml

# Create log dir again in case install removed it
sudo mkdir -p /var/log/wazuh-indexer
sudo chown -R wazuh-indexer:wazuh-indexer /var/log/wazuh-indexer

sudo systemctl restart wazuh-indexer
sleep 20
sudo systemctl restart wazuh-manager
sudo systemctl restart wazuh-dashboard

echo "[4/6] Wazuh installed — dashboard at https://$(hostname -I | awk '{print $1}')"
echo "      Login: admin / (shown during installation)"

# ---- 5. LOGSTASH ----
echo "[5/6] Installing Logstash..."

wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
sudo apt update && sudo apt install -y logstash

# Deploy pipeline config
sudo cp /opt/thesis-repo/config/logstash-soar.conf /etc/logstash/conf.d/thesis.conf

sudo systemctl enable logstash
sudo systemctl start logstash

echo "[5/6] Logstash running"

# ---- 6. UFW FIREWALL ----
echo "[6/6] Configuring UFW..."

sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH
sudo ufw allow 22/tcp

# Shuffle
sudo ufw allow 3001/tcp
sudo ufw allow 5001/tcp

# Wazuh
sudo ufw allow 443/tcp
sudo ufw allow 1514/tcp
sudo ufw allow 1515/tcp
sudo ufw allow 55000/tcp
sudo ufw allow 9200/tcp
sudo ufw allow 9201/tcp
sudo ufw allow 9300/tcp

# Logstash
sudo ufw allow 5044/tcp
sudo ufw allow 514/udp

echo "[6/6] UFW configured"

echo ""
echo "========================================================"
echo " Setup Complete!"
echo "========================================================"
echo " Shuffle:         http://$(hostname -I | awk '{print $1}'):3001"
echo " Wazuh Dashboard: https://$(hostname -I | awk '{print $1}')"
echo " Wazuh Login:     admin / (shown during install)"
echo ""
echo " Port layout:"
echo "   Shuffle OpenSearch: 9200"
echo "   Wazuh Indexer:      9201"
echo "   Wazuh Dashboard:    443"
echo "   Shuffle Frontend:   3001"
echo "   Wazuh Manager:      1514"
echo "   Logstash Beats:     5044"
echo "   Logstash Syslog:    514/udp"
echo "========================================================"
