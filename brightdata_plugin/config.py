from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    token: str
    unlocker_zone: str
    serp_zone: str
    browser_auth: str | None
    proxy_auth: str | None = None
    proxy_ca: str | None = None
    proxy_host: str = "brd.superproxy.io:33335"


def _labelled_token(env: dict) -> str | None:
    """Accept one secret-manager-labelled Bright Data token without ambiguity.

    Secret managers often preserve a credential's label in the environment
    (for example ``BRIGHTDATA_TEAM_TOKEN``). Explicit standard names always
    win; multiple labelled candidates intentionally fail closed.
    """
    candidates = [
        value for name, value in env.items()
        if name.startswith("BRIGHTDATA_") and name.endswith("_TOKEN") and value
    ]
    return candidates[0] if len(candidates) == 1 else None


def load_config(env: dict | None = None) -> Config:
    env = os.environ if env is None else env
    # BRIGHTDATA_API_KEY is Bright Data's canonical env name; accept it as an alias.
    token = (
        env.get("BRIGHTDATA_API_TOKEN")
        or env.get("BRIGHTDATA_API_KEY")
        or _labelled_token(env)
    )
    if not token:
        raise ConfigError(
            "BRIGHTDATA_API_TOKEN (or BRIGHTDATA_API_KEY) is not set; "
            "one BRIGHTDATA_<LABEL>_TOKEN is also accepted"
        )
    unlocker_zone = (
        env.get("BRIGHTDATA_WEB_UNLOCKER_ZONE")
        or env.get("WEB_UNLOCKER_ZONE")
        or "web_unlocker1"
    )
    return Config(
        token=token,
        unlocker_zone=unlocker_zone,
        serp_zone=env.get("BRIGHTDATA_SERP_ZONE", "serp_api1"),
        browser_auth=env.get("BRIGHTDATA_BROWSER_AUTH"),
        proxy_auth=env.get("BRIGHTDATA_PROXY_AUTH"),
        proxy_ca=env.get("BRIGHTDATA_PROXY_CA"),
        proxy_host=env.get("BRIGHTDATA_PROXY_HOST", "brd.superproxy.io:33335"),
    )
