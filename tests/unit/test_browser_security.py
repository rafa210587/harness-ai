import pytest

from harness.browser.security import ensure_public_http_url, ensure_public_http_url_resolved


def test_browser_url_guard_blocks_obvious_local_targets() -> None:
    blocked = [
        "http://localhost/",
        "http://api.local/",
        "http://service.internal/",
        "http://127.0.0.1/",
        "http://10.0.0.1/",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/",
    ]

    for url in blocked:
        with pytest.raises(ValueError):
            ensure_public_http_url(url)


def test_browser_url_guard_allows_public_literal_address() -> None:
    ensure_public_http_url("https://8.8.8.8/")


async def test_resolved_guard_blocks_hostname_resolving_private_address() -> None:
    async def resolver(_hostname: str) -> set[str]:
        return {"10.10.0.12"}

    with pytest.raises(ValueError, match="non-public address"):
        await ensure_public_http_url_resolved("https://example.com/", resolver=resolver)


async def test_resolved_guard_blocks_mixed_public_and_private_answers() -> None:
    async def resolver(_hostname: str) -> set[str]:
        return {"93.184.216.34", "192.168.1.10"}

    with pytest.raises(ValueError, match="non-public address"):
        await ensure_public_http_url_resolved("https://example.com/", resolver=resolver)


async def test_resolved_guard_allows_public_dns_answers() -> None:
    async def resolver(_hostname: str) -> set[str]:
        return {"93.184.216.34", "2606:2800:220:1:248:1893:25c8:1946"}

    await ensure_public_http_url_resolved("https://example.com/", resolver=resolver)


async def test_resolved_guard_rejects_empty_dns_answers() -> None:
    async def resolver(_hostname: str) -> set[str]:
        return set()

    with pytest.raises(ValueError, match="did not resolve"):
        await ensure_public_http_url_resolved("https://example.com/", resolver=resolver)
