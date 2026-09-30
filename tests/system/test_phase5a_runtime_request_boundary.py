from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_request


def test_normal_runtime_request_remains_valid_without_canary_fields():
    request = runtime_request.compile_request(
        "读取 story 分支。全自动做一篇「Phase5A 请求边界验证」。"
    )

    assert runtime_request.validate_request(request) == []


def test_runtime_request_rejects_top_level_visual_lock_bypass():
    request = runtime_request.compile_request(
        "读取 story 分支。全自动做一篇「Phase5A 请求边界验证」。"
    )
    request["skip_visual_lock"] = True

    assert "RUNTIME_REQUEST_CANNOT_ENABLE_CANARY_BYPASS" in runtime_request.validate_request(request)


def test_runtime_request_rejects_nested_canary_scope():
    request = runtime_request.compile_request(
        "读取 story 分支。全自动做一篇「Phase5A 请求边界验证」。"
    )
    request["runtime"]["canary_scope"] = "PRODUCTION_SUBPATH"

    assert "RUNTIME_REQUEST_CANNOT_ENABLE_CANARY_BYPASS" in runtime_request.validate_request(request)
