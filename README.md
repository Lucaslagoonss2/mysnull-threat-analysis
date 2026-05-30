# MysNull Threat Analysis

![CI](https://github.com/Lucaslagoonss2/mysnull-threat-analysis/actions/workflows/ci.yml/badge.svg)

I built this repo while studying Blue Team and SOC workflows — I wanted to go beyond theory and actually work a case end to end, from PCAP triage to documented IOCs. The centerpiece is a real XLoader malware traffic investigation from January 2025: suspicious DNS, encoded HTTP GET requests, a JavaScript redirect, and outbound TCP to `76.223.54.146`. I wrote up the findings in Wireshark, kept analyst notes, and built a small Python extractor to pull IPs, domains, URLs, and hashes out of that kind of evidence. Everything here ran in a lab on traffic I had permission to analyze.

## Investigated Cases

| Case | Date | Malware | Report | Sample notes |
|------|------|---------|--------|--------------|
| XLoader traffic analysis | Jan 2025 | XLoader | [reports/xloader-analysis-report.md](reports/xloader-analysis-report.md) | [samples/xloader_traffic_notes.txt](samples/xloader_traffic_notes.txt) |
| Agent Tesla exfiltration | Feb 2025 | Agent Tesla | [reports/agent-tesla-analysis-report.md](reports/agent-tesla-analysis-report.md) | [samples/agent_tesla_traffic_notes.txt](samples/agent_tesla_traffic_notes.txt) |

## Quickstart
### Requirements
- Python 3.10+
- `pip`

### Install
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run demo
```bash
python main.py
```

Reads `samples/xloader_traffic_notes.txt` and prints the extracted IOCs from the XLoader case.

## Example commands
```bash
# Basic extraction (fast mode)
python extractors/ioc_extractor.py -i samples/xloader_traffic_notes.txt --no-animation

# Export both formats to a folder
python extractors/ioc_extractor.py -i samples/xloader_traffic_notes.txt -f txt json -o outputs --basename xloader_iocs --no-animation

# Verbose run for troubleshooting
python extractors/ioc_extractor.py -i samples/xloader_traffic_notes.txt --verbose --no-animation

# Defanged output for safe sharing in tickets
python extractors/ioc_extractor.py -i samples/xloader_traffic_notes.txt --defang --no-animation

# Agent Tesla case notes
python extractors/ioc_extractor.py -i samples/agent_tesla_traffic_notes.txt --no-animation
```

## Investigation workflow
1. Review suspicious evidence (traffic notes / packet-derived text)
2. Triage behavior across DNS, HTTP, and TCP signals
3. Extract candidate IOCs (IPs, domains, URLs, hashes)
4. Normalize and organize results
5. Export structured artifacts for reporting
6. Document findings in investigation notes

## Screenshots
### Suspicious DNS Resolution
![DNS Investigation](screenshots/suspicious_dns.png)

### External TCP Communication
![TCP Communication](screenshots/tcp_communication_with_suspicious_ip.png)

### HTTP Stream Analysis
![HTTP Stream](screenshots/follow_http_stream_analysis.png)

## Repository structure
```text
mysnull-threat-analysis/
├── .github/
│   └── workflows/
│       └── ci.yml
├── extractors/
│   ├── __init__.py
│   ├── ioc_extractor.py
│   └── rich_render.py
├── iocs/
│   ├── README.md
│   ├── agent-tesla-iocs.md
│   └── xloader-iocs.md
├── outputs/                  # export artifacts (generated at runtime)
├── pcap/
│   └── README.md
├── reports/
│   ├── README.md
│   ├── agent-tesla-analysis-report.md
│   └── xloader-analysis-report.md
├── samples/
│   ├── agent_tesla_traffic_notes.txt
│   ├── test.txt
│   └── xloader_traffic_notes.txt
├── screenshots/
│   ├── README.md
│   ├── follow_http_stream_analysis.png
│   ├── suspicious_dns.png
│   └── tcp_communication_with_suspicious_ip.png
├── tests/
│   └── test_ioc_extraction.py
├── .gitignore
├── LICENSE
├── main.py
├── requirements.txt
└── README.md
```

## Future roadmap
- Add SHA1 hash support
- Add preprocessing helpers for packet-derived text inputs
- Add reporting templates for faster case writeups
- Add a third investigation case with PCAP artifact in-repo

---

## Ethical Use
This tool is intended strictly for defensive security research, SOC analyst training, 
and educational purposes in controlled lab environments.

Do not use this tool against systems you do not own or have explicit written permission 
to analyze. The author assumes no responsibility for misuse.

---
