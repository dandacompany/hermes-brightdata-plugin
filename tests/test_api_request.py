import pytest
import responses
from brightdata_plugin.api import BrightDataClient, BrightDataError
from brightdata_plugin.config import Config

CFG = Config(token="tok_123", unlocker_zone="web_unlocker1",
             serp_zone="serp_api1", browser_auth=None)
ENDPOINT = "https://api.brightdata.com/request"


@responses.activate
def test_unlock_sends_markdown_request_and_returns_body():
    responses.add(responses.POST, ENDPOINT, body="# Hello", status=200)
    client = BrightDataClient(CFG)
    out = client.unlock("https://example.com")
    assert out == "# Hello"
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer tok_123"
    import json
    payload = json.loads(req.body)
    assert payload["zone"] == "web_unlocker1"
    assert payload["url"] == "https://example.com"
    assert payload["format"] == "raw"
    assert payload["data_format"] == "markdown"


@responses.activate
def test_serp_appends_brd_json_and_uses_serp_zone():
    responses.add(responses.POST, ENDPOINT, body='{"organic": []}', status=200)
    client = BrightDataClient(CFG)
    out = client.serp("https://www.google.com/search?q=pizza")
    assert '"organic"' in out
    import json
    payload = json.loads(responses.calls[0].request.body)
    assert payload["zone"] == "serp_api1"
    assert "brd_json=1" in payload["url"]


@responses.activate
def test_unlock_401_raises_with_hint():
    responses.add(responses.POST, ENDPOINT,
                  json={"error": "User authentication is required"}, status=401)
    client = BrightDataClient(CFG)
    with pytest.raises(BrightDataError) as exc:
        client.unlock("https://example.com")
    assert exc.value.status == 401
    assert "token" in exc.value.hint.lower()


@responses.activate
def test_unlock_429_hint_mentions_quota():
    responses.add(responses.POST, ENDPOINT, body="rate limited", status=429)
    client = BrightDataClient(CFG)
    with pytest.raises(BrightDataError) as exc:
        client.unlock("https://example.com")
    assert exc.value.status == 429
    assert "quota" in exc.value.hint.lower() or "rate" in exc.value.hint.lower()
