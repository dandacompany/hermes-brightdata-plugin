import pytest
import sys
import types
from brightdata_plugin import browser
from brightdata_plugin.config import Config

CFG = Config(token="t", unlocker_zone="u", serp_zone="s",
             browser_auth="brd-customer-x-zone-b:pw")
NO_AUTH = Config(token="t", unlocker_zone="u", serp_zone="s", browser_auth=None)


class _FakeMouse:
    def __init__(self, actions):
        self._actions = actions

    def wheel(self, dx, dy):
        self._actions.append(("wheel", dx, dy))


class FakePage:
    def __init__(self):
        self.actions = []
        self.mouse = _FakeMouse(self.actions)

    def aria_snapshot(self):
        return '- document:\n  - heading "Example Domain" [level=1]'

    def goto(self, url):
        self.actions.append(("goto", url))

    def click(self, ref):
        self.actions.append(("click", ref))

    def fill(self, ref, value):
        self.actions.append(("fill", ref, value))

    def content(self):
        return "<html></html>"

    def inner_text(self, sel):
        return "text"

    def screenshot(self):
        return b"PNG"

    def wait_for_timeout(self, ms):
        self.actions.append(("wait", ms))

    def close(self):
        self.actions.append(("close",))


def make_session():
    page = FakePage()
    sess = browser.BrowserSession(CFG, connector=lambda cdp: page)
    return sess, page


def test_navigate_connects_and_goes():
    sess, page = make_session()
    out = sess.navigate("https://example.com")
    assert out["url"] == "https://example.com"
    assert ("goto", "https://example.com") in page.actions


def test_act_click():
    sess, page = make_session()
    sess.navigate("https://example.com")
    sess.act("click", ref="btn-1")
    assert ("click", "btn-1") in page.actions


def test_act_type_requires_value():
    sess, _ = make_session()
    sess.navigate("https://example.com")
    with pytest.raises(ValueError):
        sess.act("type", ref="input-1")


def test_get_text():
    sess, _ = make_session()
    sess.navigate("https://example.com")
    out = sess.get("text")
    assert out["kind"] == "text"
    assert out["data"] == "text"


def test_get_screenshot_base64():
    sess, _ = make_session()
    sess.navigate("https://example.com")
    out = sess.get("screenshot")
    assert out["kind"] == "screenshot"
    assert out["encoding"] == "base64"


def test_missing_auth_raises_browser_unavailable():
    sess = browser.BrowserSession(NO_AUTH)  # default connector
    with pytest.raises(browser.BrowserUnavailable):
        sess.navigate("https://example.com")


def test_close_calls_page_close_and_resets():
    sess, page = make_session()
    sess.navigate("https://example.com")
    sess.close()
    assert ("close",) in page.actions
    assert sess._page is None


def test_close_is_exception_safe():
    class RaisingPage:
        def goto(self, url):
            pass

        def close(self):
            raise RuntimeError("already disconnected")

    page = RaisingPage()
    sess = browser.BrowserSession(CFG, connector=lambda cdp: page)
    sess.navigate("https://example.com")
    sess.close()  # must not raise despite page.close() raising
    assert sess._page is None


def test_snapshot_uses_aria_snapshot():
    sess, page = make_session()
    sess.navigate("https://example.com")
    out = sess.snapshot()
    assert "Example Domain" in out["snapshot"]


def test_act_scroll_uses_mouse_wheel():
    sess, page = make_session()
    sess.navigate("https://example.com")
    sess.act("scroll", value="500")
    assert ("wheel", 0, 500) in page.actions


def test_act_wait_uses_wait_for_timeout():
    sess, page = make_session()
    sess.navigate("https://example.com")
    sess.act("wait", value="250")
    assert ("wait", 250.0) in page.actions


def test_failed_page_creation_closes_browser_before_stopping_playwright(monkeypatch):
    calls = []

    class FakeBrowser:
        def new_page(self):
            calls.append("new_page")
            raise RuntimeError("page creation failed")

        def close(self):
            calls.append("browser.close")

    class FakePlaywright:
        def __init__(self):
            self.chromium = types.SimpleNamespace(connect_over_cdp=self.connect_over_cdp)

        def connect_over_cdp(self, url):
            calls.append("connect")
            return FakeBrowser()

        def stop(self):
            calls.append("pw.stop")

    pw = FakePlaywright()
    sync_api = types.ModuleType("playwright.sync_api")
    sync_api.sync_playwright = lambda: types.SimpleNamespace(start=lambda: pw)
    monkeypatch.setitem(sys.modules, "playwright", types.ModuleType("playwright"))
    monkeypatch.setitem(sys.modules, "playwright.sync_api", sync_api)

    with pytest.raises(browser.BrowserUnavailable):
        browser._default_connector(CFG)("wss://secret@example.test")

    assert calls == ["connect", "new_page", "browser.close", "pw.stop"]
