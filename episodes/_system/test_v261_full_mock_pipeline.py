#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path
from unittest import mock

from PIL import Image, ImageDraw

SYSTEM = Path(__file__).resolve().parent
ROOT = SYSTEM.parents[1]
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import caption_image_audit
import episode_performance
import final_candidate_snapshot
import release_preflight
import runtime_provenance
import subtitle_layout
import text_audit

VERSION = "2.6.1"
TITLE = "凌晨一点，返乡大巴多停了一站"
VISUAL_LOCK_FRAMES = {1, 7, 13, 20}
CAPTIONS = {
    1: "凌晨一点，我坐上了回老家的末班大巴。",
    2: "车上没几个人，司机一直没开广播。",
    3: "出了县城，窗外连路灯都快没了。",
    4: "我本来想睡，后视镜里却一直有白光。",
    5: "那光像一辆车，可后面明明什么都没有。",
    6: "十几分钟后，大巴突然拐进了旧辅路。",
    7: "路边站着一块早就拆掉的收费站牌子。",
    8: "司机没减速，像每天都要从这里经过。",
    9: "我看导航，车还在主路上直着走。",
    10: "再抬头时，窗外又是刚才那排路灯。",
    11: "前排的人也醒了，却没人问司机。",
    12: "玻璃反光里，多出了一排空座位。",
    13: "可我回头看，最后一排明明坐着人。",
    14: "他们都低着头，像在等同一站。",
    15: "车里的顶灯开始一盏一盏往后灭。",
    16: "司机第一次开口，让我们别看窗外。",
    17: "下一秒，整辆车停在了那座旧收费站。",
    18: "外面没有路，只有一片没开灯的站房。",
    19: "后视镜里，那排空座位已经坐满了人。",
    20: "天亮后我到家，车票上却多了一站。",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def repo_rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def make_mock_image(path: Path, frame: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    base = (22 + frame * 7) % 180
    image = Image.new("RGB", (1080, 1350), (base, min(220, base + 24), min(235, base + 42)))
    draw = ImageDraw.Draw(image)
    horizon = 430 + (frame % 5) * 42
    draw.rectangle((0, horizon, 1080, 1350), fill=(max(0, base - 12), max(0, base - 4), min(210, base + 12)))
    draw.rectangle((90 + frame * 11 % 420, 250 + frame * 9 % 250, 520 + frame * 13 % 450, 300 + frame * 9 % 250), fill=(220, 220, 220))
    draw.ellipse((730 - frame * 7 % 260, 180 + frame * 5 % 260, 850 - frame * 7 % 260, 300 + frame * 5 % 260), outline=(245, 245, 245), width=8)
    draw.line((80, 1100 - frame * 9, 980, 900 + frame * 6), fill=(245, 245, 245), width=6)
    image.save(path, format="PNG")


def state_doc(ep: Path, current: str) -> dict:
    return {
        "schema_version": 1,
        "tool_version": VERSION,
        "episode_id": "mock-v261-runtime",
        "series": "_tests",
        "title": TITLE,
        "current_state": current,
        "updated_at": episode_performance.now(),
        "history": [{"state": current, "at": episode_performance.now(), "mode": "mock_runtime", "note": "V2.6.1 full mock benchmark"}],
    }


def set_state(ep: Path, source: str, target: str) -> None:
    p = ep / "meta/episode-state.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    data["current_state"] = target
    data["updated_at"] = episode_performance.now()
    data.setdefault("history", []).append({"state": target, "at": data["updated_at"], "mode": "mock_runtime", "note": f"{source}->{target}"})
    write_json(p, data)
    episode_performance.safe_record_state_transition(ep, source, target, data["updated_at"])


def story_gates() -> dict:
    return {
        "schema_version": 1,
        "tool_version": VERSION,
        "episode_id": "mock-v261-runtime",
        "story": {
            "recent5_checked": True,
            "four_locks_diff_count": 3,
            "mechanism_skin_swap_veto": False,
            "task_closed": True,
            "competing_explanations": 2,
            "hook_frames": [1, 4, 7],
            "escalation_frames": [7, 13],
            "climax_frame": 17,
            "payoff_frame": 20,
        },
        "visual_profile": {"id": "M00", "status": "passed"},
        "visual": {
            "admission_frames": [1, 7, 13, 20],
            "authenticity_card": {"status": "passed"},
            "continuity": {
                "required": ["location", "protagonist", "weather_time"],
                "anchors": {
                    "protagonist": "二十多岁普通年轻男性，返乡乘夜班大巴",
                    "location": "中国县城外夜间公路与废弃收费站",
                    "key_prop": "纸质车票",
                    "wardrobe": "普通深色短袖和轻薄外套",
                    "weather_time": "夏末闷热深夜",
                },
            },
            "references": {"status": "passed", "classic_cinema_structure": True},
            "environment_contract": {"status": "passed"},
            "frame_directives": {"status": "passed"},
            "calibration": {"strategy": "1+3", "items": [1, 7, 13, 20]},
        },
        "subtitles": {"required": True, "sound_card_completed": True},
        "locks": {"edit_mode": "none", "assets": []},
        "reviews": {
            "story": "passed",
            "authenticity": "passed",
            "continuity": "passed",
            "visual_admission": "passed",
            "subtitle": "passed",
            "production": "passed",
            "recommendation_fit": "passed",
            "publish": "passed",
        },
    }


def release_manifest(ep: Path) -> dict:
    return {
        "schema_version": 1,
        "tool_version": VERSION,
        "episode": {
            "id": "mock-v261-runtime",
            "series": "_tests",
            "title": TITLE,
            "format": "douyin_photo_carousel",
            "aspect_ratio": "4:5",
        },
        "release": {
            "version": "MOCK-V1",
            "body_frame_count": 20,
            "publish_dir": repo_rel(ep / "production/publish"),
            "body_glob": "[0-9][0-9].png",
            "cover_path": repo_rel(ep / "production/cover.png"),
            "contact_sheet_path": None,
        },
        "artifacts": {
            "story": repo_rel(ep / "docs/story.md"),
            "storyboard": repo_rel(ep / "docs/storyboard.md"),
            "visual_spec": repo_rel(ep / "docs/visual-spec.md"),
            "captions": repo_rel(ep / "docs/subtitles.yaml"),
            "publish_copy": repo_rel(ep / "docs/publish-copy.md"),
            "production_review": repo_rel(ep / "docs/production-review.md"),
            "propagation_card": repo_rel(ep / "docs/propagation-card.md"),
        },
        "quality": {
            "production_gate": "pass",
            "propagation_score": 9.0,
            "s_min_score": 8.6,
            "propagation_decision": "strong",
            "publish_decision": "go",
            "decision_note": "mock benchmark pass",
        },
        "publication": {
            "platform": "douyin",
            "actual_title": TITLE,
            "description": "一个普通年轻人深夜坐大巴返乡，途中经过一座地图上不存在的旧收费站。AI生成剧情内容，故事为虚构创作。",
            "topics": ["AI剧情", "返乡", "怪谈"],
            "pinned_comment": "如果是你，你会在第几站下车？",
            "published_at": None,
            "timing_window": None,
            "post_url": None,
        },
        "data_review": {"report_path": "reports/数据验收报告.md", "completed_checkpoints": []},
    }


def run_stage(ep: Path, name: str, fn):
    run_id = episode_performance.begin_stage(ep, name, source="v261_full_mock_pipeline")
    t0 = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - t0
    episode_performance.end_stage(ep, name, run_id, status="PASS", metadata={"mock_external_capabilities": True, "measured_seconds": round(elapsed, 6)})
    return elapsed, result


def run() -> dict:
    base = ROOT / "episodes" / "_tests"
    base.mkdir(parents=True, exist_ok=True)
    chunk_calls: list[list[str]] = []
    reuse_chunk_calls: list[list[str]] = []

    with tempfile.TemporaryDirectory(prefix="v261-full-mock-", dir=base) as td:
        ep = Path(td)
        (ep / "meta").mkdir(parents=True, exist_ok=True)
        write_json(ep / "meta/episode-state.json", state_doc(ep, "IDEA_LOCKED"))
        episode_performance.safe_start_episode(ep, source="v261_full_mock_pipeline")

        timings: dict[str, float] = {}

        def creative_story():
            write_text(ep / "docs/story.md", """# 凌晨一点，返乡大巴多停了一站\n\n主角是二十多岁的普通年轻人，夏末深夜坐大巴回老家。异常不靠调查，而是发生在一次普通返乡途中：后视镜、车窗反光、重复路灯和一座地图上不存在的旧收费站逐步出现。高潮是大巴真正停进旧收费站；结尾只留下多出来的一站车票，不解释真相。\n""")
            write_json(ep / "meta/story-gates.json", story_gates())
            write_json(ep / "meta/episode-fingerprint.json", {
                "episode_id": "mock-v261-runtime",
                "title": TITLE,
                "dimensions": {
                    "core_anomaly_mechanism": "返乡夜班大巴重复进入不存在的旧收费站",
                    "story_engine": "普通返乡途中逐步现实裂缝",
                    "entry_mode": "夜间返乡",
                    "anomaly_carrier": "后视镜与车窗反光",
                    "primary_visual_space": "县城外夜间公路与大巴车厢",
                    "middle_escalation": "导航与窗外道路开始不一致",
                    "climax_form": "车辆停进现实中不存在的旧收费站",
                    "relationship": "陌生乘客共同沉默",
                    "reality_residue": "车票多出一站",
                },
            })

        timings["CREATIVE_STORY"], _ = run_stage(ep, "CREATIVE_STORY", creative_story)
        set_state(ep, "IDEA_LOCKED", "STORYBOARD_LOCKED")

        def preimage_compile():
            rows = []
            for i in range(1, 21):
                scale = "large" if i in {1, 6, 10, 17} else ("close" if i in {4, 12, 19, 20} else "medium")
                anomaly = "reflection/light concealment" if i in {4, 5, 12, 13, 19} else "environmental progression"
                rows.append(f"{i:02d}. {scale} shot | {anomaly} | caption: {CAPTIONS[i]}")
            write_text(ep / "docs/storyboard.md", "# Storyboard\n\n" + "\n".join(rows) + "\n")
            write_text(ep / "docs/visual-spec.md", "真实手机相册感；左中字幕；大中小景别交替；同一机位不重复；夜间 practical lighting；异常优先藏在后视镜、车窗反光和路灯中。\n")
            write_text(ep / "docs/production-review.md", "Mock production review placeholder; deterministic runtime benchmark only.\n")
            write_text(ep / "docs/publish-copy.md", "标题：凌晨一点，返乡大巴多停了一站\n简介：一个普通年轻人深夜返乡，途中经过一座地图上不存在的旧收费站。\n")
            write_text(ep / "docs/propagation-card.md", "封面钩子：凌晨一点，这辆返乡大巴多停了一站。\n")
            yaml = ["voice_card:", "  tone: 口语化、克制、第一人称", "frames:"]
            yaml.extend([f"  {i}: {json.dumps(CAPTIONS[i], ensure_ascii=False)}" for i in range(1, 21)])
            yaml.append("silent_frames: []")
            write_text(ep / "docs/subtitles.yaml", "\n".join(yaml) + "\n")
            write_json(ep / "meta/release-manifest.json", release_manifest(ep))

        timings["PREIMAGE_COMPILE"], _ = run_stage(ep, "PREIMAGE_COMPILE", preimage_compile)

        ledger = {
            "schema_version": 1,
            "engine_version": "mock-v261",
            "canvas": {"aspect_ratio": "4:5", "width": 1080, "height": 1350, "source": "mock"},
            "policy": {"image_quality": "mock", "normalize_enabled": False},
            "asset_roots": {"approved": "media/approved", "publish": "production/publish"},
            "frames": {},
        }

        def generate_frame(frame: int, scope: str, status: str):
            path = ep / "media/approved" / f"{frame:02d}.png"
            started_at = episode_performance.now()
            t0 = time.perf_counter()
            make_mock_image(path, frame)
            elapsed = time.perf_counter() - t0
            ended_at = episode_performance.now()
            sha = sha256_file(path)
            ledger["frames"][f"{frame:02d}"] = {
                "number": frame,
                "status": status,
                "content_repairs_used": 0,
                "technical_failures": [],
                "attempts": [],
                "approved_asset": {
                    "path": repo_rel(path),
                    "sha256": sha,
                    "width": 1080,
                    "height": 1350,
                    "source_sha256": sha,
                },
                "lock": {"sha256": sha, "reason": "mock synthetic pixel pass"} if status == "LOCKED" else None,
            }
            episode_performance.safe_record_image_attempt(
                ep,
                frame=frame,
                scope=scope,
                kind="original",
                status="success",
                model="MOCK_SYNTHETIC_PNG",
                attempt=1,
                started_at=started_at,
                ended_at=ended_at,
                elapsed_seconds=elapsed,
                queue_item_id=f"mock-{scope}-{frame:02d}",
            )

        def visual_lock():
            for frame in sorted(VISUAL_LOCK_FRAMES):
                generate_frame(frame, "visual_lock", "LOCKED")
            write_json(ep / "meta/production-ledger.json", ledger)
            write_json(ep / "meta/visual-lock-plan.json", {"schema_version": 1, "strategy": "1+3", "frames": sorted(VISUAL_LOCK_FRAMES), "summary": {"passed": True}})

        timings["VISUAL_LOCK"], _ = run_stage(ep, "VISUAL_LOCK", visual_lock)
        set_state(ep, "STORYBOARD_LOCKED", "VISUAL_CALIBRATED")

        def production():
            for frame in range(1, 21):
                if frame in VISUAL_LOCK_FRAMES:
                    continue
                generate_frame(frame, "production", "PASSED")
            write_json(ep / "meta/production-ledger.json", ledger)
            write_json(ep / "meta/frame-scout-summary.json", {"schema_version": 1, "summary": {"passed": True}, "mocked_visual_critic": True})

        timings["PRODUCTION"], _ = run_stage(ep, "PRODUCTION", production)
        set_state(ep, "VISUAL_CALIBRATED", "PRODUCTION_PASSED")

        def fake_chunk(rows, store):
            store.append([r["frame"] for r in rows])
            return {
                "frames": [
                    {
                        "frame": r["frame"],
                        "supported": True,
                        "subtitle_unobstructed": True,
                        "notes": "mock critic pass; actual SHA/layout pipeline exercised",
                    }
                    for r in rows
                ],
                "critic_provenance": runtime_provenance.build_critic_provenance("WORK", attempt=1),
            }

        release_counts: dict[str, int] = {}
        release_subseconds: dict[str, float] = {}
        snapshot_verify_errors: list[str] = []
        release_verify_rc = None

        def release_stage():
            nonlocal release_verify_rc, snapshot_verify_errors
            sub_t0 = time.perf_counter()
            subtitle_source = ep / "docs/subtitles.yaml"
            audit = text_audit.audit(text_audit.parse_simple_subtitles_yaml(subtitle_source), subtitle_source)
            if (audit.get("summary") or {}).get("passed") is not True:
                raise AssertionError(f"text audit failed: {audit}")
            write_json(ep / "meta/text-audit.json", audit)
            release_subseconds["text_audit"] = time.perf_counter() - sub_t0

            sub_t0 = time.perf_counter()
            subtitle_layout.render_all(ep)
            shutil.copyfile(ep / "production/publish/01.png", ep / "production/cover.png")
            release_subseconds["subtitle_render_20"] = time.perf_counter() - sub_t0

            sub_t0 = time.perf_counter()
            with mock.patch.object(caption_image_audit, "_run_chunk", side_effect=lambda _ep, rows, texts, codex_raw, timeout, index: fake_chunk(rows, chunk_calls)):
                ok, _ = caption_image_audit.ensure(ep, codex_raw="MOCK", timeout=30)
            if not ok:
                raise AssertionError("caption image audit mock did not pass")
            caption_errors = caption_image_audit.verify(ep)
            if caption_errors:
                raise AssertionError("caption image audit verify failed: " + "; ".join(caption_errors))
            release_subseconds["caption_audit_20_mock_critic"] = time.perf_counter() - sub_t0

            sub_t0 = time.perf_counter()
            frames = caption_image_audit.base.frame_records(ep, require_files=True)
            write_json(ep / "meta/visual-final-freeze.json", {
                "schema_version": 1,
                "module_version": "mock-v261",
                "authority": "visual evidence only; mock benchmark",
                "frames": [{"frame": r["frame"], "asset_path": r["path_rel"], "asset_sha256": r["sha256"]} for r in frames],
                "summary": {"passed": True, "frame_count": len(frames)},
            })

            write_json(ep / "meta/publish-compliance.json", {
                "schema_version": 1,
                "story_os_version": VERSION,
                "ai_generated": True,
                "platform_ai_label_required": True,
                "platform_ai_label_method": "douyin_platform_declaration",
                "fiction_context_notice_required": True,
                "fiction_context_notice": "AI生成剧情内容；故事为虚构创作，真实地点仅作为故事背景。",
                "user_must_confirm_label_at_publish_time": True,
            })
            release_subseconds["freeze_and_compliance"] = time.perf_counter() - sub_t0

            sub_t0 = time.perf_counter()
            hashes = release_preflight.release_hashes(ep)
            review = {
                "schema_version": 1,
                "story_os_version": VERSION,
                "artifacts": hashes,
                "critic_provenance": runtime_provenance.build_critic_provenance("WORK", attempt=1),
                "release_checks": {k: True for k in release_preflight.RELEASE_CHECKS},
                "governance_checks": {k: True for k in release_preflight.GOV_CHECKS},
                "issue_codes": [],
                "notes": ["mock semantic critic pass"],
                "summary": {"passed": True},
            }
            write_json(ep / release_preflight.RELEASE_REVIEW_REL, review)
            semantic_errors = release_preflight.validate_release_review(ep, review)
            if semantic_errors:
                raise AssertionError("release semantic validation failed: " + "; ".join(semantic_errors))

            rows = release_preflight.release_artifacts(ep)
            review_rows = release_preflight.release_review_rows(release_preflight.release_hashes(ep))
            release_counts.update({
                "release_artifact_roles": len(rows),
                "release_review_roles": len(review_rows),
                "release_review_image_roles": sum(1 for k in review_rows if k in {"cover", "body01", "body02", "body03", "climax", "payoff"}),
            })
            release_subseconds["release_hash_and_semantic"] = time.perf_counter() - sub_t0

            sub_t0 = time.perf_counter()
            with mock.patch.object(release_preflight, "verify_recent5_evidence", return_value=[]), \
                 mock.patch.object(release_preflight, "verify_series_lock", return_value=[]), \
                 mock.patch.object(release_preflight.visual_final_freeze, "verify", return_value=[]):
                release_verify_rc = release_preflight.cmd_verify(type("Args", (), {"episode_dir": str(ep)})())
            if release_verify_rc != 0:
                raise AssertionError(f"release verify rc={release_verify_rc}")
            release_subseconds["release_verify"] = time.perf_counter() - sub_t0

            sub_t0 = time.perf_counter()
            with mock.patch.object(final_candidate_snapshot.frame_semantic_review, "verify_episode", return_value=[]), \
                 mock.patch.object(final_candidate_snapshot.visual_final_freeze, "verify", return_value=[]), \
                 mock.patch.object(final_candidate_snapshot.fast_frame_scout, "audit", return_value=[]), \
                 mock.patch.object(final_candidate_snapshot.character_visual_contract, "pixel_master_required", return_value=False):
                snap = final_candidate_snapshot.build(ep)
                snapshot_verify_errors = final_candidate_snapshot.verify(ep)
                if snapshot_verify_errors:
                    raise AssertionError("final snapshot verify failed: " + "; ".join(snapshot_verify_errors))
                if not snap.get("snapshot_sha256"):
                    raise AssertionError("final snapshot SHA missing")
            release_subseconds["final_snapshot_build_verify"] = time.perf_counter() - sub_t0

        timings["RELEASE"], _ = run_stage(ep, "RELEASE", release_stage)
        # Keep this integration benchmark isolated: PUBLISH_READY finalization normally
        # rebuilds the repository-wide performance report, which is not part of the mock fixture.
        with mock.patch.object(episode_performance, "rebuild_report", return_value={}):
            set_state(ep, "PRODUCTION_PASSED", "PUBLISH_READY")

        t0 = time.perf_counter()
        dirty2, *_ = caption_image_audit.dirty_frames(ep)
        with mock.patch.object(caption_image_audit, "_run_chunk", side_effect=lambda _ep, rows, texts, codex_raw, timeout, index: fake_chunk(rows, reuse_chunk_calls)):
            reuse_ok, _ = caption_image_audit.ensure(ep, codex_raw="MOCK", timeout=30)
        reuse_caption_seconds = time.perf_counter() - t0
        if dirty2:
            raise AssertionError(f"reuse dirty frames should be 0, got {len(dirty2)}")
        if reuse_chunk_calls:
            raise AssertionError(f"reuse must not invoke critic chunks: {reuse_chunk_calls}")
        if not reuse_ok:
            raise AssertionError("reuse ensure should stay pass")

        summary = episode_performance.episode_summary(ep)
        total_measured = sum(timings.values())
        result = {
            "schema_version": 1,
            "story_os_version": VERSION,
            "mock_story": {
                "title": TITLE,
                "frames": 20,
                "visual_lock_strategy": "1+3",
                "visual_lock_frames": sorted(VISUAL_LOCK_FRAMES),
                "image_provider": "MOCK_SYNTHETIC_PNG",
                "critic_provider": "MOCK_PASS",
            },
            "stage_seconds": {k: round(v, 6) for k, v in timings.items()},
            "sum_stage_seconds": round(total_measured, 6),
            "episode_performance": summary,
            "caption_audit": {
                "chunk_size": caption_image_audit.CHUNK,
                "chunk_calls": chunk_calls,
                "chunk_count": len(chunk_calls),
                "reuse_dirty_frames": len(dirty2),
                "reuse_chunk_calls": reuse_chunk_calls,
                "reuse_seconds": round(reuse_caption_seconds, 6),
            },
            "release": {
                **release_counts,
                "substep_seconds": {k: round(v, 6) for k, v in release_subseconds.items()},
                "verify_rc": release_verify_rc,
                "snapshot_verify_errors": snapshot_verify_errors,
            },
            "assertions": {
                "publish_ready": True,
                "all_20_mock_images_generated": len(ledger["frames"]) == 20,
                "caption_chunks_are_5x4": [len(x) for x in chunk_calls] == [5, 5, 5, 5],
                "caption_reuse_is_noop": len(dirty2) == 0 and not reuse_chunk_calls,
                "release_final_critic_uses_6_key_images": release_counts.get("release_review_image_roles") == 6,
                "final_snapshot_verified": not snapshot_verify_errors,
            },
        }
        if not all(result["assertions"].values()):
            raise AssertionError(result["assertions"])
        return result


def main() -> int:
    result = run()
    print("V2.6.1 FULL MOCK PIPELINE PASS")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
