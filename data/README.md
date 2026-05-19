# Data

## sample_alerts/wazuh_sample_100.json

Contains 10 representative sample alerts from the 100-alert random sample used for manual labelling in the thesis.

The full 100-alert sample is not included to avoid potential privacy concerns with real attack data. The 10 samples here show the alert format and the distribution of alert types:

- Rule 5760: SSH authentication failed (True Positive)
- Rule 52004: AppArmor DENIED (True Positive)  
- Rule 19007-19009: CIS benchmark compliance (False Positive)
- Rule 2901-2904: dpkg package events (False Positive)
- Rule 5501-5502: PAM login sessions (False Positive)
- Rule 40704: Systemd service failures (Gray)

## Labelling Results (100 alerts)

| Label | Count | Percentage | Primary Rule IDs |
|-------|-------|------------|-----------------|
| True Positive (TP) | 5 | 5% | 5760, 5503, 52004 |
| False Positive (FP) | 60 | 60% | 19007-19009, 2901-2904, 5501-5502 |
| Gray | 35 | 35% | 40704 |

**Cohen's Kappa:** 0.87 (almost perfect inter-rater agreement)
