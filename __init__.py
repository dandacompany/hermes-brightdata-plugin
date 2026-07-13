"""Hermes directory-plugin entry point.

``hermes plugins install`` loads a cloned plugin directory from its root
``__init__.py``.  The distributable package keeps its implementation in
``brightdata_plugin`` for PyPI entry-point discovery; this shim makes both
installation paths expose the same ``register(ctx)`` function.
"""

if __package__:
    # Hermes loads directory plugins as a package, so the implementation is a
    # child package of this shim.
    from .brightdata_plugin import register
else:  # pragma: no cover - exercised by pytest's top-level package import
    # Test runners can import the repository root as a bare ``__init__``
    # module, where a relative import has no package anchor.
    from brightdata_plugin import register

__all__ = ["register"]
