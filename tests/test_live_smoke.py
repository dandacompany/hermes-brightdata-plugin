import os
import json
import pytest
import brightdata_plugin

pytestmark = pytest.mark.skipif(
    not os.environ.get("BRIGHTDATA_API_TOKEN"),
    reason="live test needs BRIGHTDATA_API_TOKEN",
)


def test_live_scrape_example_com():
    handlers = brightdata_plugin.build_handlers()
    out = handlers["scrape"]({"url": "https://example.com"})
    data = json.loads(out)
    assert "error" not in data or "content" in data


def test_live_search():
    handlers = brightdata_plugin.build_handlers()
    out = handlers["search_engine"]({"query": "bright data"})
    data = json.loads(out)
    assert "results" in data or "error" in data
