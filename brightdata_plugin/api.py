from __future__ import annotations

import time

import requests

from .config import Config

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

    def _post_request(self, payload: dict) -> requests.Response:
        resp = self._session.post(REQUEST_ENDPOINT, json=payload, timeout=self._timeout)
        if resp.status_code >= 400:
            raise BrightDataError(
                f"Bright Data /request failed: {resp.status_code}",
                status=resp.status_code,
            )
        return resp

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

    def trigger_dataset(self, dataset_id: str, urls: list[str]) -> str:
        body = [{"url": u} for u in urls]
        resp = self._session.post(
            DATASET_TRIGGER, params={"dataset_id": dataset_id},
            json=body, timeout=self._timeout,
        )
        if resp.status_code >= 400:
            raise BrightDataError(
                f"trigger failed: {resp.status_code}", status=resp.status_code)
        return resp.json()["snapshot_id"]

    def poll_snapshot(self, snapshot_id: str) -> str:
        resp = self._session.get(
            f"{DATASET_PROGRESS}/{snapshot_id}", timeout=self._timeout)
        if resp.status_code >= 400:
            raise BrightDataError(
                f"progress failed: {resp.status_code}", status=resp.status_code)
        return resp.json()["status"]

    def download_snapshot(self, snapshot_id: str, fmt: str = "json") -> str:
        resp = self._session.get(
            f"{DATASET_SNAPSHOT}/{snapshot_id}", params={"format": fmt},
            timeout=self._timeout,
        )
        if resp.status_code >= 400:
            raise BrightDataError(
                f"snapshot failed: {resp.status_code}", status=resp.status_code)
        return resp.text

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
