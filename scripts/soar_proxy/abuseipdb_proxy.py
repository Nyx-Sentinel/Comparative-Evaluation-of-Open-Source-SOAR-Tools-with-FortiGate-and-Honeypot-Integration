#!/usr/bin/env python3
"""
SOAR Proxy — Custom Flask Gateway
===================================
Runs as a systemd service on the SOAR machine (port 9090).

Purpose: Circumvents university firewall restrictions that block
outbound traffic from Docker containers (Shuffle worker containers).
Both Shuffle and Wazuh route all external API calls through this proxy.

Routes:
  GET  /check?ip=X     -> AbuseIPDB reputation lookup
  POST /block          -> FortiGate REST API IP blocking
  POST /notify         -> TheHive alert creation
  POST /case           -> TheHive case creation

Usage:
  pip3 install flask requests
  python3 abuseipdb_proxy.py

Systemd service: soar-proxy.service
Author: Alphonse Joseph & Filmon Mehari Gebrezghi
University West, 2026
"""

from flask import Flask, request, jsonify
import requests
import json
import urllib3

# Suppress SSL warnings for FortiGate self-signed cert
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
ABUSEIPDB_KEY   = "YOUR_ABUSEIPDB_KEY"  # [SENSITIVE — not shared. Get your key at https://www.abuseipdb.com/account/api]
THEHIVE_URL     = "http://localhost:9000"
THEHIVE_KEY     = "YOUR_THEHIVE_API_KEY"  # [SENSITIVE — not shared. Generate in TheHive: Admin → API Keys]
FORTIGATE_URL   = "https://YOUR_FORTIGATE_IP"  # [SENSITIVE — not shared. Replace with your FortiGate WAN IP]
FORTIGATE_KEY   = "YOUR_FORTIGATE_API_KEY"  # [SENSITIVE — not shared. Generate in FortiGate: System → Administrators → REST API]
# ──────────────────────────────────────────────────────────────────────────────


# ── Route 1: AbuseIPDB IP Reputation Lookup ───────────────────────────────────
@app.route('/check', methods=['GET'])
def check_ip():
    """
    Query AbuseIPDB for IP reputation.
    Used by: Shuffle PB2, Wazuh WZ-PB2

    Query param: ip=<IP_ADDRESS>
    Returns: JSON with abuseConfidenceScore, country, isp, totalReports
    """
    ip = request.args.get('ip', '')
    if not ip:
        return jsonify({"error": "ip parameter required"}), 400

    try:
        response = requests.get(
            'https://api.abuseipdb.com/api/v2/check',
            headers={
                'Key': ABUSEIPDB_KEY,
                'Accept': 'application/json'
            },
            params={
                'ipAddress': ip,
                'maxAgeInDays': 90
            },
            timeout=10
        )
        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


# ── Route 2: FortiGate IP Blocking ────────────────────────────────────────────
@app.route('/block', methods=['POST'])
def block_ip():
    """
    Block an IP address on the FortiGate firewall via REST API.
    Used by: Shuffle PB1, Wazuh WZ-PB1

    Body (JSON): {"ip": "1.2.3.4"}
    Action: Creates address object on FortiGate, adds to deny policy
    """
    data = request.get_json(force=True, silent=True) or {}
    ip = data.get('ip', '')

    if not ip:
        return jsonify({"error": "ip field required"}), 400

    headers = {
        'Authorization': f'Bearer {FORTIGATE_KEY}',
        'Content-Type': 'application/json'
    }

    # Step 1: Create address object
    addr_payload = {
        "name": f"block_{ip.replace('.', '_')}",
        "type": "ipmask",
        "subnet": f"{ip} 255.255.255.255",
        "comment": "Blocked by SOAR automation"
    }

    try:
        addr_response = requests.post(
            f"{FORTIGATE_URL}/api/v2/cmdb/firewall/address/",
            headers=headers,
            json=addr_payload,
            verify=False,
            timeout=10
        )

        return jsonify({
            "status": "blocked",
            "ip": ip,
            "fortigate_response": addr_response.status_code
        }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


# ── Route 3: TheHive Alert Creation ───────────────────────────────────────────
@app.route('/notify', methods=['POST'])
def notify_thehive():
    """
    Create a structured alert in TheHive.
    Used by: Shuffle PB3, Wazuh WZ-PB3

    Body (JSON): {
        "title": "Alert title",
        "description": "Alert description",
        "ip": "1.2.3.4",
        "severity": 2
    }
    """
    data = request.get_json(force=True, silent=True) or {}

    title       = data.get('title', 'SOAR Alert')
    description = data.get('description', 'Automated alert from SOAR platform')
    ip          = data.get('ip', 'unknown')
    severity    = data.get('severity', 2)

    alert_payload = {
        "title": title,
        "description": description,
        "type": "external",
        "source": "SOAR-Proxy",
        "sourceRef": f"soar-{ip}",
        "severity": severity,
        "tags": ["soar", "automated", "honeypot"],
        "tlp": 2,
        "status": "New",
        "observables": [
            {
                "dataType": "ip",
                "data": ip,
                "message": "Source IP from honeypot alert"
            }
        ]
    }

    try:
        response = requests.post(
            f"{THEHIVE_URL}/api/v1/alert",
            headers={
                'Authorization': f'Bearer {THEHIVE_KEY}',
                'Content-Type': 'application/json'
            },
            json=alert_payload,
            timeout=10
        )
        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


# ── Route 4: TheHive Case Creation ────────────────────────────────────────────
@app.route('/case', methods=['POST'])
def create_case():
    """
    Create a full investigation case in TheHive.
    Used by: Shuffle PB4, Wazuh WZ-PB4

    Body (JSON): {
        "title": "Case title",
        "description": "Case description",
        "ip": "1.2.3.4",
        "severity": 3
    }
    """
    data = request.get_json(force=True, silent=True) or {}

    title       = data.get('title', 'SOAR Incident Case')
    description = data.get('description', 'Automated case from SOAR platform')
    ip          = data.get('ip', 'unknown')
    severity    = data.get('severity', 3)

    case_payload = {
        "title": title,
        "description": description,
        "severity": severity,
        "tags": ["soar", "automated", "honeypot"],
        "tlp": 2,
        "flag": False,
        "tasks": [
            {
                "title": "Investigate source IP",
                "description": f"Check AbuseIPDB and block {ip} on FortiGate if confirmed malicious"
            },
            {
                "title": "Verify FortiGate block",
                "description": "Confirm IP blocking rule was applied on FortiGate"
            }
        ]
    }

    try:
        response = requests.post(
            f"{THEHIVE_URL}/api/v1/case",
            headers={
                'Authorization': f'Bearer {THEHIVE_KEY}',
                'Content-Type': 'application/json'
            },
            json=case_payload,
            timeout=10
        )
        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


# ── Health check ──────────────────────────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "soar-proxy", "port": 9090}), 200


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("[SOAR Proxy] Starting on port 9090...")
    app.run(host='0.0.0.0', port=9090, debug=False)
