#!/usr/bin/env python3
# ============================================================
# Alert Sampling Script
# ============================================================
# Randomly samples 100 alerts from Wazuh alert log for
# manual labelling and Cohen's Kappa calculation.
#
# Usage:
#   python3 sampling.py
#
# Output:
#   /opt/scripts/wazuh_sample_100.json
#
# Author: Alphonse Joseph & Filmon Mehari Gebrezghi
# University West, 2026
# ============================================================

import json
import random
import os
import sys
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────────
ALERTS_FILE  = '/var/ossec/logs/alerts/alerts.json'
OUTPUT_FILE  = '/opt/scripts/wazuh_sample_100.json'
SAMPLE_SIZE  = 100
RANDOM_SEED  = 42   # Set seed for reproducibility
# ──────────────────────────────────────────────────────────────────────────────


def load_alerts(filepath):
    """Load all alerts from Wazuh JSON alert log."""
    alerts = []
    errors = 0

    if not os.path.exists(filepath):
        print(f"ERROR: Alert file not found: {filepath}")
        sys.exit(1)

    with open(filepath, 'r') as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                alert = json.loads(line)
                alerts.append(alert)
            except json.JSONDecodeError:
                errors += 1

    print(f"Loaded {len(alerts)} alerts ({errors} parse errors)")
    return alerts


def sample_alerts(alerts, n=100, seed=42):
    """Randomly sample n alerts."""
    random.seed(seed)
    if len(alerts) < n:
        print(f"WARNING: Only {len(alerts)} alerts available, sampling all.")
        return alerts
    return random.sample(alerts, n)


def print_summary(sample):
    """Print summary of sampled alerts."""
    rule_counts = {}
    for alert in sample:
        rule_id = alert.get('rule', {}).get('id', 'unknown')
        rule_desc = alert.get('rule', {}).get('description', 'No description')
        key = f"{rule_id}: {rule_desc}"
        rule_counts[key] = rule_counts.get(key, 0) + 1

    print("\n── Sampled Alert Distribution ──────────────────")
    for rule, count in sorted(rule_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"  {count:3d}  {rule}")
    print(f"\nTotal sampled: {len(sample)}")


def save_sample(sample, output_file):
    """Save sampled alerts to output file."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        for alert in sample:
            f.write(json.dumps(alert) + '\n')
    print(f"\nSaved to: {output_file}")


def generate_labelling_sheet(sample):
    """Print labelling sheet for manual classification."""
    print("\n── Manual Labelling Sheet ──────────────────────")
    print("Label each alert as: TP / FP / Gray")
    print("=" * 60)

    for i, alert in enumerate(sample, 1):
        rule_id   = alert.get('rule', {}).get('id', 'N/A')
        rule_desc = alert.get('rule', {}).get('description', 'N/A')
        level     = alert.get('rule', {}).get('level', 'N/A')
        agent     = alert.get('agent', {}).get('name', 'N/A')
        timestamp = alert.get('timestamp', 'N/A')
        src_ip    = alert.get('data', {}).get('srcip', 'N/A')

        print(f"\n--- Alert #{i} ---")
        print(f"  Rule ID:     {rule_id}")
        print(f"  Description: {rule_desc}")
        print(f"  Level:       {level}")
        print(f"  Agent:       {agent}")
        print(f"  Source IP:   {src_ip}")
        print(f"  Time:        {timestamp}")
        print(f"  Label:       [ TP / FP / Gray ]")


def main():
    print("=" * 60)
    print("Wazuh Alert Sampling Script")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Load alerts
    alerts = load_alerts(ALERTS_FILE)

    # Sample
    sample = sample_alerts(alerts, SAMPLE_SIZE, RANDOM_SEED)

    # Summary
    print_summary(sample)

    # Save
    save_sample(sample, OUTPUT_FILE)

    # Print labelling sheet
    generate_labelling_sheet(sample)

    print("\nDone. Share the output file with both researchers for independent labelling.")


if __name__ == "__main__":
    main()
