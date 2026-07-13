from brightdata_plugin.api import BrightDataError
from brightdata_plugin.provider import BrightDataWebSearchProvider


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.urls = []

    def serp(self, url):
        self.urls.append(url)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def test_provider_returns_normalized_web_results():
    client = FakeClient(
        '{"organic": "[{\\"title\\": \\"Example\\", \\"link\\": \\"https://example.com\\", '
        '\\"snippet\\": \\"Description\\", \\"rank\\": 7}]"}'
    )
    provider = BrightDataWebSearchProvider(lambda: client)

    result = provider.search("hello world", limit=1)

    assert result == {"success": True, "data": {"web": [{
        "title": "Example", "url": "https://example.com", "description": "Description", "position": 7,
    }]}}
    assert "q=hello+world" in client.urls[0]
    assert provider.name == "brightdata"
    assert provider.is_available() is True


def test_provider_exposes_hermes_setup_schema():
    provider = BrightDataWebSearchProvider(lambda: FakeClient({}))

    assert provider.get_setup_schema() == {
        "name": "Bright Data",
        "badge": "paid",
        "tag": "SERP search through Bright Data's Web Unlocker API.",
        "env_vars": [{
            "key": "BRIGHTDATA_API_TOKEN",
            "prompt": "Bright Data API token",
            "url": "https://brightdata.com/cp/zones",
        }],
    }


def test_provider_converts_brightdata_error_to_failure_payload():
    provider = BrightDataWebSearchProvider(
        lambda: FakeClient(BrightDataError("request failed", status=429, hint="retry later"))
    )
    result = provider.search("hello")
    assert result["success"] is False
    assert result["hint"] == "retry later"


def test_provider_rejects_unparseable_serp_result():
    provider = BrightDataWebSearchProvider(lambda: FakeClient("<html>not JSON</html>"))
    result = provider.search("hello")
    assert result["success"] is False
    assert "organic" in result["error"]
