from __future__ import annotations

import asyncio
import socket
from collections.abc import Awaitable, Callable
from ipaddress import ip_address
from urllib.parse import urlsplit

_BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "instance-data.ec2.internal",
}
_BLOCKED_HOSTNAME_SUFFIXES = (
    ".localhost",
    ".local",
    ".localdomain",
    ".internal",
    ".home.arpa",
)

HostResolver = Callable[[str], Awaitable[set[str]]]


def ensure_public_http_url(url: str) -> None:
    """Reject obvious local/private HTTP(S) targets before browser network access."""
    parsed = urlsplit(url)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("Browser navigation only allows HTTP or HTTPS URLs")

    hostname = (parsed.hostname or "").lower().rstrip(".")
    if not hostname:
        raise ValueError("Browser navigation URL has no hostname")
    if hostname in _BLOCKED_HOSTNAMES or hostname.endswith(_BLOCKED_HOSTNAME_SUFFIXES):
        raise ValueError(f"Browser navigation target is blocked: {hostname}")

    try:
        address = ip_address(hostname)
    except ValueError:
        return

    if not address.is_global:
        raise ValueError(f"Browser navigation target is not public: {hostname}")


async def ensure_public_http_url_resolved(
    url: str,
    *,
    resolver: HostResolver | None = None,
) -> None:
    """Also reject hostnames whose current DNS answers contain non-public addresses."""
    ensure_public_http_url(url)
    hostname = (urlsplit(url).hostname or "").lower().rstrip(".")

    try:
        ip_address(hostname)
    except ValueError:
        pass
    else:
        return

    addresses = await (resolver or _resolve_hostname)(hostname)
    if not addresses:
        raise ValueError(f"Browser navigation target did not resolve: {hostname}")

    for raw_address in addresses:
        try:
            address = ip_address(raw_address)
        except ValueError as exc:
            raise ValueError(
                f"Browser navigation target resolved to an invalid address: {raw_address}"
            ) from exc
        if not address.is_global:
            raise ValueError(
                f"Browser navigation target resolved to a non-public address: {hostname} -> {address}"
            )


def is_blocked_http_url(url: str) -> bool:
    parsed = urlsplit(url)
    if parsed.scheme.lower() not in {"http", "https"}:
        return False
    try:
        ensure_public_http_url(url)
    except ValueError:
        return True
    return False


async def _resolve_hostname(hostname: str) -> set[str]:
    loop = asyncio.get_running_loop()
    infos = await loop.getaddrinfo(
        hostname,
        None,
        family=socket.AF_UNSPEC,
        type=socket.SOCK_STREAM,
    )
    return {str(sockaddr[0]) for *_, sockaddr in infos}
