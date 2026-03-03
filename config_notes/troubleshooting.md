# Configuration Notes & Troubleshooting

## Issue 1 — Bouncer Not Blocking IPs

**Symptom:** CrowdSec was detecting the attack and generating alerts, but the attacker IP was never actually blocked at the firewall level.

**Root Cause:** The firewall bouncer was configured to use `iptables`, but Ubuntu 22.04 uses `nftables` by default. The two systems don't share rules, so the bouncer was running but applying rules to the wrong backend.

**Fix:**
```yaml
# /etc/crowdsec/bouncers/crowdsec-firewall-bouncer.yaml
mode: nftables   # was: iptables
```
Then restart:
```bash
sudo systemctl restart crowdsec-firewall-bouncer
```

---

## Issue 2 — Attack Not Being Detected

**Symptom:** The `auth.log` was showing failed login attempts, but `cscli decisions list` returned nothing. CrowdSec was completely silent.

**Root Cause:** CrowdSec ships with a default whitelist that excludes all RFC 1918 private IP ranges, including `192.168.0.0/16`. Since both VMs were on the same local network, every event from the attacker was silently whitelisted before reaching the detection engine.

**Fix:**
```bash
sudo nano /etc/crowdsec/parsers/s02-enrich/crowdsecurity/whitelists.yaml
```
Comment out the private range:
```yaml
# - "192.168.0.0/16"
```
Then restart:
```bash
sudo systemctl restart crowdsec
```

> ⚠️ This change is intentional and scoped to this isolated lab. In a production environment, this whitelist should remain active to avoid accidentally blocking legitimate internal traffic.

---

## Lesson Learned

Both issues were identified through systematic log analysis using `journalctl` and `crowdsec.log`, combined with network reasoning — recognizing that internal LAN traffic would be treated differently than external traffic by default security tools.
