# MysNull Threat Analysis
Practical junior Blue Team SOC portfolio project focused on malware-traffic investigation and IOC extraction.
This repo highlights repeatable analyst workflow, evidence artifacts, and clean Python tooling with a light cyberpunk terminal style.

## Recruiter snapshot
- Scope: one realistic investigation case (not an enterprise platform)
- Focus: DNS/HTTP/TCP triage and IOC extraction
- Output: reproducible `.txt` / `.json` artifacts for reporting and handoff

## What this project does
- Extracts IPv4s, domains, and URLs from text-based evidence
- Normalizes and structures IOC results for analyst use
- Exports findings to `txt` and `json`
- Provides Rich-powered SOC-style CLI output

## Quickstart
### Requirements
- Python 3.10+
- `pip`

### Install
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install rich
```

### Run demo
```bash
python main.py
```

## Example commands
```bash
# Basic extraction (fast mode)
python extractors/ioc_extractor.py -i samples/test.txt --no-animation

# Export both formats to a folder
python extractors/ioc_extractor.py -i samples/test.txt -f txt json -o outputs --basename xloader_iocs --no-animation

# Verbose run for troubleshooting
python extractors/ioc_extractor.py -i samples/test.txt --verbose --no-animation
```

## Investigation workflow
1. Review suspicious evidence (traffic notes / packet-derived text)
2. Triage behavior across DNS, HTTP, and TCP signals
3. Extract candidate IOCs (IPs, domains, URLs)
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

## Skills demonstrated
- IOC extraction and normalization fundamentals
- SOC-style malware traffic triage (DNS/HTTP/TCP)
- Investigation documentation and evidence handling
- Python scripting for repeatable analyst workflows

## Future roadmap
- Add unit tests for IOC parsing edge cases
- Extend IOC support (hashes, emails, file paths)
- Add preprocessing helpers for packet-derived text inputs
- Add reporting templates for faster case writeups
