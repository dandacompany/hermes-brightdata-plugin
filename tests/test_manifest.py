from pathlib import Path
import yaml
from brightdata_plugin import schemas

ROOT = Path(__file__).resolve().parents[1]


def test_manifest_lists_all_tools():
    manifest = yaml.safe_load((ROOT / "plugin.yaml").read_text())
    assert set(manifest["provides_tools"]) == set(schemas.TOOL_SCHEMAS)


def test_manifest_requires_token():
    manifest = yaml.safe_load((ROOT / "plugin.yaml").read_text())
    req = manifest["requires_env"]
    names = req if isinstance(req, list) else list(req)
    assert any("BRIGHTDATA_API_TOKEN" in str(x) for x in names)
