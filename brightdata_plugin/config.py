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


def load_config(env: dict | None = None) -> Config:
    env = os.environ if env is None else env
    # BRIGHTDATA_API_KEY is Bright Data's canonical env name; accept it as an alias.
    token = env.get("BRIGHTDATA_API_TOKEN") or env.get("BRIGHTDATA_API_KEY")
    if not token:
        raise ConfigError("BRIGHTDATA_API_TOKEN (or BRIGHTDATA_API_KEY) is not set")
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
    )
