from __future__ import annotations

import os
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

import httpx

DEFAULT_MAX_CHARS = 20000


class _HTMLTextExtractor(HTMLParser):
    """Extract readable text from HTML, excluding scripts and styles."""

    def __init__(self) -> None:
        super().__init__()
        self._text_parts: list[str] = []
        self._skip_tag = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "head", "meta", "link"}:
            self._skip_tag = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "head", "meta", "link"}:
            self._skip_tag = False
        elif tag.lower() in {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "br"}:
            self._text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_tag:
            stripped = data.strip()
            if stripped:
                self._text_parts.append(stripped)

    def get_text(self) -> str:
        return " ".join(self._text_parts)


def web_fetch(args: dict[str, Any]) -> str:
    url = str(args.get("url", "")).strip()
    if not url:
        return "web_fetch error: url is required."
    if not _is_safe_url(url):
        return "web_fetch error: url not allowed."
    max_chars_raw = args.get("max_chars", DEFAULT_MAX_CHARS)
    try:
        max_chars = int(max_chars_raw)
    except Exception:
        max_chars = DEFAULT_MAX_CHARS
    max_chars = max(200, min(200000, max_chars))

    # Support custom headers (e.g. for API tokens)
    custom_headers = args.get("headers")
    if not isinstance(custom_headers, dict):
        custom_headers = {}

    # Try Firecrawl first if configured
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
    if firecrawl_key:
        try:
            return _fetch_firecrawl(url, firecrawl_key, max_chars, custom_headers)
        except Exception:
            # Fall back to basic fetch if Firecrawl fails
            pass

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; BroodMind/1.0)",
        "Accept-Language": "en-US,en;q=0.9",
    }
    # Merge custom headers
    if custom_headers:
        headers.update(custom_headers)

    try:
        with httpx.Client(timeout=20.0, headers=headers) as client:
            resp = client.get(url)
        content = resp.text
        # Extract readable text if HTML
        content_type = (resp.headers.get("content-type") or "").lower()
        if "text/html" in content_type:
            extractor = _HTMLTextExtractor()
            try:
                extractor.feed(content)
                text = extractor.get_text()
            except Exception:
                text = content  # Fall back to raw content if parsing fails
        else:
            text = content
        snippet = text[:max_chars]
        payload = {
            "url": url,
            "status_code": resp.status_code,
            "content_type": resp.headers.get("content-type"),
            "snippet": snippet,
        }
        return _to_json(payload)
    except Exception as exc:
        return f"web_fetch error: {exc}"


def _fetch_firecrawl(url: str, api_key: str, max_chars: int, target_headers: dict[str, Any] | None = None) -> str:
    """Fetch content using Firecrawl API."""
    endpoint = "https://api.firecrawl.dev/v1/scrape"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": True,
        "timeout": 30000,
    }
    if target_headers:
        payload["headers"] = target_headers

    with httpx.Client(timeout=40.0) as client:
        resp = client.post(endpoint, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    if not data.get("success"):
        raise ValueError(f"Firecrawl failed: {data.get('error')}")

    markdown = data.get("data", {}).get("markdown", "")
    snippet = markdown[:max_chars]

    result = {
        "url": url,
        "status_code": 200,
        "content_type": "text/markdown",
        "snippet": snippet,
        "source": "firecrawl",
    }
    return _to_json(result)


def _is_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    if parsed.scheme not in {"http", "https"}:
        return False
    host = (parsed.hostname or "").lower()
    return host not in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}


def _to_json(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False)
