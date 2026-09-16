from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import character_contract
import codex_auto_orchestrator
import runtime_request


MIXED = """@DevSpace 读取 story-platform-v3 分支，不要切换分支。
【执行约束】
1) 只用这一条命令：python episodes/_system/story_os.py dag run <剧集目录> --codex codex.cmd
2) 看到 STOP_TARGET_REACHED 就停止，不要推进 Release。
【创作要求】
全自动做一篇「尸解仙」，不要每一步问我。
题材方向：民俗与古籍规则改编。现代背景，第一人称亲历视角，像一部真实手机相册。
必须保留：
1. 独占主机制：痕迹与主人解绑——人已不在，但属于他的生活痕迹每天继续出现
2. 不得使用影子作为主证据通道
3. 主角是 20 多岁普通年轻人，不得是道士/调查员/探灵人
"""


def test_partition_preserves_legacy_request_but_keeps_operator_commands_out_of_creative_view():
    request = runtime_request.compile_request(MIXED)
    # Backward compatibility: immutable schema fields still preserve the raw request.
    assert "python episodes/_system/story_os.py" in request["story_input"]["raw"]
    assert runtime_request.validate_request(request) == []

    sections = runtime_request.partitioned_view(request)
    creative = sections["creative_request"]
    operator = sections["operator_instructions"]
    execution = sections["execution_policy"]

    assert creative["story_input"]["mode"] == "core_constraints"
    assert creative["story_input"]["constraints"] == [
        "独占主机制：痕迹与主人解绑——人已不在，但属于他的生活痕迹每天继续出现",
        "不得使用影子作为主证据通道",
        "主角是 20 多岁普通年轻人，不得是道士/调查员/探灵人",
    ]
    assert "python episodes/_system/story_os.py" not in creative["story_input"]["raw"]
    assert "独占主机制" in creative["story_input"]["raw"]
    assert "python episodes/_system/story_os.py" in operator["raw"]
    assert "独占主机制" not in operator["raw"]
    assert execution["mode"] == "full_auto"
    assert execution["runtime"]["continuous_execution"] is True


def test_character_source_text_consumes_only_creative_partition():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        path = ep / "meta/runtime-request.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(runtime_request.compile_request(MIXED), ensure_ascii=False), encoding="utf-8")

        text = character_contract.source_text(ep)

        assert "独占主机制" in text
        assert "20 多岁普通年轻人" in text
        assert "python episodes/_system/story_os.py" not in text
        assert "STOP_TARGET_REACHED" not in text


def test_codex_request_block_labels_three_domains_and_prevents_operator_story_leakage():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        path = ep / "meta/runtime-request.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(runtime_request.compile_request(MIXED), ensure_ascii=False), encoding="utf-8")

        block = codex_auto_orchestrator.runtime_request_block(ep)

        assert "<CREATIVE_REQUEST>" in block
        assert "<EXECUTION_POLICY>" in block
        assert "<OPERATOR_INSTRUCTIONS>" in block
        assert "CREATIVE_REQUEST is the only story/character creative input" in block
        creative_block = block.split("<CREATIVE_REQUEST>", 1)[1].split("</CREATIVE_REQUEST>", 1)[0]
        operator_block = block.split("<OPERATOR_INSTRUCTIONS>", 1)[1].split("</OPERATOR_INSTRUCTIONS>", 1)[0]
        assert "独占主机制" in creative_block
        assert "python episodes/_system/story_os.py" not in creative_block
        assert "python episodes/_system/story_os.py" in operator_block


def test_legacy_request_without_explicit_creative_boundary_keeps_old_creative_semantics():
    request = runtime_request.compile_request("全自动做一篇「旧屋」。剧情大概是：两个年轻人返乡整理旧屋。")
    creative = runtime_request.creative_request_view(request)
    operator = runtime_request.operator_instructions_view(request)

    assert creative["story_input"] == request["story_input"]
    assert "两个年轻人返乡" in creative["story_input"]["raw"]
    assert operator == {"raw": None, "source": "none"}
