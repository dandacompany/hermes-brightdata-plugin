from __future__ import annotations

from . import datasets
from .tools import SEARCH_ENGINE_URLS

TOOL_SCHEMAS: dict[str, dict] = {
    "search_engine": {
        "name": "search_engine",
        "description": (
            "Search the web via Bright Data SERP API and return parsed results. "
            "Use for current events, fact-checking, finding pages, or any web search. "
            "Bypasses bot detection; more reliable than built-in web search."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query text."},
                "engine": {"type": "string", "enum": sorted(SEARCH_ENGINE_URLS),
                           "description": "Search engine to use. Default google."},
            },
            "required": ["query"],
        },
    },
    "scrape": {
        "name": "scrape",
        "description": (
            "Fetch a single URL as clean markdown (or html) using Bright Data Web "
            "Unlocker. Handles JavaScript, CAPTCHAs, and bot detection. Use to read "
            "any webpage, article, doc, or site."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Absolute URL incl. protocol."},
                "format": {"type": "string", "enum": ["markdown", "html"],
                           "description": "Output format. Default markdown."},
            },
            "required": ["url"],
        },
    },
    "scrape_batch": {
        "name": "scrape_batch",
        "description": (
            "Scrape multiple URLs in one call (max 20). Returns per-URL content or "
            "error. Use when you have several pages to read at once."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "urls": {"type": "array", "items": {"type": "string"},
                         "description": "List of absolute URLs (max 20)."},
                "format": {"type": "string", "enum": ["markdown", "html"],
                           "description": "Output format. Default markdown."},
            },
            "required": ["urls"],
        },
    },
    "web_data": {
        "name": "web_data",
        "description": (
            "Get structured JSON data from a supported platform via Bright Data "
            "Web Scraper API (e.g. an Amazon product page, a LinkedIn profile). "
            "Returns clean structured fields, not raw HTML. May take up to a minute."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "enum": datasets.platforms(),
                             "description": "Which structured dataset to use."},
                "url": {"type": "string", "description": "Target page URL."},
            },
            "required": ["platform", "url"],
        },
    },
    "proxy_scrape": {
        "name": "proxy_scrape",
        "description": (
            "Fetch a URL through a Bright Data residential proxy, optionally from a "
            "specific country. Use for geo-targeted content (region-specific pricing, "
            "localized pages). Returns the raw response. Requires BRIGHTDATA_PROXY_AUTH; "
            "for HTTPS, set BRIGHTDATA_PROXY_CA to the Bright Data proxy CA cert path."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Absolute URL to fetch."},
                "country": {"type": "string",
                            "description": "2-letter ISO country code (e.g. 'us', 'gb'). Optional."},
            },
            "required": ["url"],
        },
    },
    "session_stats": {
        "name": "session_stats",
        "description": "Report Bright Data tool call counts for this session.",
        "parameters": {"type": "object", "properties": {}},
    },
    "brightdata_browser_navigate": {
        "name": "brightdata_browser_navigate",
        "description": (
            "Open a URL in a Bright Data Scraping Browser (real browser with a "
            "persistent session). Use for interactive flows requiring clicks/typing. "
            "Requires the [browser] extra and BRIGHTDATA_BROWSER_AUTH."
        ),
        "parameters": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "URL to open."}},
            "required": ["url"],
        },
    },
    "brightdata_browser_snapshot": {
        "name": "brightdata_browser_snapshot",
        "description": (
            "Return an ARIA snapshot (accessibility tree) of the current browser page "
            "for reading its structure and content. Use CSS/text selectors with "
            "brightdata_browser_act to interact."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
    "brightdata_browser_act": {
        "name": "brightdata_browser_act",
        "description": (
            "Perform an action on the current browser page: click, type, scroll, or "
            "wait. Target click/type with a CSS or text selector (e.g. 'text=Login')."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["click", "type", "scroll", "wait"]},
                "ref": {"type": "string",
                        "description": "CSS or text selector, e.g. '#submit' or 'text=Login' (click/type)."},
                "value": {"type": "string",
                          "description": "Text to type (type), scroll delta in px (scroll), or wait ms (wait)."},
            },
            "required": ["action"],
        },
    },
    "brightdata_browser_get": {
        "name": "brightdata_browser_get",
        "description": (
            "Read the current browser page: html, text, or a base64 screenshot."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": ["html", "text", "screenshot"],
                         "description": "What to return. Default text."},
            },
        },
    },
}
