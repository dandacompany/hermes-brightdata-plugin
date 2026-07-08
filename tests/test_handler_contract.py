import json
import pytest
import brightdata_plugin
from brightdata_plugin.config import Config

CFG = Config(token="t", unlocker_zone="u", serp_zone="s", browser_auth=None)
ALL = ["search_engine", "scrape", "scrape_batch", "web_data", "proxy_scrape",
       "session_stats",
       "browser_navigate", "browser_snapshot", "browser_act", "browser_get"]


@pytest.fixture
def handlers():
    return brightdata_plugin.build_handlers(CFG)


@pytest.mark.parametrize("name", ALL)
def test_handler_returns_json_string_on_empty_args(handlers, name):
    out = handlers[name]({})
    assert isinstance(out, str)
    json.loads(out)  # must be valid JSON


@pytest.mark.parametrize("name", ALL)
def test_handler_accepts_kwargs(handlers, name):
    out = handlers[name]({}, extra="ignored")
    assert isinstance(out, str)


@pytest.mark.parametrize("name", ALL)
def test_handler_never_raises(handlers, name, monkeypatch):
    # keep the suite hermetic: block real Bright Data network calls so
    # truthy-but-garbage args cannot trigger a live HTTPS request
    import requests

    def _boom(*args, **kwargs):
        raise requests.exceptions.ConnectionError("network blocked in tests")

    monkeypatch.setattr(requests.Session, "request", _boom)
    # even with garbage args and the network cut, handlers must not raise
    handlers[name]({"url": 123, "urls": "notalist", "platform": None})
