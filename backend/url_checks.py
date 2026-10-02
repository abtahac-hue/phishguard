import ipaddress
import re
from urllib.parse import urlsplit


SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd"
}


def analyze_urls(text: str) -> list[dict]:
    findings = []
    seen_rules = set()

    def add_finding(rule_id, url, points, explanation):
        # Count each warning type once per analysis.
        if rule_id not in seen_rules:
            seen_rules.add(rule_id)
            findings.append({
                "id": rule_id,
                "matched_text": url,
                "points": points,
                "explanation": explanation,
            })

    urls = re.findall(
        r"""(?:https?://|www\.)[^\s<>"']+""",
        text,
        flags=re.IGNORECASE,
    )

    for raw_url in urls:
        url = raw_url.rstrip(".,;!?)")
        normalized = (
            "https://" + url
            if url.lower().startswith("www.")
            else url
        )

        try:
            parsed = urlsplit(normalized)
            host = (parsed.hostname or "").lower().rstrip(".")
            if not host:
                raise ValueError("Missing hostname")
            # Accessing port also checks for invalid port values.
            parsed.port
        except ValueError:
            add_finding(
                "malformed_url", url, 10,
                "The link could not be parsed correctly. Verify it independently.",
            )
            continue

        if parsed.scheme.lower() == "http":
            add_finding(
                "unencrypted_link", url, 5,
                "This link uses HTTP. The connection is not encrypted; "
                "this alone does not prove phishing.",
            )

        if host in SHORTENERS:
            add_finding(
                "shortened_url", url, 10,
                "This shortened link hides the final destination.",
            )

        if parsed.username is not None:
            add_finding(
                "url_userinfo", url, 20,
                "Text before @ can disguise the destination. "
                f"The actual hostname is {host}.",
            )

        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            add_finding(
                "ip_address_url", url, 15,
                "This link uses an IP address instead of a domain name. "
                "It may be legitimate, but needs closer review.",
            )

        if any(label.startswith("xn--") for label in host.split(".")):
            add_finding(
                "internationalized_domain", url, 10,
                "This domain uses an internationalized encoding. "
                "Check its spelling carefully; legitimate domains use this too.",
            )

    return findings
    