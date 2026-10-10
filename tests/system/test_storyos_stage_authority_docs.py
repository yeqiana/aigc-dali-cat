"""Agent entrypoints must not teach obsolete JSON-only stage authority."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_agent_entrypoints_state_mode_source_of_truth():
    for name in ("AGENTS.md", "SKILL.md"):
        text = (ROOT / name).read_text(encoding="utf-8-sig")
        assert "episode_state_persistence" in text
        assert "MySQL" in text
        assert "- `meta/episode-state.json` 仍是唯一阶段状态源。" not in text
        assert "不改变 `meta/episode-state.json` 唯一阶段权威" not in text


def test_authority_matrix_documents_mysql_fail_closed():
    text = (ROOT / "docs/StoryOS_阶段状态权威矩阵_20261010.md").read_text(encoding="utf-8-sig")
    for token in ("mysql", "dual", "json", "load_with_source", "不得", "Episode"):
        assert token in text
