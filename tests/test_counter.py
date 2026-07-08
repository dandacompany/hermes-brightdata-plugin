from brightdata_plugin.counter import SessionCounter


def test_counter_records_and_reports():
    c = SessionCounter()
    c.record("scrape")
    c.record("scrape")
    c.record("search_engine")
    stats = c.stats()
    assert stats["total"] == 3
    assert stats["by_tool"]["scrape"] == 2
    assert stats["by_tool"]["search_engine"] == 1


def test_counter_reset():
    c = SessionCounter()
    c.record("scrape")
    c.reset()
    assert c.stats()["total"] == 0
