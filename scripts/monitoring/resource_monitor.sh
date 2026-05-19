#!/bin/bash
# ============================================================
# Resource Monitor — CPU and RAM Logger
# ============================================================
# Location: /opt/scripts/resource_monitor.sh
# Runs as: systemd service (resource-monitor.service)
# Output: /opt/scripts/resource_log.csv
#
# Records CPU and RAM usage every 60 seconds.
# Used for measuring resource consumption metric in thesis.
#
# Author: Alphonse Joseph & Filmon Mehari Gebrezghi
# University West, 2026
# ============================================================

LOG="/opt/scripts/resource_log.csv"
INTERVAL=60

# Create CSV header if file does not exist
if [ ! -f "$LOG" ]; then
    echo "timestamp,cpu_percent,ram_used_gb,ram_total_gb,ram_percent,load_avg_1m" > "$LOG"
    echo "Log file created: $LOG"
fi

echo "Resource monitor started. Logging every ${INTERVAL}s to $LOG"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    # CPU usage (percentage idle subtracted from 100)
    CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')

    # RAM usage
    RAM_USED=$(free -g | awk '/^Mem:/{print $3}')
    RAM_TOTAL=$(free -g | awk '/^Mem:/{print $2}')
    RAM_PCT=$(free | awk '/^Mem:/{printf "%.1f", $3/$2*100}')

    # Load average (1 minute)
    LOAD=$(cat /proc/loadavg | awk '{print $1}')

    # Write to CSV
    echo "$TIMESTAMP,$CPU,$RAM_USED,$RAM_TOTAL,$RAM_PCT,$LOAD" >> "$LOG"

    sleep "$INTERVAL"
done
