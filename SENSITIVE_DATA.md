# Sensitive Data Notice

This repository was created as part of an academic Master's thesis at University West, Sweden (2026).

All API keys, passwords, IP addresses, and credentials used in the original testbed have been **removed or replaced with placeholders** before publication.

---

## What Has Been Removed

| Item | Placeholder Used | How to Get Yours |
|------|-----------------|-----------------|
| AbuseIPDB API key | `YOUR_ABUSEIPDB_KEY` | Register at https://www.abuseipdb.com/account/api |
| TheHive API key | `YOUR_THEHIVE_API_KEY` | TheHive UI → Admin → API Keys |
| FortiGate REST API key | `YOUR_FORTIGATE_API_KEY` | FortiGate → System → Administrators → Create REST API admin |
| FortiGate WAN IP | `YOUR_FORTIGATE_IP` | Your firewall's WAN interface IP |
| SOAR machine IP | `YOUR_SOAR_IP` | Your SOAR server IP |
| T-Pot machine IP | `YOUR_TPOT_IP` | Your honeypot server IP |
| Shuffle webhook ID | `YOUR_SHUFFLE_WEBHOOK_ID` | Shuffle UI → Workflows → Webhook trigger → Copy URL |
| TheHive org credentials | Removed | Set up your own org in TheHive admin panel |

---

## Files Containing Placeholders

- `scripts/soar_proxy/abuseipdb_proxy.py` — AbuseIPDB key, TheHive key, FortiGate key and IP
- `scripts/wazuh/custom-thehive` — TheHive key and URL
- `scripts/wazuh/fortigate-block.sh` — Proxy URL (localhost by default)
- `configs/wazuh/ossec.conf` — TheHive API key in integration block
- `configs/logstash/logstash.conf` — Shuffle webhook ID in HTTP output URL

---

## Before Running

1. Replace all placeholders in the files listed above
2. Never commit real API keys to a public repository
3. Add your `.env` file to `.gitignore` if you use one
4. The `soar-proxy.service` systemd file supports environment variable injection — use that for production deployments

---

## Testbed IPs (Used in Study — No Longer Active)

The original testbed used the following IP addresses during the research period (March–April 2026). These machines are no longer exposed to the internet and these IPs are listed here only for documentation purposes:

- SOAR machine: `193.10.203.151`
- T-Pot honeypot: `193.10.203.150`
- FortiGate WAN: `193.10.203.159`

---

## Contact

For questions about the implementation:

- Alphonse Joseph — alphonse.joseph@student.hv.se
- Filmon Mehari Gebrezghi — filmon-mehari.gebrezghi@student.hv.se
