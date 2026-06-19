"""
search_tools.py — Free search APIs used by the research node.

Same pattern proven in multi-tool-agent:
  1. Try Wikipedia search + extract (most reliable, no key needed)
  2. Fall back to DuckDuckGo Instant Answer API
"""

import json
import re
import ssl
import urllib.parse
import urllib.request
from dataclasses import dataclass


def _ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


@dataclass
class SearchResult:
    query: str
    source: str       # "wikipedia" | "duckduckgo" | "none"
    title: str
    content: str


def search_wikipedia(query: str) -> SearchResult | None:
    """Search Wikipedia and return the top article's intro extract."""
    ctx = _ssl_ctx()
    encoded = urllib.parse.quote_plus(query)

    try:
        search_url = (
            "https://en.wikipedia.org/w/api.php"
            f"?action=query&list=search&srsearch={encoded}&format=json&srlimit=1"
        )
        req = urllib.request.Request(
            search_url,
            headers={"User-Agent": "research-agent-langgraph/1.0 (educational)"}
        )
        with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
            data = json.loads(resp.read().decode())

        hits = data.get("query", {}).get("search", [])
        if not hits:
            return None

        title = hits[0]["title"]
        title_enc = urllib.parse.quote_plus(title)
        extract_url = (
            "https://en.wikipedia.org/w/api.php"
            f"?action=query&prop=extracts&exintro=true&explaintext=true"
            f"&titles={title_enc}&format=json"
        )
        req2 = urllib.request.Request(
            extract_url,
            headers={"User-Agent": "research-agent-langgraph/1.0"}
        )
        with urllib.request.urlopen(req2, timeout=8, context=ctx) as resp2:
            edata = json.loads(resp2.read().decode())

        pages = edata.get("query", {}).get("pages", {})
        for page in pages.values():
            extract = page.get("extract", "")
            if extract:
                return SearchResult(
                    query=query,
                    source="wikipedia",
                    title=title,
                    content=extract[:800].strip(),
                )
        return None

    except Exception:
        return None


def search_duckduckgo(query: str) -> SearchResult | None:
    """Fallback search using DuckDuckGo Instant Answer API."""
    ctx = _ssl_ctx()
    encoded = urllib.parse.quote_plus(query)

    try:
        url = (
            f"https://api.duckduckgo.com/?q={encoded}"
            "&format=json&no_redirect=1&no_html=1"
        )
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        )
        with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
            data = json.loads(resp.read().decode())

        text = data.get("AbstractText", "")
        if text:
            return SearchResult(
                query=query,
                source="duckduckgo",
                title=data.get("Heading", query),
                content=text,
            )

        topics = data.get("RelatedTopics", [])
        snippets = [t["Text"] for t in topics[:2] if isinstance(t, dict) and t.get("Text")]
        if snippets:
            return SearchResult(
                query=query,
                source="duckduckgo",
                title=query,
                content="\n".join(snippets),
            )
        return None

    except Exception:
        return None


def search(query: str) -> SearchResult:
    """Try Wikipedia first, then DuckDuckGo. Always returns a SearchResult."""
    result = search_wikipedia(query)
    if result:
        return result

    result = search_duckduckgo(query)
    if result:
        return result

    return SearchResult(query=query, source="none", title=query, content="")