from __future__ import annotations

import json
from urllib.parse import quote_plus

from . import datasets
from .api import BrightDataError
from .browser import BrowserUnavailable

MAX_BATCH = 20

SEARCH_ENGINE_URLS = {
    "google": "https://www.google.com/search?q={q}",
    "bing": "https://www.bing.com/search?q={q}",
    "yandex": "https://yandex.com/search/?text={q}",
    "duckduckgo": "https://duckduckgo.com/?q={q}",
}


def normalize_json_strings(value):
    """Decode JSON objects/arrays embedded as response strings recursively.

    Bright Data can return an already-JSON payload wrapped one or more times as
    a string.  Keep ordinary text untouched so callers never lose page content.
    """
    if isinstance(value, str):
        candidate = value.strip()
        if candidate[:1] in ("{", "["):
            try:
                return normalize_json_strings(json.loads(candidate))
            except json.JSONDecodeError:
                pass
        return value
    if isinstance(value, list):
        return [normalize_json_strings(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize_json_strings(item) for key, item in value.items()}
    return value


def _err(message: str, hint: str = "") -> str:
    payload = {"error": message}
    if hint:
        payload["hint"] = hint
    return json.dumps(payload, ensure_ascii=False)


def _ok(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False)


def make_core_handlers(get_client, counter) -> dict:
    def search_engine(args: dict, **kwargs) -> str:
        try:
            query = args.get("query")
            if not query:
                return _err("'query' is required")
            engine = args.get("engine", "google").lower()
            template = SEARCH_ENGINE_URLS.get(engine)
            if template is None:
                return _err(f"unknown engine '{engine}'",
                            f"choose one of {sorted(SEARCH_ENGINE_URLS)}")
            url = template.format(q=quote_plus(query))
            results = normalize_json_strings(get_client().serp(url))
            counter.record("search_engine")
            return _ok({"engine": engine, "results": results})
        except BrightDataError as e:
            return _err(str(e), e.hint)
        except Exception as e:  # noqa: BLE001
            return _err(f"unexpected error: {e}")

    def scrape(args: dict, **kwargs) -> str:
        try:
            url = args.get("url")
            if not url:
                return _err("'url' is required")
            fmt = args.get("format", "markdown")
            content = get_client().unlock(url, data_format=fmt)
            counter.record("scrape")
            return _ok({"url": url, "format": fmt, "content": content})
        except BrightDataError as e:
            return _err(str(e), e.hint)
        except Exception as e:  # noqa: BLE001
            return _err(f"unexpected error: {e}")

    def scrape_batch(args: dict, **kwargs) -> str:
        try:
            urls = args.get("urls")
            if not urls or not isinstance(urls, list):
                return _err("'urls' must be a non-empty list")
            if len(urls) > MAX_BATCH:
                return _err(f"too many urls (max {MAX_BATCH})")
            fmt = args.get("format", "markdown")
            client = get_client()
            results = []
            for u in urls:
                try:
                    content = client.unlock(u, data_format=fmt)
                    counter.record("scrape_batch")
                    results.append({"url": u, "content": content})
                except BrightDataError as e:
                    results.append({"url": u, "error": str(e), "hint": e.hint})
                except Exception as e:  # noqa: BLE001 — isolate per-URL failure
                    results.append({"url": u, "error": f"unexpected error: {e}"})
            return _ok({"results": results})
        except Exception as e:  # noqa: BLE001
            return _err(f"unexpected error: {e}")

    def web_data(args: dict, **kwargs) -> str:
        try:
            platform = args.get("platform")
            url = args.get("url")
            if not platform or not url:
                return _err("'platform' and 'url' are required")
            try:
                dataset_id = datasets.resolve(platform)
            except datasets.UnknownPlatform as e:
                return _err(str(e), f"available: {e.available}")
            result = normalize_json_strings(get_client().collect_dataset(dataset_id, [url]))
            counter.record("web_data")
            return _ok(result)
        except BrightDataError as e:
            return _err(str(e), e.hint)
        except Exception as e:  # noqa: BLE001
            return _err(f"unexpected error: {e}")

    def proxy_scrape(args: dict, **kwargs) -> str:
        try:
            url = args.get("url")
            if not url:
                return _err("'url' is required")
            country = args.get("country")
            content = get_client().proxy_scrape(url, country=country)
            counter.record("proxy_scrape")
            return _ok({"url": url, "country": country, "content": content})
        except BrightDataError as e:
            return _err(str(e), e.hint)
        except Exception as e:  # noqa: BLE001
            return _err(f"unexpected error: {e}")

    def session_stats(args: dict, **kwargs) -> str:
        try:
            return _ok(counter.stats())
        except Exception as e:  # noqa: BLE001
            return _err(f"unexpected error: {e}")

    return {
        "search_engine": search_engine,
        "scrape": scrape,
        "scrape_batch": scrape_batch,
        "web_data": web_data,
        "proxy_scrape": proxy_scrape,
        "session_stats": session_stats,
    }


def make_browser_handlers(get_session, counter) -> dict:
    def _run(tool_name, fn):
        def handler(args: dict, **kwargs) -> str:
            try:
                session = get_session()
            except BrowserUnavailable as e:
                hint = f"{str(e)} - {e.hint}" if e.hint else str(e)
                return _err(str(e), hint)
            except Exception as e:  # noqa: BLE001
                return _err(f"unexpected error: {e}")
            try:
                result = fn(session, args)
                counter.record(tool_name)
                return _ok(result)
            except BrowserUnavailable as e:
                hint = f"{str(e)} - {e.hint}" if e.hint else str(e)
                return _err(str(e), hint)
            except ValueError as e:
                return _err(str(e))
            except Exception as e:  # noqa: BLE001
                return _err(f"unexpected error: {e}")
        return handler

    def _navigate(session, args):
        url = args.get("url")
        if not url:
            raise ValueError("'url' is required")
        return session.navigate(url)

    def _snapshot(session, args):
        return session.snapshot()

    def _act(session, args):
        action = args.get("action")
        if not action:
            raise ValueError("'action' is required")
        return session.act(action, ref=args.get("ref"), value=args.get("value"))

    def _get(session, args):
        kind = args.get("kind", "text")
        return session.get(kind)

    return {
        "brightdata_browser_navigate": _run("brightdata_browser_navigate", _navigate),
        "brightdata_browser_snapshot": _run("brightdata_browser_snapshot", _snapshot),
        "brightdata_browser_act": _run("brightdata_browser_act", _act),
        "brightdata_browser_get": _run("brightdata_browser_get", _get),
    }
