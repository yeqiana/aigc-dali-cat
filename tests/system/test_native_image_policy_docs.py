from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_active_agent_instructions_do_not_enable_legacy_image_api():
    for name in ("AGENTS.md", "SKILL.md"):
        document = (ROOT / name).read_text(encoding="utf-8-sig")
        assert "当前生产已退役" in document
        assert "原生 ChatGPT/Codex 登录通道" in document
        assert "严格禁止 OpenCodex" in document
        assert "有无 `OPENAI_API_KEY`" in document
        assert "存在 `OPENAI_API_KEY`：优先 OpenAI Image API" not in document
        assert "没有 `OPENAI_API_KEY` 时，Production Batch 正式走" not in document
