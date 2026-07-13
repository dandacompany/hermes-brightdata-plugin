from __future__ import annotations

import json

from . import schemas
from .api import BrightDataClient
from .browser import BrowserSession
from .config import Config, load_config
from .counter import SessionCounter
from .provider import BrightDataWebSearchProvider
from .tools import make_browser_handlers, make_core_handlers


def build_handlers(cfg: Config | None = None) -> dict:
    cfg = cfg or load_config()
    counter = SessionCounter()

    _client: dict = {}
    def get_client() -> BrightDataClient:
        if "c" not in _client:
            _client["c"] = BrightDataClient(cfg)
        return _client["c"]

    _session: dict = {}
    def get_session() -> BrowserSession:
        if "s" not in _session:
            _session["s"] = BrowserSession(cfg)
        return _session["s"]

    handlers = {}
    handlers.update(make_core_handlers(get_client, counter))
    handlers.update(make_browser_handlers(get_session, counter))
    # private keys popped by register(); not real tools
    handlers["_counter"] = counter  # type: ignore
    handlers["_get_client"] = get_client  # type: ignore
    handlers["_get_session"] = get_session  # type: ignore
    handlers["_session_holder"] = _session  # type: ignore
    return handlers


def register(ctx) -> None:
    cfg = load_config()
    handlers = build_handlers(cfg)
    counter = handlers.pop("_counter")
    get_client = handlers.pop("_get_client")
    handlers.pop("_get_session")
    session_holder = handlers.pop("_session_holder")

    for name, handler in handlers.items():
        ctx.register_tool(name, "brightdata", schemas.TOOL_SCHEMAS[name], handler)

    # Provider-aware Hermes releases can route their native ``web_search``
    # tool here. Older releases retain the standalone ``search_engine`` tool
    # without overwriting any built-in handler.
    register_provider = getattr(ctx, "register_web_search_provider", None)
    if callable(register_provider):
        register_provider(BrightDataWebSearchProvider(get_client, configured=bool(cfg.token)))

    def brightdata_cmd(args, **kwargs) -> str:
        return json.dumps(counter.stats(), ensure_ascii=False)
    ctx.register_command("brightdata", brightdata_cmd,
                         description="Show Bright Data session usage stats")

    def on_session_end(*args, **kwargs):
        # only close if a browser session was actually created this session
        s = session_holder.get("s")
        if s is not None:
            try:
                s.close()
            except Exception:  # noqa: BLE001
                pass
    ctx.register_hook("on_session_end", on_session_end)
