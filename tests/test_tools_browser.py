import json
import pytest
from brightdata_plugin import tools
from brightdata_plugin.browser import BrowserUnavailable
from brightdata_plugin.counter import SessionCounter


class FakeSession:
    def navigate(self, url):
        return {"url": url, "ok": True}

    def snapshot(self):
        return {"snapshot": {"role": "WebArea"}}

    def act(self, action, ref=None, value=None):
        if action == "type" and value is None:
            raise ValueError("value required")
        return {"action": action, "ok": True}

    def get(self, kind):
        return {"kind": kind, "data": "x"}


@pytest.fixture
def wired():
    counter = SessionCounter()
    session = FakeSession()
    handlers = tools.make_browser_handlers(lambda: session, counter)
    return handlers, counter


def test_browser_navigate(wired):
    handlers, _ = wired
    out = handlers["brightdata_browser_navigate"]({"url": "https://example.com"})
    assert json.loads(out)["url"] == "https://example.com"


def test_browser_navigate_missing_url(wired):
    handlers, _ = wired
    out = handlers["brightdata_browser_navigate"]({})
    assert "error" in json.loads(out)


def test_browser_act_value_error_becomes_error_json(wired):
    handlers, _ = wired
    out = handlers["brightdata_browser_act"]({"action": "type", "ref": "i1"})
    assert "error" in json.loads(out)


def test_browser_unavailable_returns_hint():
    def raiser():
        raise BrowserUnavailable("no playwright", "pip install hermes-brightdata[browser]")
    handlers = tools.make_browser_handlers(raiser, SessionCounter())
    out = handlers["brightdata_browser_navigate"]({"url": "https://example.com"})
    data = json.loads(out)
    assert "error" in data
    assert "playwright" in data["hint"]


def test_browser_get_records_counter(wired):
    handlers, counter = wired
    handlers["brightdata_browser_get"]({"kind": "text"})
    assert counter.stats()["by_tool"]["brightdata_browser_get"] == 1


def test_browser_act_failure_not_counted(wired):
    handlers, counter = wired
    out = handlers["brightdata_browser_act"]({"action": "type", "ref": "i1"})
    assert "error" in json.loads(out)
    # a failed browser action must not be counted as a successful call
    assert counter.stats()["by_tool"].get("brightdata_browser_act", 0) == 0
