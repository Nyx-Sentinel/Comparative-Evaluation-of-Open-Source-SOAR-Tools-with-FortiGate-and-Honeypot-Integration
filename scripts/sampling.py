#!/usr/bin/env python3
"""
Alert Sampling Script
=====================
Randomly samples 100 alerts from each SOAR platform's execution logs
for the manual labelling phase of the thesis evaluation.

Usage:
    python3 sampling.py --platform shuffle --input executions.json --output sample_shuffle.csv
    python3 sampling.py --platform wazuh   --input alerts.json     --output sample_wazuh.csv

Output CSV columns:
    alert_id, timestamp, src_ip, alert_type, platform, playbook_triggered,
    execution_success, latency_seconds, label (TP/FP/Gray), notes

Authors: Filmon Mehari Gebrezghi & Alphonse Joseph
University West, 2026
"""

import argparse
import csv
import json
import random
import sys
from datetime import datetime
from pathlib import Path


def load_shuffle_executions(filepath: str) -> list:
    """Load and normalize Shuffle execution log entries."""
    with open(filepath) as f:
        data = json.load(f)

    records = []
    for execution in data:
        records.append({
            "alert_id":           execution.get("execution_id", ""),
            "timestamp":          execution.get("started_at", ""),
            "src_ip":             execution.get("extra", {}).get("src_ip", ""),
            "alert_type":         execution.get("extra", {}).get("type", ""),
            "platform":           "shuffle",
            "playbook_triggered": execution.get("workflow_id", ""),
            "execution_success":  str(execution.get("status", "") == "FINISHED"),
            "latency_seconds":    _calc_latency(
                execution.get("started_at", ""),
                execution.get("completed_at", "")
            ),
            "label":              "",
            "notes":              ""
        })
    return records


def load_wazuh_alerts(filepath: str) -> list:
    """Load and normalize Wazuh alert log entries."""
    records = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                alert = json.loads(line)
            except json.JSONDecodeError:
                continue

            records.append({
                "alert_id":           alert.get("id", ""),
                "timestamp":          alert.get("timestamp", ""),
                "src_ip":             alert.get("data", {}).get("srcip",
                                      alert.get("data", {}).get("src_ip", "")),
                "alert_type":         alert.get("rule", {}).get("description", ""),
                "platform":           "wazuh",
                "playbook_triggered": str(alert.get("rule", {}).get("id", "")),
                "execution_success":  "True",   # Wazuh alert = rule fired successfully
                "latency_seconds":    "",       # Filled from active-response log
                "label":              "",
                "notes":              ""
            })
    return records


def _calc_latency(start: str, end: str) -> str:
    """Calculate latency in seconds between two ISO timestamps."""
    if not start or not end:
        return ""
    try:
        fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
        t1 = datetime.strptime(start[:26] + "Z", fmt)
        t2 = datetime.strptime(end[:26] + "Z", fmt)
        return f"{(t2 - t1).total_seconds():.2f}"
    except ValueError:
        return ""


def sample_alerts(records: list, n: int = 100, seed: int = 42) -> list:
    """
    Randomly sample n alerts.
    Uses fixed seed for reproducibility — both researchers sample identically.
    """
    random.seed(seed)
    if len(records) <= n:
        print(f"[!] Only {len(records)} records available — using all of them.")
        return records
    return random.sample(records, n)


def write_csv(records: list, output_path: str):
    """Write sampled alerts to CSV for manual labelling."""
    fields = [
        "alert_id", "timestamp", "src_ip", "alert_type",
        "platform", "playbook_triggered", "execution_success",
        "latency_seconds", "label", "notes"
    ]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    print(f"[+] Wrote {len(records)} sampled alerts to: {output_path}")
    print(f"    Fill in 'label' column: TP (True Positive), FP (False Positive), Gray")
    print(f"    Use 'notes' for justification on Gray cases")


def main():
    parser = argparse.ArgumentParser(
        description="Sample 100 alerts for manual labelling (thesis evaluation)"
    )
    parser.add_argument("--platform", choices=["shuffle", "wazuh"], required=True)
    parser.add_argument("--input",    required=True, help="Path to execution/alert JSON file")
    parser.add_argument("--output",   required=True, help="Output CSV file path")
    parser.add_argument("--n",        type=int, default=100, help="Number of alerts to sample")
    parser.add_argument("--seed",     type=int, default=42,  help="Random seed for reproducibility")
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"[!] Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"[+] Loading {args.platform} data from: {args.input}")

    if args.platform == "shuffle":
        records = load_shuffle_executions(args.input)
    else:
        records = load_wazuh_alerts(args.input)

    print(f"[+] Loaded {len(records)} total records")

    sampled = sample_alerts(records, n=args.n, seed=args.seed)
    write_csv(sampled, args.output)


if __name__ == "__main__":
    main()
