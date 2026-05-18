#!/bin/bash
# ============================================================
# WZ-PB1: FortiGate IP Blocking — Wazuh Active Response
# ============================================================
# Location: /var/ossec/active-response/bin/fortigate-block.sh
# Triggered by: Wazuh manager at rule level 6+
# Action: Blocks source IP on FortiGate via REST API
#
# Usage (called automatically by Wazuh):
#   fortigate-block.sh add|delete <username> <ip> <alert_id> <rule_id>
#
# Author: Alphonse Joseph & Filmon Mehari Gebrezghi
# University West, 2026
# ============================================================

PROXY_URL="http://localhost:9090"
LOG_FILE="/var/ossec/logs/active-responses.log"

# Read arguments passed by Wazuh
ACTION=$1
USER=$2
IP=$3
ALERT_ID=$4
RULE_ID=$5

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Validate IP
if [ -z "$IP" ] || [ "$IP" = "None" ]; then
    echo "[$TIMESTAMP] ERROR: No IP provided. Skipping." >> "$LOG_FILE"
    exit 1
fi

# Only act on add (block) action
if [ "$ACTION" = "add" ]; then
    echo "[$TIMESTAMP] Blocking IP: $IP (Alert: $ALERT_ID, Rule: $RULE_ID)" >> "$LOG_FILE"

    RESPONSE=$(curl -s -o /tmp/fortigate_response.json -w "%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{\"ip\": \"$IP\", \"alert_id\": \"$ALERT_ID\", \"rule_id\": \"$RULE_ID\"}" \
        "$PROXY_URL/block")

    echo "[$TIMESTAMP] FortiGate response HTTP $RESPONSE for IP $IP" >> "$LOG_FILE"

    if [ "$RESPONSE" = "200" ]; then
        echo "[$TIMESTAMP] SUCCESS: IP $IP blocked on FortiGate." >> "$LOG_FILE"
        exit 0
    else
        echo "[$TIMESTAMP] FAILED: Could not block IP $IP. HTTP $RESPONSE" >> "$LOG_FILE"
        exit 1
    fi

elif [ "$ACTION" = "delete" ]; then
    echo "[$TIMESTAMP] Unblock action for $IP (not implemented in this study)" >> "$LOG_FILE"
    exit 0

else
    echo "[$TIMESTAMP] Unknown action: $ACTION" >> "$LOG_FILE"
    exit 1
fi
