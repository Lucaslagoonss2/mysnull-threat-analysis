from extractors.ioc_extractor import defang_iocs, extract_iocs


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


def test_extracts_md5_hash():
    text = "Dropped file MD5: 44d88612fea8a8f36de82e1278abb02f"
    results = extract_iocs(text)

    assert "44d88612fea8a8f36de82e1278abb02f" in results.hashes


def test_extracts_sha256_hash():
    text = (
        "Sample SHA256: "
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    results = extract_iocs(text)

    assert "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" in results.hashes


def test_defang_output():
    text = "Host 76.223.54.146 used https://www.evil.com/drop and www.evil.com"
    results = extract_iocs(text)
    defanged = defang_iocs(results)

    assert "76[.]223[.]54[.]146" in defanged.ips
    assert "www[.]evil[.]com" in defanged.domains
    assert "https[://]www[.]evil[.]com/drop" in defanged.urls
