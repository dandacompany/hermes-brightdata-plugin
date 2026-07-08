import json
import responses
from brightdata_plugin.api import BrightDataClient
from brightdata_plugin.config import Config

CFG = Config(token="tok_123", unlocker_zone="web_unlocker1",
             serp_zone="serp_api1", browser_auth=None)
BASE = "https://api.brightdata.com/datasets/v3"


@responses.activate
def test_trigger_returns_snapshot_id():
    responses.add(responses.POST, f"{BASE}/trigger",
                  json={"snapshot_id": "s_abc"}, status=200)
    client = BrightDataClient(CFG)
    sid = client.trigger_dataset("gd_x", ["https://example.com/p/1"])
    assert sid == "s_abc"
    req = responses.calls[0].request
    assert "dataset_id=gd_x" in req.url
    body = json.loads(req.body)
    assert body == [{"url": "https://example.com/p/1"}]


@responses.activate
def test_poll_returns_status():
    responses.add(responses.GET, f"{BASE}/progress/s_abc",
                  json={"status": "running"}, status=200)
    client = BrightDataClient(CFG)
    assert client.poll_snapshot("s_abc") == "running"


@responses.activate
def test_download_returns_body():
    responses.add(responses.GET, f"{BASE}/snapshot/s_abc",
                  body='[{"title": "x"}]', status=200)
    client = BrightDataClient(CFG)
    out = client.download_snapshot("s_abc")
    assert '"title"' in out


@responses.activate
def test_collect_dataset_happy_path():
    responses.add(responses.POST, f"{BASE}/trigger",
                  json={"snapshot_id": "s_abc"}, status=200)
    responses.add(responses.GET, f"{BASE}/progress/s_abc",
                  json={"status": "running"}, status=200)
    responses.add(responses.GET, f"{BASE}/progress/s_abc",
                  json={"status": "ready"}, status=200)
    responses.add(responses.GET, f"{BASE}/snapshot/s_abc",
                  body='[{"title": "x"}]', status=200)
    client = BrightDataClient(CFG)
    calls = []
    result = client.collect_dataset("gd_x", ["https://example.com/p/1"],
                                    poll_interval=0, max_wait=10,
                                    sleep=lambda s: calls.append(s))
    assert result["status"] == "ready"
    assert '"title"' in result["data"]


@responses.activate
def test_collect_dataset_timeout_returns_snapshot_id():
    responses.add(responses.POST, f"{BASE}/trigger",
                  json={"snapshot_id": "s_abc"}, status=200)
    responses.add(responses.GET, f"{BASE}/progress/s_abc",
                  json={"status": "running"}, status=200)
    client = BrightDataClient(CFG)
    ticks = iter([0.0, 0.0, 999.0])  # 3rd now() exceeds max_wait
    result = client.collect_dataset("gd_x", ["https://example.com/p/1"],
                                    poll_interval=0, max_wait=10,
                                    sleep=lambda s: None,
                                    now=lambda: next(ticks))
    assert result["status"] == "timeout"
    assert result["snapshot_id"] == "s_abc"


@responses.activate
def test_collect_dataset_failed_status():
    responses.add(responses.POST, f"{BASE}/trigger",
                  json={"snapshot_id": "s_abc"}, status=200)
    responses.add(responses.GET, f"{BASE}/progress/s_abc",
                  json={"status": "failed"}, status=200)
    client = BrightDataClient(CFG)
    result = client.collect_dataset("gd_x", ["https://example.com/p/1"],
                                    poll_interval=0, max_wait=10,
                                    sleep=lambda s: None)
    assert result["status"] == "failed"
    assert result["snapshot_id"] == "s_abc"
