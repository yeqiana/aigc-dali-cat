"""Prevent accidental removal of StoryOS' permanent multi-Episode boundary."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"


def _func_body(path: Path, name: str) -> str:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    node = next(n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and n.name == name)
    return ast.get_source_segment(text, node) or ""


def test_multi_episode_permanent_policy_preserved_in_codex_agent_contract():
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "STORY_OS_MULTI_EPISODE_PERMANENT_CONTRACT_BEGIN" in text
    assert "多个不同 Episode 同时执行正式生产" in text
    assert "合计最多 5 张在途图片" in text
    assert "同一 Episode 只允许一个正式 Owner/Writer" in text
    assert "跨主机或独立 Git 克隆" in text
    assert "共享硬上限不等于严格跨 Episode 公平调度" in text


def test_all_formal_image_entrypoints_still_require_shared_capacity():
    for file, method in (
        ("image_worker_pool.py", "execute"),
        ("batch_image_worker.py", "execute_batch"),
        ("image_generation_gateway.py", "provider_generate"),
        ("image_generation_gateway.py", "provider_generate_many"),
        ("codex_subscription_image.py", "main"),
    ):
        body = _func_body(SYSTEM / file, method)
        assert "global_image_capacity.image_permits(" in body, (file, method)
    capacity = (SYSTEM / "global_image_capacity.py").read_text(encoding="utf-8")
    assert "CAPACITY = 5" in capacity


def test_multi_episode_launch_remains_opt_in_and_never_bypasses_driver():
    body = _func_body(ROOT / "scripts" / "storyos_multi_episode.py", "main")
    assert "MULTI_EPISODE_REAL_PRODUCTION_ACK_REQUIRED" in body
    assert "start_episodes(eps)" in body
    start = _func_body(ROOT / "scripts" / "storyos_multi_episode.py", "start_episodes")
    assert "runtime_driver.launch" in start
    assert "MULTI_EPISODE_DRIVER_OWNER_UNVERIFIED" in start
