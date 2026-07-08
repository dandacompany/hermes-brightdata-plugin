import pytest
import responses
from brightdata_plugin.api import BrightDataClient, BrightDataError
from brightdata_plugin.config import Config

PROXY_CFG = Config(
    token="tok", unlocker_zone="u", serp_zone="s", browser_auth=None,
    proxy_auth="brd-customer-x-zone-res:pw", proxy_ca=None,
    proxy_host="brd.superproxy.io:33335",
)
NO_PROXY_CFG = Config(token="tok", unlocker_zone="u", serp_zone="s", browser_auth=None)


def test_proxy_url_without_country():
    client = BrightDataClient(PROXY_CFG)
    assert client._proxy_url() == (
        "http://brd-customer-x-zone-res:pw@brd.superproxy.io:33335")


def test_proxy_url_with_country_injects_suffix():
    client = BrightDataClient(PROXY_CFG)
    assert client._proxy_url("US") == (
        "http://brd-customer-x-zone-res-country-us:pw@brd.superproxy.io:33335")


@responses.activate
def test_proxy_scrape_returns_body():
    responses.add(responses.GET, "https://example.com", body="<html>hi</html>", status=200)
    client = BrightDataClient(PROXY_CFG)
    out = client.proxy_scrape("https://example.com")
    assert out == "<html>hi</html>"


def test_proxy_scrape_no_auth_raises_with_hint():
    client = BrightDataClient(NO_PROXY_CFG)
    with pytest.raises(BrightDataError) as exc:
        client.proxy_scrape("https://example.com")
    assert "BRIGHTDATA_PROXY_AUTH" in exc.value.hint


@responses.activate
def test_proxy_scrape_http_error_raises():
    responses.add(responses.GET, "https://example.com", body="blocked", status=403)
    client = BrightDataClient(PROXY_CFG)
    with pytest.raises(BrightDataError) as exc:
        client.proxy_scrape("https://example.com")
    assert exc.value.status == 403
