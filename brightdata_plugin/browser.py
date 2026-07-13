from __future__ import annotations

import base64

from .config import Config

CDP_HOST = "brd.superproxy.io:9222"


class BrowserUnavailable(Exception):
    def __init__(self, message: str, hint: str = ""):
        super().__init__(message)
        self.hint = hint


def _default_connector(cfg: Config):
    def connect(cdp_url: str):
        if cfg.browser_auth is None:
            raise BrowserUnavailable(
                "browser auth not configured",
                "set BRIGHTDATA_BROWSER_AUTH to 'brd-customer-<id>-zone-<zone>:<pw>'")
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            raise BrowserUnavailable(
                "playwright not installed",
                "install with: pip install hermes-brightdata[browser]") from e
        pw = sync_playwright().start()
        browser_obj = None
        try:
            browser_obj = pw.chromium.connect_over_cdp(cdp_url)
            page = browser_obj.new_page()
        except BrowserUnavailable:
            _close_after_failed_start(browser_obj, pw)
            raise
        except Exception:
            _close_after_failed_start(browser_obj, pw)
            # never surface the raw exception: it can embed the CDP URL,
            # which contains the browser_auth password.
            raise BrowserUnavailable(
                "browser connection failed",
                "check BRIGHTDATA_BROWSER_AUTH and that the Scraping Browser zone is active",
            ) from None
        page._bd_pw = pw  # keep ref for teardown
        page._bd_browser = browser_obj
        return page
    return connect


def _close_after_failed_start(browser_obj, pw) -> None:
    """Release a partly created CDP browser before stopping Playwright."""
    if browser_obj is not None:
        try:
            browser_obj.close()
        except Exception:  # noqa: BLE001 — best-effort cleanup after a failed start
            pass
    try:
        pw.stop()
    except Exception:  # noqa: BLE001 — preserve the original connection failure
        pass


class BrowserSession:
    def __init__(self, cfg: Config, connector=None):
        self._cfg = cfg
        self._connector = connector or _default_connector(cfg)
        self._page = None

    def _cdp_url(self) -> str:
        return f"wss://{self._cfg.browser_auth}@{CDP_HOST}"

    def _ensure_page(self):
        if self._page is None:
            self._page = self._connector(self._cdp_url())
        return self._page

    def navigate(self, url: str) -> dict:
        page = self._ensure_page()
        page.goto(url)
        return {"url": url, "ok": True}

    def snapshot(self) -> dict:
        page = self._ensure_page()
        return {"snapshot": page.aria_snapshot()}

    def act(self, action: str, ref: str | None = None, value: str | None = None) -> dict:
        page = self._ensure_page()
        if action == "click":
            page.click(ref)
        elif action == "type":
            if value is None:
                raise ValueError("'value' is required for type action")
            page.fill(ref, value)
        elif action == "scroll":
            delta = int(value) if value else 800
            page.mouse.wheel(0, delta)
        elif action == "wait":
            timeout_ms = float(value) if value else 1000.0
            page.wait_for_timeout(timeout_ms)
        else:
            raise ValueError(f"unknown action '{action}'")
        return {"action": action, "ok": True}

    def get(self, kind: str) -> dict:
        page = self._ensure_page()
        if kind == "html":
            return {"kind": "html", "data": page.content()}
        if kind == "text":
            return {"kind": "text", "data": page.inner_text("body")}
        if kind == "screenshot":
            png = page.screenshot()
            return {"kind": "screenshot", "encoding": "base64",
                    "data": base64.b64encode(png).decode()}
        raise ValueError(f"unknown kind '{kind}'")

    def close(self) -> None:
        page = self._page
        if page is None:
            return
        for closer in (
            page.close,
            getattr(getattr(page, "_bd_browser", None), "close", None),
            getattr(getattr(page, "_bd_pw", None), "stop", None),
        ):
            if closer is None:
                continue
            try:
                closer()
            except Exception:  # noqa: BLE001 — best-effort teardown
                pass
        self._page = None
