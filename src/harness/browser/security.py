from __future__ import annotations

from ipaddress import ip_address
from urllib.parse import urlsplit

_BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
}


def ensure_public_http_url(url: str) -> None:
    """Reject obvious local/private HTTP(S) targets before browser network access."""
    parsed = urlsplit(url)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("Browser navigation only allows HTTP or HTTPS URLs")

    hostname = (parsed.hostname or "").lower().rstrip(".")
    if not hostname:
        raise ValueError("Browser navigation URL has no hostname")
    if hostname in _BLOCKED_HOSTNAMES or hostname.endswith(".localhost"):
        raise ValueError(f"Browser navigation target is blocked: {hostname}")

    try:
        address = ip_address(hostname)
    except ValueError:
        return

    if not address.is_global:
        raise ValueError(f"Browser navigation target is not public: {hostname}")


def is_blocked_http_url(url: str) -> bool:
    parsed = urlsplit(url)
    if parsed.scheme.lower() not in {"http", "https"}:
        return False
    try:
        ensure_public_http_url(url)
    except ValueError:
        return True
    return False
