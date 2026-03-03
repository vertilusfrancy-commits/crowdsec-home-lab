# 🛡️ Home Cybersecurity Lab — SSH Brute Force Detection with CrowdSec

> **Author:** Vertilus Francy  
> **Environment:** VirtualBox | Ubuntu Server 22.04 | Windows 10 (UTM)  
> **Focus:** Intrusion Detection, Log Analysis, Firewall Bouncer Configuration

---

## 📌 Overview

This project documents the setup and operation of a personal cybersecurity lab designed to simulate, detect, and block SSH brute force attacks using **CrowdSec** — an open-source, collaborative Intrusion Prevention System (IPS).

The lab was built to develop hands-on skills in:
- Host-based intrusion detection
- Log analysis and alert triage
- Firewall bouncer configuration
- Attack simulation and troubleshooting

---

## 🖥️ Lab Architecture

```
┌─────────────────────┐         SSH Brute Force         ┌─────────────────────┐
│   Windows 10 VM     │ ──────────────────────────────► │   Ubuntu Server     │
│   (Attacker)        │         192.168.100.4            │   22.04 (Target)    │
│   UTM / VirtualBox  │                                  │   CrowdSec + SSHD   │
└─────────────────────┘                                  └─────────────────────┘
                                  Local Network: 192.168.100.0/24
```

| Component | Details |
|-----------|---------|
| Hypervisor | Oracle VirtualBox |
| Target OS | Ubuntu Server 22.04 LTS |
| Attacker OS | Windows 10 (UTM) |
| IPS | CrowdSec + cs-firewall-bouncer |
| Scenario | crowdsecurity/ssh-bf |
| Network | Internal LAN (isolated) |

---

## ⚙️ Setup & Configuration

### 1. CrowdSec Installation (Ubuntu)

```bash
curl -s https://packagecloud.io/install/repositories/crowdsec/crowdsec/script.deb.sh | sudo bash
sudo apt install crowdsec -y
sudo apt install crowdsec-firewall-bouncer-nftables -y
```

### 2. SSH Collection

```bash
sudo cscli collections install crowdsecurity/sshd
sudo systemctl restart crowdsec
```

### 3. Firewall Bouncer Configuration

The bouncer was initially configured for `iptables`, which is not the default on Ubuntu 22.04. This was identified and corrected:

```bash
# /etc/crowdsec/bouncers/crowdsec-firewall-bouncer.yaml
mode: nftables   # Changed from iptables — Ubuntu 22.04 uses nftables by default
```

```bash
sudo systemctl restart crowdsec-firewall-bouncer
```

### 4. LAN Whitelist — Troubleshooting

CrowdSec includes a default whitelist that excludes private IP ranges (RFC 1918), including `192.168.0.0/16`. Since the attacker VM was on the same local network, this whitelist was preventing detection during the lab simulation.

**Solution:** The private range was commented out in the whitelist configuration for lab purposes:

```bash
# /etc/crowdsec/parsers/s02-enrich/crowdsecurity/whitelists.yaml
# - "192.168.0.0/16"   ← commented out for internal lab simulation
```

> ⚠️ **Note:** This change is intentional and scoped to this isolated lab environment. In production, this whitelist should remain active.

---

## ⚔️ Attack Simulation

A Python script was used to simulate a brute force attack from the Windows VM against the Ubuntu SSH service:

```python
import subprocess
import time

target = "192.168.100.12"
user = "usuario_falso"
passwords = [
    "123456","password","admin","root","test","qwerty","letmein",
    "abc123","pass123","welcome","monkey","dragon","master","hello",
    "shadow","sunshine","princess","football","charlie","donald",
    "password1","iloveyou","superman","batman","trustno1","access",
    "login","admin123","root123","toor","pass","1234","12345",
    "123123","111111","000000","654321","666666","888888","password2",
    "qwerty123","admin1","user","guest","test123","default","alpine",
    "raspberry","ubuntu","changeme"
]

for i, pwd in enumerate(passwords):
    print(f"[{i+1}/{len(passwords)}] Trying: {pwd}")
    try:
        subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no",
                    "-o", "ConnectTimeout=2",
                    "-o", "BatchMode=yes",
                    "-o", "NumberOfPasswordPrompts=1",
                    f"{user}@{target}"],
            timeout=3, capture_output=True
        )
    except Exception:
        pass
    time.sleep(0.3)
```

