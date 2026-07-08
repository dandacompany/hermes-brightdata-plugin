import json
import brightdata_plugin
from brightdata_plugin.config import Config

CFG = Config(token="t", unlocker_zone="u", serp_zone="s", browser_auth=None)


class FakeCtx:
    def __init__(self):
        self.tools = {}
        self.commands = {}
        self.hooks = {}

    def register_tool(self, name, toolset, schema, handler, override=False):
        self.tools[name] = (toolset, schema, handler)

    def register_command(self, name, handler, description=""):
        self.commands[name] = handler

    def register_hook(self, event, fn):
        self.hooks.setdefault(event, []).append(fn)


def test_register_wires_nine_tools(monkeypatch):
    monkeypatch.setenv("BRIGHTDATA_API_TOKEN", "t")
    ctx = FakeCtx()
    brightdata_plugin.register(ctx)
    assert len(ctx.tools) == 9
    assert "scrape" in ctx.tools
    assert "browser_navigate" in ctx.tools


def test_register_adds_command_and_hook(monkeypatch):
    monkeypatch.setenv("BRIGHTDATA_API_TOKEN", "t")
    ctx = FakeCtx()
    brightdata_plugin.register(ctx)
    assert "brightdata" in ctx.commands
    assert "on_session_end" in ctx.hooks


def test_build_handlers_returns_nine():
    handlers = brightdata_plugin.build_handlers(CFG)
    real_tools = {k: v for k, v in handlers.items() if not k.startswith("_")}
    assert len(real_tools) == 9
    assert {"_counter", "_get_session", "_session_holder"} <= handlers.keys()


def test_on_session_end_closes_created_session(monkeypatch):
    monkeypatch.setenv("BRIGHTDATA_API_TOKEN", "t")
    closed = []

    class FakeSession:
        def __init__(self, cfg):
            pass

        def navigate(self, url):
            return {"url": url, "ok": True}

        def close(self):
            closed.append(True)

    monkeypatch.setattr(brightdata_plugin, "BrowserSession", FakeSession)
    ctx = FakeCtx()
    brightdata_plugin.register(ctx)
    # trigger lazy session creation through the browser_navigate tool handler
    ctx.tools["browser_navigate"][2]({"url": "https://example.com"})
    for fn in ctx.hooks["on_session_end"]:
        fn()
    assert closed == [True]


def test_on_session_end_noop_when_no_session(monkeypatch):
    monkeypatch.setenv("BRIGHTDATA_API_TOKEN", "t")
    created = []

    class FakeSession:
        def __init__(self, cfg):
            created.append(True)

        def close(self):
            pass

    monkeypatch.setattr(brightdata_plugin, "BrowserSession", FakeSession)
    ctx = FakeCtx()
    brightdata_plugin.register(ctx)
    # never invoke a browser tool → no session should be created
    for fn in ctx.hooks["on_session_end"]:
        fn()
    assert created == []
