"""Conftest: ensure `from src.xxx import ...` works in tests.

The project uses a `src/` layout without `__init__.py` at the `src/` level,
so `src` is not a package. Adding `src/` to sys.path lets tests do
`import cache` directly, but the existing tests use `from src.cache import ...`
which requires `src` to be a package.

The cleanest fix: add `src/` to sys.path AND alias `src` to point at the
`src/` directory so `from src.cache import ...` resolves to `<root>/src/cache.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"

if str(_SRC.parent) not in sys.path:
    sys.path.insert(0, str(_SRC.parent))

# Register `src` as a package alias so `from src.cache import ...` works.
import importlib
import types

if "src" not in sys.modules:
    _src_pkg = types.ModuleType("src")
    _src_pkg.__path__ = [str(_SRC)]
    sys.modules["src"] = _src_pkg
