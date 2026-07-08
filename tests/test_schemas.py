from brightdata_plugin import schemas

EXPECTED = {
    "search_engine", "scrape", "scrape_batch", "web_data", "session_stats",
    "browser_navigate", "browser_snapshot", "browser_act", "browser_get",
}


def test_all_nine_tools_present():
    assert set(schemas.TOOL_SCHEMAS) == EXPECTED


def test_each_schema_has_required_keys():
    for name, s in schemas.TOOL_SCHEMAS.items():
        assert s["name"] == name
        assert isinstance(s["description"], str) and len(s["description"]) > 20
        assert s["parameters"]["type"] == "object"
        assert "properties" in s["parameters"]


def test_web_data_lists_platform_enum():
    from brightdata_plugin import datasets
    enum = schemas.TOOL_SCHEMAS["web_data"]["parameters"]["properties"]["platform"]["enum"]
    assert set(enum) == set(datasets.platforms())


def test_search_engine_enum_matches_tools():
    from brightdata_plugin.tools import SEARCH_ENGINE_URLS
    enum = schemas.TOOL_SCHEMAS["search_engine"]["parameters"]["properties"]["engine"]["enum"]
    assert set(enum) == set(SEARCH_ENGINE_URLS)
