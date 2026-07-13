"""Bright Data implementation of Hermes' normalized web-search provider contract.

The Hermes core owns the provider registry. Provider-aware Hermes releases
expose ``agent.web_search_provider.WebSearchProvider``; older releases receive
a compatible local base class so the standalone tools keep working.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable
from urllib.parse import quote_plus

from .api import BrightDataError, BrightDataClient
from .tools import normalize_json_strings


try:  # Hermes' provider ABC is available only on provider-aware releases.
    from agent.web_search_provider import WebSearchProvider
except ImportError:
    class WebSearchProvider(ABC):
        """Compatibility copy of the Hermes web-search provider contract."""

        @property
        @abstractmethod
        def name(self) -> str:
            pass

        @abstractmethod
        def is_available(self) -> bool:
            pass

        @abstractmethod
        def search(self, query: str, limit: int = 5) -> dict[str, Any]:
            pass


class BrightDataWebSearchProvider(WebSearchProvider):
    """Search through Bright Data and return Hermes' normalized ``data.web`` shape."""

    def __init__(self, get_client: Callable[[], BrightDataClient], configured: bool = True):
        self._get_client = get_client
        self._configured = configured

    @property
    def name(self) -> str:
        return "brightdata"

    @property
    def display_name(self) -> str:
        return "Bright Data"

    def is_available(self) -> bool:
        """Return the already-validated plugin configuration state."""
        return self._configured

    def get_setup_schema(self) -> dict[str, Any]:
        """Describe Bright Data for Hermes' interactive provider picker."""
        return {
            "name": self.display_name,
            "badge": "paid",
            "tag": "SERP search through Bright Data's Web Unlocker API.",
            "env_vars": [
                {
                    "key": "BRIGHTDATA_API_TOKEN",
                    "prompt": "Bright Data API token",
                    "url": "https://brightdata.com/cp/zones",
                },
            ],
        }

    def search(self, query: str, limit: int = 5) -> dict[str, Any]:
        if not isinstance(query, str) or not query.strip():
            return {"success": False, "error": "search query is required"}
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            return {"success": False, "error": "limit must be a positive integer"}

        url = f"https://www.google.com/search?q={quote_plus(query)}"
        try:
            payload = normalize_json_strings(self._get_client().serp(url))
        except BrightDataError as e:
            return {"success": False, "error": str(e), "hint": e.hint}
        except Exception:  # noqa: BLE001 — provider contract returns failure payloads
            return {
                "success": False,
                "error": "Bright Data search failed unexpectedly",
                "hint": "retry the search; check Bright Data configuration and network connectivity.",
            }

        raw_results = _organic_results(payload)
        if raw_results is None:
            return {
                "success": False,
                "error": "Bright Data search response did not contain organic results",
                "hint": "retry the search; the selected SERP zone may not return JSON results.",
            }

        web = []
        for index, item in enumerate(raw_results[:limit], start=1):
            if not isinstance(item, dict):
                continue
            web.append({
                "title": str(item.get("title", "")),
                "url": str(item.get("url") or item.get("link") or item.get("dest_url") or ""),
                "description": str(item.get("description") or item.get("snippet") or item.get("content") or ""),
                "position": item.get("position") or item.get("rank") or index,
            })
        return {"success": True, "data": {"web": web}}


def _organic_results(payload: Any) -> list[Any] | None:
    """Find the common Bright Data organic-result arrays after normalization."""
    if not isinstance(payload, dict):
        return None
    for key in ("organic", "organic_results", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return None