---

## 🔍 Detection Results

### auth.log — Failed Login Attempts

CrowdSec monitors `/var/log/auth.log` in real time. The attack generated multiple entries:

```
Mar 2 06:04:33 francy sshd[4096]: Invalid user usuario_falso from 192.168.100.4 port 39970
Mar 2 06:04:33 francy sshd[4096]: Connection reset by invalid user usuario_falso 192.168.100.4 port 39970 [preauth]
Mar 2 06:04:34 francy sshd[4098]: Invalid user usuario_falso from 192.168.100.4 port 43266
Mar 2 06:04:35 francy sshd[4102]: Invalid user usuario_falso from 192.168.100.4 port 41246
Mar 2 06:04:36 francy sshd[4104]: Invalid user usuario_falso from 192.168.100.4 port 40548
```

### Decision — IP Banned

After 6 failed attempts (capacity threshold: 5), CrowdSec triggered the `crowdsecurity/ssh-bf` scenario and issued a ban:

```
ID     | Source    | Scope:Value          | Reason                    | Action | Events | Expiration
-------|-----------|----------------------|---------------------------|--------|--------|----------
46796  | crowdsec  | Ip:192.168.100.4     | crowdsecurity/ssh-bf      | ban    | 6      | 3h 57m
```

### Alert Generated

```
ID | Value             | Reason                    | Decisions | Created At
---|-------------------|---------------------------|-----------|--------------------
6  | Ip:192.168.100.4  | crowdsecurity/ssh-bf      | ban:1     | 2026-03-02T06:04:33Z
```

### CrowdSec Metrics Summary

```
Local API Alerts:
  crowdsecurity/ssh-bf → 1 alert

Local API Decisions:
  crowdsecurity/ssh-bf   | crowdsec | ban  | 1
  generic:scan           | CAPI     | ban  | 57
  ssh:bruteforce         | CAPI     | ban  | 842

Bouncer Metrics:
  cs-firewall-bouncer    | active_decisions: 899 IPs | processed: 64.63M bytes / 14.76k packets

Scenario Metrics:
  crowdsecurity/ssh-bf          | Overflows: 1 | Poured: 10
  crowdsecurity/ssh-slow-bf     | Current Count: 1
  crowdsecurity/ssh-time-based  | Current Count: 1
```

---

## 🧠 Key Learnings

| Challenge | Root Cause | Solution |
|-----------|------------|----------|
| Bouncer not blocking IPs | Mode set to `iptables` on Ubuntu 22.04 | Changed to `nftables` in bouncer config |
| Attack not detected | LAN IP range whitelisted by default | Commented out `192.168.0.0/16` in whitelists.yaml for lab use |
| No decisions showing | Whitelist was silently dropping all events from private IPs | Identified via log analysis and crowdsec.log review |

---

## 📁 Repository Structure

```
├── README.md               ← This file
├── attack_simulation/
│   └── brute_force.py      ← SSH brute force simulation script
├── screenshots/
│   ├── auth_log.png        ← Failed login attempts in auth.log
│   ├── decisions_list.png  ← IP ban issued by CrowdSec
│   ├── alerts_list.png     ← Alert generated by ssh-bf scenario
│   └── metrics.png         ← CrowdSec full metrics output
└── config_notes/
    └── troubleshooting.md  ← Notes on iptables vs nftables and whitelist fix
```

---

## 🔧 Tools & Technologies

| Tool | Purpose |
|------|---------|
| CrowdSec | Collaborative IPS — detection engine |
| cs-firewall-bouncer | Enforcement layer (nftables) |
| OpenSSH Server | Attack surface (target service) |
| Python 3 | Attack simulation script |
| tmux | Multi-terminal monitoring during live attack |
| VirtualBox / UTM | Virtualization (isolated lab environment) |

---

## ⚠️ Disclaimer

This lab was conducted in a **fully isolated, private virtual network** on personal hardware. No external systems were targeted. All attack simulations were performed exclusively against virtual machines owned and controlled by the author for educational purposes only.

---

## 👤 Author

**Vertilus Francy**  
Junior Cybersecurity Professional | SOC Analyst Candidate  
📧 vertilusfrancy@hotmail.com  
🔗 [LinkedIn](https://www.linkedin.com/in/francy-vertilus-30b891151/)
