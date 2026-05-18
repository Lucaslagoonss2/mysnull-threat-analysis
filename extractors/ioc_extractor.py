import re
from urllib.parse import urlparse


IP_PATTERN = re.compile(
    r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
)

DOMAIN_PATTERN = re.compile(
    r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b"
)

URL_PATTERN = re.compile(
    r"https?://[^\s]+"
)


def extract_iocs(text):

    ips = set(
        IP_PATTERN.findall(text)
    )

    urls = set(
        URL_PATTERN.findall(text)
    )

    domains = set(
        DOMAIN_PATTERN.findall(text)
    )

    for url in urls:

        parsed = urlparse(url)

        if parsed.hostname:
            domains.add(
                parsed.hostname
            )

    return {
        "ips": list(ips),
        "domains": list(domains),
        "urls": list(urls)
    }
