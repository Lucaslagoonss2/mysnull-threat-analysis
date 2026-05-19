# MysNull Threat Analysis
Blue Team portfolio project focused on SOC-style malware traffic investigation and IOC extraction.  
This repository is intentionally practical and learning-oriented, with clear evidence artifacts, reproducible scripts, and analyst-friendly output.

## Project overview
`mysnull-threat-analysis` documents an end-to-end mini investigation workflow:
- review suspicious traffic evidence
- identify and document indicators of compromise (IOCs)
- produce structured outputs for triage and reporting

Current scope is junior-friendly and realistic: one investigation case, reproducible extraction tooling, and clear room for iterative improvement.

## Features
- IOC extraction from text/log inputs (IPv4, domains, URLs)
- Rich-powered cyberpunk SOC terminal UI for extraction runs
- JSON and TXT artifact export
- Investigation evidence folders (reports, screenshots, IOCs)
- Portfolio-friendly project organization

## Investigation workflow
1. Collect or review suspicious traffic artifacts (PCAP/snapshots/report notes)
2. Analyze traffic behavior (DNS, HTTP, TCP patterns)
3. Extract candidate indicators (IPs, domains, URLs)
4. Validate and normalize IOCs
5. Export structured IOC artifacts
6. Document findings for SOC-style reporting

## IOC extraction capabilities
The IOC extractor (`extractors/ioc_extractor.py`) currently supports:
- regex-based extraction of:
  - IPv4 addresses
  - domains
  - HTTP/HTTPS URLs
- URL/domain normalization
- sorted/structured output via `IOCResults`
- output formats:
  - `.txt` report
  - `.json` structured artifact
- terminal UX features:
  - animated startup (optional)
  - summary panels
  - export/log visibility
- run logging to file for troubleshooting

## Quickstart
```bash
# 1) (optional) create virtual environment
python -m venv .venv

# 2) activate it (PowerShell)
.\.venv\Scripts\Activate.ps1

# 3) install dependency used by the extractor UI
pip install rich

# 4) run quick demo script
python main.py
```

## Installation
### Requirements
- Python 3.10+ (recommended)
- `pip`

### Install
```bash
pip install rich
```

## Example commands
```bash
# Run extractor against sample data (fast mode, no animation)
python extractors/ioc_extractor.py -i samples/test.txt --no-animation

# Export both formats into a target folder
python extractors/ioc_extractor.py -i samples/test.txt -f txt json -o outputs --basename xloader_iocs --no-animation

# Enable verbose logging
python extractors/ioc_extractor.py -i samples/test.txt --verbose --no-animation
```

## Sample output
Example from `main.py`:
```text
IOC RESULTS

IPs:
['185.243.115.84']

Domains:
['evil-malware.com', 'hacker-control.net']

URLs:
['http://evil-malware.com']
```

Extractor exports artifacts such as:
- `ioc_results.txt`
- `ioc_results.json`
- `ioc_extractor.log`

## Screenshots
### Suspicious DNS Resolution
![DNS Investigation](screenshots/suspicious_dns.png)

### External TCP Communication
![TCP Communication](screenshots/tcp_communication_with_suspicious_ip.png)

### HTTP Stream Analysis
![HTTP Stream](screenshots/follow_http_stream_analysis.png)

## Skills demonstrated
- IOC extraction and normalization
- Malware traffic triage fundamentals (DNS/HTTP/TCP)
- SOC-style investigation documentation
- Python scripting for analyst workflows
- Structured artifact generation for repeatability

## Accurate project tree
```text
mysnull-threat-analysis/
├── core/
│   └── README.md
├── exporters/
│   └── README.md
├── extractors/
│   ├── README.md
│   ├── ioc_extractor.py
│   └── rich_render.py
├── iocs/
│   ├── README.md
│   └── xloader-iocs.md
├── pcap/
│   └── README.md
├── reports/
│   ├── README.md
│   └── xloader-analysis-report.md
├── samples/
│   ├── README.md
│   └── test.txt
├── screenshots/
│   ├── README.md
│   ├── follow_http_stream_analysis.png
│   ├── suspicious_dns.png
│   └── tcp_communication_with_suspicious_ip.png
├── tests/
│   └── README.md
├── ui/
│   └── README.md
├── .gitignore
├── LICENSE
├── main.py
└── README.md
```

## Future roadmap
- Add unit tests for IOC parsing edge cases
- Add hash/email/path IOC types
- Add pcap-to-text preprocessing helpers
- Add markdown report generation templates
- Add confidence/false-positive tuning notes

---
Status: in progress, actively refactoring for cleaner modularity and stronger portfolio presentation.
