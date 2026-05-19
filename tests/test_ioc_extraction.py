from extractors.ioc_extractor import extract_iocs


def test_extracts_ip_addresses():
    text = "Observed callbacks to 185.243.115.84 and 10.0.0.5."
    results = extract_iocs(text)

    assert "185.243.115.84" in results.ips
    assert "10.0.0.5" in results.ips


def test_extracts_domains_with_normalization():
    text = "C2 domains: Evil-Malware.com. and hacker-control.net"
    results = extract_iocs(text)

    assert "evil-malware.com" in results.domains
    assert "hacker-control.net" in results.domains


def test_extracts_urls_and_trims_trailing_punctuation():
    text = "Payload URL observed: https://evil-malware.com/dropper)."
    results = extract_iocs(text)

    assert "https://evil-malware.com/dropper" in results.urls


def test_iocresults_backward_compatible_access():
    text = "http://evil-malware.com connected to 185.243.115.84"
    results = extract_iocs(text)

    assert isinstance(results["ips"], list)
    assert "185.243.115.84" in results["ips"]
    assert "evil-malware.com" in results.get("domains", [])
    assert results.get("missing", ["fallback"]) == ["fallback"]
