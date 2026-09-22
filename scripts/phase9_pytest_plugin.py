"""
Temporary pytest bridge for Phase9 Runtime Operations validation.

pytest itself must use Python stdlib `platform` during bootstrap.
After pytest session starts, Runtime tests need the Story OS `platform` package.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def register_story_platform_package() -> None:
    platform_path = PROJECT_ROOT / "platform"

    if not platform_path.exists():
        return

    spec = importlib.util.spec_from_file_location(
        "platform",
        platform_path / "__init__.py",
        submodule_search_locations=[str(platform_path)],
    )

    if spec is None or spec.loader is None:
        return

    module = importlib.util.module_from_spec(spec)
    sys.modules["platform"] = module
    spec.loader.exec_module(module)


def pytest_sessionstart(session):
    register_story_platform_package()
