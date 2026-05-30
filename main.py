import sys
from pathlib import Path

from extractors.ioc_extractor import extract_iocs

DEFAULT_SAMPLE = Path(__file__).parent / "samples" / "xloader_traffic_notes.txt"


def normalize_results(results):
    """Support both IOCResults and legacy dict payloads."""
    if hasattr(results, "to_sorted_dict"):
        return results.to_sorted_dict()
    return results


def run_demo() -> None:
    sample_path = DEFAULT_SAMPLE
    if not sample_path.is_file():
        print(f"Demo sample not found: {sample_path}")
        raise SystemExit(1)

    sample_text = sample_path.read_text(encoding="utf-8")
    results = extract_iocs(sample_text)
    results_dict = normalize_results(results)

    print("\nIOC RESULTS\n")
    print("IPs:")
    print(results_dict["ips"])
    print("\nDomains:")
    print(results_dict["domains"])
    print("\nURLs:")
    print(results_dict["urls"])
    print("\nHashes:")
    print(results_dict["hashes"])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        from mysnull_cli import main as cli_main

        raise SystemExit(cli_main())
    run_demo()
