#!/usr/bin/env python3
"""
Wazuh → TheHive Case Creation Script
File: /var/ossec/active-response/bin/thehive-connector.py

This script is called by Wazuh active response when an alert fires.
It creates a case in TheHive with the alert details and adds the
source IP as an observable.

Usage: Called automatically by Wazuh active response framework.
Manual test: python3 thehive-connector.py add - alert_json
"""

import sys
import json
import datetime
import requests

# ---- CONFIGURATION ----
THEHIVE_URL = "http://localhost:9000"
THEHIVE_API_KEY = "REPLACE_WITH_THEHIVE_API_KEY"
HEADERS = {
    "Authorization": f"Bearer {THEHIVE_API_KEY}",
    "Content-Type": "application/json"
}

def create_case(alert):
    """Create a TheHive case from a Wazuh alert."""
    rule_id    = alert.get("rule", {}).get("id", "unknown")
    rule_desc  = alert.get("rule", {}).get("description", "No description")
    src_ip     = alert.get("data", {}).get("srcip", alert.get("data", {}).get("src_ip", "unknown"))
    agent_name = alert.get("agent", {}).get("name", "unknown")
    timestamp  = alert.get("timestamp", datetime.datetime.utcnow().isoformat())
    severity   = alert.get("rule", {}).get("level", 3)

    # Map Wazuh level (1-15) to TheHive severity (1-4)
    if severity >= 12:
        thehive_severity = 4   # Critical
    elif severity >= 9:
        thehive_severity = 3   # High
    elif severity >= 6:
        thehive_severity = 2   # Medium
    else:
        thehive_severity = 1   # Low

    case_payload = {
        "title": f"Wazuh Alert [{rule_id}]: {rule_desc[:80]}",
        "description": (
            f"**Automated case created by Wazuh active response**\n\n"
            f"- **Rule ID:** {rule_id}\n"
            f"- **Description:** {rule_desc}\n"
            f"- **Source IP:** {src_ip}\n"
            f"- **Agent:** {agent_name}\n"
            f"- **Timestamp:** {timestamp}\n"
            f"- **Wazuh Level:** {severity}\n\n"
            f"**Raw Alert:**\n```json\n{json.dumps(alert, indent=2)}\n```"
        ),
        "severity": thehive_severity,
        "tlp": 2,
        "tags": ["wazuh", "automated", f"rule-{rule_id}", agent_name],
        "flag": False
    }

    resp = requests.post(
        f"{THEHIVE_URL}/api/v1/case",
        headers=HEADERS,
        json=case_payload,
        timeout=10,
        verify=False
    )
    resp.raise_for_status()
    case = resp.json()
    case_id = case.get("_id")
    print(f"[+] Created TheHive case: {case_id}")

    # Add source IP as observable
    if src_ip and src_ip != "unknown":
        obs_payload = {
            "dataType": "ip",
            "data": src_ip,
            "message": f"Attacker source IP from Wazuh rule {rule_id}",
            "tlp": 2,
            "ioc": True,
            "sighted": True,
            "tags": ["attacker", "source-ip", f"rule-{rule_id}"]
        }
        obs_resp = requests.post(
            f"{THEHIVE_URL}/api/v1/case/{case_id}/observable",
            headers=HEADERS,
            json=obs_payload,
            timeout=10,
            verify=False
        )
        if obs_resp.ok:
            print(f"[+] Added observable: {src_ip}")
        else:
            print(f"[!] Failed to add observable: {obs_resp.text}", file=sys.stderr)

    return case_id


def main():
    """Wazuh active response entry point."""
    # Wazuh passes: action - alert_json
    if len(sys.argv) < 3:
        print("Usage: thehive-connector.py <action> - <alert_json>", file=sys.stderr)
        sys.exit(1)

    action = sys.argv[1]
    if action not in ("add", "delete"):
        sys.exit(0)

    # Read alert JSON from stdin or argument
    try:
        alert_data = sys.stdin.read().strip()
        if not alert_data:
            alert_data = sys.argv[3] if len(sys.argv) > 3 else "{}"
        alert = json.loads(alert_data)
    except (json.JSONDecodeError, IndexError) as e:
        print(f"[!] Failed to parse alert: {e}", file=sys.stderr)
        sys.exit(1)

    if action == "add":
        try:
            create_case(alert)
        except requests.RequestException as e:
            print(f"[!] TheHive API error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
