"""Regression coverage for ``hermes plugins install <owner>/<repo>``."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_root_directory_plugin_shim_loads_register_function():
    """Hermes loads directory plugins from the cloned repository root."""
    parent_name = "hermes_plugins"
    module_name = f"{parent_name}.brightdata_git_install_test"
    parent = types.ModuleType(parent_name)
    parent.__path__ = []  # type: ignore[attr-defined]
    sys.modules[parent_name] = parent

    spec = importlib.util.spec_from_file_location(
        module_name,
        ROOT / "__init__.py",
        submodule_search_locations=[str(ROOT)],
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    try:
        spec.loader.exec_module(module)
        assert callable(module.register)
    finally:
        for name in list(sys.modules):
            if name == module_name or name.startswith(f"{module_name}."):
                sys.modules.pop(name, None)
        sys.modules.pop(parent_name, None)
