from extractors.ioc_extractor import extract_iocs


sample_text = """
Connection to malicious domain:

http://evil-malware.com

Suspicious IP:
185.243.115.84

Another domain:
hacker-control.net
"""


results = extract_iocs(sample_text)

print("\nIOC RESULTS\n")

print("IPs:")
print(results["ips"])

print("\nDomains:")
print(results["domains"])

print("\nURLs:")
print(results["urls"])
