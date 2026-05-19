import sys
from extractors.ioc_extractor import extract_iocs

def normalize_results(results):
    """Support both IOCResults and legacy dict payloads."""
    if hasattr(results, "to_sorted_dict"):
        return results.to_sorted_dict()
    return results
def run_demo() -> None:
    sample_text = """
Connection to malicious domain:

http://evil-malware.com

Suspicious IP:
185.243.115.84

Another domain:
hacker-control.net
"""

    results = extract_iocs(sample_text)
    results_dict = normalize_results(results)

    print("\nIOC RESULTS\n")
    print("IPs:")
    print(results_dict["ips"])
    print("\nDomains:")
    print(results_dict["domains"])
    print("\nURLs:")
    print(results_dict["urls"])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        from mysnull_cli import main as cli_main

        raise SystemExit(cli_main())
    run_demo()
