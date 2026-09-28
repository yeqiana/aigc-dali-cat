from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT / "episodes/_system", ROOT / "episodes/_system/agents"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import codex_critic_runner
import final_semantic_critic_adapter as critic


def _capsule(tmp_path: Path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setattr(critic, "ROOT", repo)
    sources = []
    frames = []
    text_paths = {}
    for name, content in (("story.md", "frozen story text"),
                          ("storyboard.md", "frozen storyboard text"),
                          ("rubric.md", "frozen rubric text")):
        path = repo / name
        path.write_text(content, encoding="utf-8")
        rel = path.relative_to(repo).as_posix()
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        sources.append({"path": rel, "sha256": sha, "role": "frozen_review_input"})
        text_paths[name] = path
    for n in range(20):
        path = repo / "frames" / f"frame-{n + 1:02d}.png"
        path.parent.mkdir(exist_ok=True)
        Image.new("RGB", (2, 2), (n, n, n)).save(path, format="PNG")
        rel = path.relative_to(repo).as_posix()
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        frames.append({"frame": f"{n + 1:02d}", "asset_path": rel, "asset_sha256": sha})
        sources.append({"path": rel, "sha256": sha, "role": "reviewable_frame"})
    schema = repo / "critic_decision.schema.json"
    schema.write_text("{}", encoding="utf-8")
    capsule = {
        "frame_set": frames,
        "source_files": sources,
        "required_checks": ["identity"],
        "frame_set_sha256": critic.digest(frames),
        "source_sha256": critic.digest(sources),
        "obligation_sha256": "a" * 64,
        "decision_schema_sha256": hashlib.sha256(schema.read_bytes()).hexdigest(),
    }
    capsule["capsule_sha256"] = critic.digest(capsule)
    return repo, capsule, text_paths, schema


def test_final_shadow_classifies_frame_assets_as_images(tmp_path, monkeypatch):
    repo, capsule, _texts, schema = _capsule(tmp_path, monkeypatch)
    plan = critic.final_critic_visual_attachment_plan(capsule, root=repo, non_image_paths=(schema,))
    assert plan["preflight_status"] == "PASS"
    assert plan["expected_visual_asset_count"] == 20
    assert plan["attached_visual_asset_count"] == 20
    assert len(plan["visual_attachment_files"]) == 20
    assert plan["visual_attachment_type_valid"] is True


def test_final_shadow_keeps_story_as_text_attachment(tmp_path, monkeypatch):
    repo, capsule, texts, _schema = _capsule(tmp_path, monkeypatch)
    plan = critic.final_critic_visual_attachment_plan(capsule, root=repo)
    prompt = critic.build_prompt(capsule)
    assert any(row["path"] == "story.md" for row in plan["text_sources"])
    assert "frozen story text" in prompt
    assert texts["story.md"] not in plan["visual_attachment_files"]


def test_final_shadow_keeps_storyboard_as_text_attachment(tmp_path, monkeypatch):
    repo, capsule, texts, _schema = _capsule(tmp_path, monkeypatch)
    plan = critic.final_critic_visual_attachment_plan(capsule, root=repo)
    prompt = critic.build_prompt(capsule)
    assert any(row["path"] == "storyboard.md" for row in plan["text_sources"])
    assert "frozen storyboard text" in prompt
    assert texts["storyboard.md"] not in plan["visual_attachment_files"]


def test_final_shadow_keeps_schema_as_non_image_attachment(tmp_path, monkeypatch):
    repo, capsule, _texts, schema = _capsule(tmp_path, monkeypatch)
    plan = critic.final_critic_visual_attachment_plan(capsule, root=repo, non_image_paths=(schema,))
    assert schema.relative_to(repo).as_posix() in {
        row["path"] for row in plan["non_image_attachments"]
    }
    assert schema not in plan["visual_attachment_files"]


def test_final_shadow_preserves_frame_bytes(tmp_path, monkeypatch):
    repo, capsule, _texts, _schema = _capsule(tmp_path, monkeypatch)
    before = [hashlib.sha256((repo / row["asset_path"]).read_bytes()).hexdigest()
              for row in capsule["frame_set"]]
    critic.final_critic_visual_attachment_plan(capsule, root=repo)
    after = [hashlib.sha256((repo / row["asset_path"]).read_bytes()).hexdigest()
             for row in capsule["frame_set"]]
    assert before == after


def test_final_shadow_frame_sha_unchanged(tmp_path, monkeypatch):
    repo, capsule, _texts, _schema = _capsule(tmp_path, monkeypatch)
    plan = critic.final_critic_visual_attachment_plan(capsule, root=repo)
    assert plan["visual_attachment_sha_match"] is True
    assert all(row["sha256"] == row["expected_sha256"] for row in plan["visual_assets"])


def test_final_shadow_rejects_missing_frame_asset(tmp_path, monkeypatch):
    repo, capsule, _texts, _schema = _capsule(tmp_path, monkeypatch)
    (repo / capsule["frame_set"][0]["asset_path"]).unlink()
    plan = critic.final_critic_visual_attachment_plan(capsule, root=repo)
    assert plan["preflight_status"] == "BLOCKED"
    assert plan["visual_attachment_sha_match"] is False


def test_final_shadow_rejects_frame_sha_drift(tmp_path, monkeypatch):
    repo, capsule, _texts, _schema = _capsule(tmp_path, monkeypatch)
    path = repo / capsule["frame_set"][0]["asset_path"]
    path.write_bytes(path.read_bytes() + b"drift")
    plan = critic.final_critic_visual_attachment_plan(capsule, root=repo)
    assert plan["preflight_status"] == "BLOCKED"
    assert plan["visual_attachment_sha_match"] is False


def test_final_shadow_cli_image_arguments_contain_only_frozen_frames(tmp_path, monkeypatch):
    repo, capsule, texts, schema = _capsule(tmp_path, monkeypatch)
    plan = critic.final_critic_visual_attachment_plan(capsule, root=repo,
                                                      non_image_paths=(schema,))
    argv = codex_critic_runner.build_command(
        codex=Path("codex.exe"), root=repo, attachments=plan["visual_attachment_files"],
        output_schema=schema,
    )
    image_args = [Path(argv[index + 1]) for index, value in enumerate(argv[:-1]) if value == "-i"]
    assert len(image_args) == 20
    assert set(image_args) == set(plan["visual_attachment_files"])
    assert schema not in image_args
    assert all(path not in image_args for path in texts.values())
