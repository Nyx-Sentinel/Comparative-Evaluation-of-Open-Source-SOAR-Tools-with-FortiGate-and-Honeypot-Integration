#!/bin/bash
# =============================================================
# Resource Monitoring Script
# Records CPU and RAM usage every 5 minutes for 24 hours
# Used to measure Metric 5 (CPU) and Metric 6 (RAM) for thesis
#
# Run on SOAR machine (193.10.203.151) on Collection Day 7
# (steady-state operation, both platforms running)
#
# Usage:
#   chmod +x resource_monitor.sh
#   nohup ./resource_monitor.sh > /tmp/resource_log.csv 2>&1 &
#
# Output CSV: timestamp, shuffle_cpu, shuffle_ram_gb, wazuh_cpu, wazuh_ram_gb, total_cpu, total_ram_gb
# =============================================================

OUTPUT_FILE="/tmp/resource_monitor_$(date +%Y%m%d_%H%M%S).csv"
INTERVAL=300     # 5 minutes in seconds
DURATION=86400   # 24 hours in seconds
END_TIME=$((SECONDS + DURATION))

echo "timestamp,shuffle_cpu_%,shuffle_ram_mb,wazuh_cpu_%,wazuh_ram_mb,system_cpu_%,system_ram_gb" | tee "$OUTPUT_FILE"
echo "[+] Monitoring started — logging to $OUTPUT_FILE"
echo "[+] Duration: 24 hours | Interval: 5 minutes | Samples: ~288"

while [ $SECONDS -lt $END_TIME ]; do
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # --- Shuffle CPU/RAM (all shuffle-* containers) ---
    SHUFFLE_STATS=$(sudo docker stats --no-stream --format "{{.CPUPerc}},{{.MemUsage}}" \
        $(sudo docker ps --filter "name=shuffle" -q) 2>/dev/null)

    SHUFFLE_CPU=0
    SHUFFLE_RAM=0
    while IFS=',' read -r cpu mem; do
        # Strip % from CPU
        cpu_val=$(echo "$cpu" | tr -d '%')
        # Extract MB from memory (e.g. "245.3MiB / 15.6GiB")
        mem_val=$(echo "$mem" | awk '{print $1}' | tr -d 'MiB')
        SHUFFLE_CPU=$(awk "BEGIN {print $SHUFFLE_CPU + $cpu_val}")
        SHUFFLE_RAM=$(awk "BEGIN {print $SHUFFLE_RAM + $mem_val}")
    done <<< "$SHUFFLE_STATS"

    # --- Wazuh CPU/RAM (systemd services) ---
    WAZUH_CPU=$(ps aux | grep -E "wazuh|opensearch" | grep -v grep | \
        awk '{sum+=$3} END {printf "%.1f", sum}')
    WAZUH_RAM=$(ps aux | grep -E "wazuh|opensearch" | grep -v grep | \
        awk '{sum+=$4} END {printf "%.0f", sum}')
    # Convert % RAM to MB (approximate, based on total system RAM)
    TOTAL_RAM_MB=$(free -m | awk '/^Mem:/{print $2}')
    WAZUH_RAM_MB=$(awk "BEGIN {print int($WAZUH_RAM * $TOTAL_RAM_MB / 100)}")

    # --- System-wide CPU and RAM ---
    SYSTEM_CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | tr -d '%us,')
    SYSTEM_RAM_GB=$(free -g | awk '/^Mem:/{print $3}')

    # Write to CSV
    echo "$TIMESTAMP,$SHUFFLE_CPU,$SHUFFLE_RAM,$WAZUH_CPU,$WAZUH_RAM_MB,$SYSTEM_CPU,$SYSTEM_RAM_GB" | \
        tee -a "$OUTPUT_FILE"

    sleep $INTERVAL
done

echo ""
echo "[+] Monitoring complete. Results saved to: $OUTPUT_FILE"
echo ""
echo "=== SUMMARY ==="
echo "Shuffle avg CPU: $(awk -F',' 'NR>1 {sum+=$2; count++} END {printf "%.1f%%", sum/count}' "$OUTPUT_FILE")"
echo "Shuffle avg RAM: $(awk -F',' 'NR>1 {sum+=$3; count++} END {printf "%.0f MB", sum/count}' "$OUTPUT_FILE")"
echo "Wazuh avg CPU:   $(awk -F',' 'NR>1 {sum+=$4; count++} END {printf "%.1f%%", sum/count}' "$OUTPUT_FILE")"
echo "Wazuh avg RAM:   $(awk -F',' 'NR>1 {sum+=$5; count++} END {printf "%.0f MB", sum/count}' "$OUTPUT_FILE")"
