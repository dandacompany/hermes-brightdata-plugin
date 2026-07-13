from __future__ import annotations

import json
import re
import ssl
import time
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

from .config import Config


class _ProxyCAAdapter(HTTPAdapter):
    """Trusts a CA file but relaxes OpenSSL 3 strict checks — Bright Data's
    proxy CA cert lacks an Authority Key Identifier, which strict verification
    rejects. The chain is still validated against the provided CA."""

    def __init__(self, cafile: str, **kwargs):
        self._cafile = cafile
        super().__init__(**kwargs)

    def _build_ctx(self) -> ssl.SSLContext:
        ctx = ssl.create_default_context(cafile=self._cafile)
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
        return ctx

    def init_poolmanager(self, connections, maxsize, block=False, **kwargs):
        self.poolmanager = PoolManager(
            num_pools=connections, maxsize=maxsize, block=block,
            ssl_context=self._build_ctx(), **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        kwargs["ssl_context"] = self._build_ctx()
        return super().proxy_manager_for(*args, **kwargs)

BASE_URL = "https://api.brightdata.com"
REQUEST_ENDPOINT = f"{BASE_URL}/request"
DATASET_TRIGGER = f"{BASE_URL}/datasets/v3/trigger"
DATASET_PROGRESS = f"{BASE_URL}/datasets/v3/progress"
DATASET_SNAPSHOT = f"{BASE_URL}/datasets/v3/snapshot"

_HINTS = {
    401: "API token invalid or missing — check BRIGHTDATA_API_TOKEN.",
    402: "Free quota (5,000 req/month) may be exhausted — check billing.",
    429: "Rate limited or quota exhausted — retry later or raise plan limit.",
}

_NETWORK_HINT = (
    "check network connectivity and retry; verify the Bright Data endpoint is reachable."
)
_JSON_HINT = "Bright Data returned invalid JSON; retry and contact support if it persists."
_RESPONSE_HINT = "Bright Data returned an incomplete response; retry and contact support if it persists."


class BrightDataError(Exception):
    def __init__(self, message: str, status: int, hint: str = ""):
        super().__init__(message)
        self.status = status
        self.hint = hint or _HINTS.get(status, "Unexpected Bright Data API error.")


class BrightDataClient:
    def __init__(self, cfg: Config, timeout: int = 60):
        self._cfg = cfg
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {cfg.token}",
            "Content-Type": "application/json",
        })

    def _request(self, method: str, url: str, operation: str, **kwargs) -> requests.Response:
        """Make an API request and expose operational failures uniformly."""
        try:
            resp = self._session.request(method, url, timeout=self._timeout, **kwargs)
        except requests.RequestException as e:
            raise BrightDataError(
                f"Bright Data {operation} request failed", status=0, hint=_NETWORK_HINT,
            ) from e
        if resp.status_code >= 400:
            raise BrightDataError(
                f"Bright Data {operation} failed: {resp.status_code}",
                status=resp.status_code,
            )
        return resp

    @staticmethod
    def _json_response(resp: requests.Response, operation: str,
                       required_field: str | None = None) -> dict:
        try:
            payload = resp.json()
        except (ValueError, json.JSONDecodeError) as e:
            raise BrightDataError(
                f"Bright Data {operation} returned invalid JSON", status=0, hint=_JSON_HINT,
            ) from e
        if not isinstance(payload, dict):
            raise BrightDataError(
                f"Bright Data {operation} returned an unexpected response", status=0,
                hint=_RESPONSE_HINT,
            )
        if required_field and not payload.get(required_field):
            raise BrightDataError(
                f"Bright Data {operation} response is missing '{required_field}'", status=0,
                hint=_RESPONSE_HINT,
            )
        return payload

    def _post_request(self, payload: dict) -> requests.Response:
        return self._request("POST", REQUEST_ENDPOINT, "/request", json=payload)

    def unlock(self, url: str, data_format: str = "markdown", render: bool = False) -> str:
        payload = {
            "zone": self._cfg.unlocker_zone,
            "url": url,
            "format": "raw",
            "data_format": data_format,
        }
        if render:
            payload["render"] = True
        return self._post_request(payload).text

    def serp(self, search_url: str, parse_json: bool = True) -> str:
        url = search_url
        if parse_json and "brd_json=" not in url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}brd_json=1"
        payload = {"zone": self._cfg.serp_zone, "url": url, "format": "raw"}
        return self._post_request(payload).text

    def _proxy_url(self, country: str | None = None) -> str:
        # proxy_auth is 'brd-customer-<id>-zone-<zone>:<password>'; country targeting
        # inserts '-country-<cc>' into the username before the password.
        user, _, password = self._cfg.proxy_auth.partition(":")
        if country:
            # country is LLM-supplied — reject anything but a 2-letter ISO code so it
            # cannot inject '@'/':'/'/' and break out of the userinfo section.
            if not re.fullmatch(r"[A-Za-z]{2}", country):
                raise BrightDataError(
                    "invalid country code", status=0,
                    hint="country must be a 2-letter ISO code (e.g. 'us')")
            user = f"{user}-country-{country.lower()}"
        # URL-encode userinfo as defense-in-depth against stray reserved characters.
        return (f"http://{quote(user, safe='')}:{quote(password, safe='')}"
                f"@{self._cfg.proxy_host}")

    def proxy_scrape(self, url: str, country: str | None = None) -> str:
        if not self._cfg.proxy_auth:
            raise BrightDataError(
                "proxy auth not configured", status=0,
                hint="set BRIGHTDATA_PROXY_AUTH to "
                     "'brd-customer-<id>-zone-<residential-zone>:<password>'",
            )
        proxy_url = self._proxy_url(country)
        proxies = {"http": proxy_url, "https": proxy_url}
        try:
            if self._cfg.proxy_ca:
                sess = requests.Session()
                sess.mount("https://", _ProxyCAAdapter(self._cfg.proxy_ca))
                sess.proxies = proxies
                resp = sess.get(url, timeout=self._timeout)
            else:
                resp = requests.get(url, proxies=proxies, timeout=self._timeout)
        except requests.RequestException as e:
            raise BrightDataError(
                "proxy request failed", status=0,
                hint="check BRIGHTDATA_PROXY_AUTH / BRIGHTDATA_PROXY_CA / network",
            ) from e
        if resp.status_code >= 400:
            raise BrightDataError(
                f"proxy scrape failed: {resp.status_code}", status=resp.status_code)
        return resp.text

    def trigger_dataset(self, dataset_id: str, urls: list[str]) -> str:
        body = [{"url": u} for u in urls]
        resp = self._request(
            "POST", DATASET_TRIGGER, "dataset trigger", params={"dataset_id": dataset_id}, json=body,
        )
        return self._json_response(resp, "dataset trigger", "snapshot_id")["snapshot_id"]

    def poll_snapshot(self, snapshot_id: str) -> str:
        resp = self._request("GET", f"{DATASET_PROGRESS}/{snapshot_id}", "dataset progress")
        return self._json_response(resp, "dataset progress", "status")["status"]

    def download_snapshot(self, snapshot_id: str, fmt: str = "json") -> str:
        return self._request(
            "GET", f"{DATASET_SNAPSHOT}/{snapshot_id}", "dataset snapshot",
            params={"format": fmt},
        ).text

    def collect_dataset(self, dataset_id: str, urls: list[str],
                        poll_interval: float = 2.0, max_wait: float = 60.0,
                        sleep=time.sleep, now=time.monotonic) -> dict:
        snapshot_id = self.trigger_dataset(dataset_id, urls)
        start = now()
        while now() - start <= max_wait:
            status = self.poll_snapshot(snapshot_id)
            if status == "ready":
                return {"status": "ready",
                        "data": self.download_snapshot(snapshot_id)}
            if status == "failed":
                return {"status": "failed", "snapshot_id": snapshot_id}
            sleep(poll_interval)
        return {"status": "timeout", "snapshot_id": snapshot_id}
