import pytest
from brightdata_plugin import config


def test_load_config_reads_token():
    cfg = config.load_config({"BRIGHTDATA_API_TOKEN": "tok_123"})
    assert cfg.token == "tok_123"


def test_load_config_defaults_zones():
    cfg = config.load_config({"BRIGHTDATA_API_TOKEN": "tok_123"})
    assert cfg.unlocker_zone == "web_unlocker1"
    assert cfg.serp_zone == "serp_api1"


def test_load_config_overrides_zones():
    cfg = config.load_config({
        "BRIGHTDATA_API_TOKEN": "tok_123",
        "BRIGHTDATA_WEB_UNLOCKER_ZONE": "z_unlock",
        "BRIGHTDATA_SERP_ZONE": "z_serp",
        "BRIGHTDATA_BROWSER_AUTH": "brd-customer-x-zone-b:pw",
    })
    assert cfg.unlocker_zone == "z_unlock"
    assert cfg.serp_zone == "z_serp"
    assert cfg.browser_auth == "brd-customer-x-zone-b:pw"


def test_load_config_missing_token_raises():
    with pytest.raises(config.ConfigError):
        config.load_config({})


def test_load_config_accepts_one_secret_manager_labelled_token():
    cfg = config.load_config({"BRIGHTDATA_TEAM_TOKEN": "tok_123"})
    assert cfg.token == "tok_123"


def test_load_config_rejects_ambiguous_labelled_tokens():
    with pytest.raises(config.ConfigError):
        config.load_config({
            "BRIGHTDATA_TEAM_TOKEN": "tok_123",
            "BRIGHTDATA_STAGING_TOKEN": "tok_456",
        })


def test_load_config_accepts_api_key_alias():
    cfg = config.load_config({"BRIGHTDATA_API_KEY": "key_456"})
    assert cfg.token == "key_456"


def test_load_config_api_token_wins_over_api_key():
    cfg = config.load_config({
        "BRIGHTDATA_API_TOKEN": "tok_123",
        "BRIGHTDATA_API_KEY": "key_456",
    })
    assert cfg.token == "tok_123"


def test_load_config_accepts_unprefixed_unlocker_zone():
    cfg = config.load_config({
        "BRIGHTDATA_API_TOKEN": "tok_123",
        "WEB_UNLOCKER_ZONE": "z_unlock",
    })
    assert cfg.unlocker_zone == "z_unlock"


def test_load_config_prefixed_unlocker_zone_wins():
    cfg = config.load_config({
        "BRIGHTDATA_API_TOKEN": "tok_123",
        "BRIGHTDATA_WEB_UNLOCKER_ZONE": "prefixed",
        "WEB_UNLOCKER_ZONE": "unprefixed",
    })
    assert cfg.unlocker_zone == "prefixed"


def test_load_config_proxy_fields():
    cfg = config.load_config({
        "BRIGHTDATA_API_TOKEN": "tok_123",
        "BRIGHTDATA_PROXY_AUTH": "brd-customer-x-zone-res:pw",
        "BRIGHTDATA_PROXY_CA": "/path/to/ca.crt",
        "BRIGHTDATA_PROXY_HOST": "brd.superproxy.io:33335",
    })
    assert cfg.proxy_auth == "brd-customer-x-zone-res:pw"
    assert cfg.proxy_ca == "/path/to/ca.crt"
    assert cfg.proxy_host == "brd.superproxy.io:33335"


def test_load_config_proxy_defaults():
    cfg = config.load_config({"BRIGHTDATA_API_TOKEN": "tok_123"})
    assert cfg.proxy_auth is None
    assert cfg.proxy_ca is None
    assert cfg.proxy_host == "brd.superproxy.io:33335"
