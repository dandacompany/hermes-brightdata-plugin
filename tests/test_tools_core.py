import json
import pytest
from brightdata_plugin import tools


class FakeClient:
    def __init__(self):
        self.calls = []

    def unlock(self, url, data_format="markdown", render=False):
        self.calls.append(("unlock", url, data_format))
        return f"MD:{url}"

    def serp(self, search_url, parse_json=True):
        self.calls.append(("serp", search_url))
        return '{"organic": []}'

    def collect_dataset(self, dataset_id, urls, **kw):
        self.calls.append(("collect", dataset_id, tuple(urls)))
        return {"status": "ready", "data": "[]"}


@pytest.fixture
def wired():
    from brightdata_plugin.counter import SessionCounter
    client = FakeClient()
    counter = SessionCounter()
    handlers = tools.make_core_handlers(lambda: client, counter)
    return handlers, client, counter


def test_scrape_returns_json_string(wired):
    handlers, client, _ = wired
    out = handlers["scrape"]({"url": "https://example.com"})
    assert isinstance(out, str)
    data = json.loads(out)
    assert data["content"] == "MD:https://example.com"


def test_scrape_missing_url_returns_error_json(wired):
    handlers, _, _ = wired
    out = handlers["scrape"]({})
    data = json.loads(out)
    assert "error" in data


def test_search_engine_builds_google_url(wired):
    handlers, client, _ = wired
    handlers["search_engine"]({"query": "pizza"})
    assert client.calls[0][0] == "serp"
    assert "q=pizza" in client.calls[0][1]


def test_search_engine_normalizes_nested_json_strings(wired):
    handlers, client, _ = wired
    client.serp = lambda *args, **kwargs: '{"organic": "[{\\"title\\": \\"Example\\"}]"}'
    data = json.loads(handlers["search_engine"]({"query": "pizza"}))
    assert data["results"]["organic"] == [{"title": "Example"}]


def test_search_engine_unknown_engine_error(wired):
    handlers, _, _ = wired
    out = handlers["search_engine"]({"query": "x", "engine": "askjeeves"})
    assert "error" in json.loads(out)


def test_scrape_batch_respects_max(wired):
    handlers, _, _ = wired
    urls = [f"https://e.com/{i}" for i in range(25)]
    out = handlers["scrape_batch"]({"urls": urls})
    data = json.loads(out)
    assert "error" in data  # exceeds MAX_BATCH


def test_scrape_batch_returns_results(wired):
    handlers, _, _ = wired
    out = handlers["scrape_batch"]({"urls": ["https://e.com/1", "https://e.com/2"]})
    data = json.loads(out)
    assert len(data["results"]) == 2


def test_web_data_known_platform(wired):
    handlers, client, _ = wired
    out = handlers["web_data"]({"platform": "amazon_product",
                                "url": "https://amazon.com/dp/x"})
    data = json.loads(out)
    assert data["status"] == "ready"
    assert client.calls[0][1] == "gd_l7q7dkf244hwjntr0"


def test_web_data_normalizes_nested_json_strings(wired):
    handlers, client, _ = wired
    client.collect_dataset = lambda *args, **kwargs: {
        "status": "ready", "data": '[{"title": "Example"}]',
    }
    data = json.loads(handlers["web_data"]({"platform": "amazon_product", "url": "https://amazon.com/dp/x"}))
    assert data["data"] == [{"title": "Example"}]


def test_web_data_unknown_platform_lists_available(wired):
    handlers, _, _ = wired
    out = handlers["web_data"]({"platform": "myspace", "url": "https://x.com"})
    data = json.loads(out)
    assert "error" in data
    assert "amazon_product" in json.dumps(data)


def test_session_stats_reflects_calls(wired):
    handlers, _, counter = wired
    handlers["scrape"]({"url": "https://example.com"})
    out = handlers["session_stats"]({})
    data = json.loads(out)
    assert data["total"] == 1
    assert data["by_tool"]["scrape"] == 1


def test_scrape_batch_isolates_unexpected_error():
    from brightdata_plugin.counter import SessionCounter

    class PartialClient:
        def unlock(self, url, data_format="markdown", render=False):
            if url.endswith("/2"):
                raise ConnectionError("boom")
            return f"MD:{url}"

    counter = SessionCounter()
    handlers = tools.make_core_handlers(lambda: PartialClient(), counter)
    out = handlers["scrape_batch"](
        {"urls": ["https://e.com/1", "https://e.com/2", "https://e.com/3"]})
    data = json.loads(out)
    assert len(data["results"]) == 3
    ok = [r for r in data["results"] if "content" in r]
    errs = [r for r in data["results"] if "error" in r]
    assert len(ok) == 2
    assert len(errs) == 1
    # only successful URLs are counted
    assert counter.stats()["by_tool"]["scrape_batch"] == 2


def test_failed_scrape_not_counted():
    from brightdata_plugin.api import BrightDataError
    from brightdata_plugin.counter import SessionCounter

    class FailUnlock:
        def unlock(self, url, data_format="markdown", render=False):
            raise BrightDataError("fail", status=429)

    counter = SessionCounter()
    handlers = tools.make_core_handlers(lambda: FailUnlock(), counter)
    out = handlers["scrape"]({"url": "https://e.com/x"})
    assert "error" in json.loads(out)
    stats = json.loads(handlers["session_stats"]({}))
    assert stats["by_tool"].get("scrape", 0) == 0


def test_proxy_scrape_missing_url(wired):
    handlers, _, _ = wired
    out = json.loads(handlers["proxy_scrape"]({}))
    assert "error" in out


def test_proxy_scrape_returns_content_and_counts(wired):
    handlers, client, counter = wired
    # extend FakeClient dynamically with a proxy_scrape method
    client.proxy_scrape = lambda url, country=None: f"PROXY:{country}:{url}"
    out = json.loads(handlers["proxy_scrape"]({"url": "https://e.com", "country": "us"}))
    assert out["content"] == "PROXY:us:https://e.com"
    assert out["country"] == "us"
    assert counter.stats()["by_tool"]["proxy_scrape"] == 1
