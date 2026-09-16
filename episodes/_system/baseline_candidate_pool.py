#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bounded Visual Lock ordinary-baseline candidate competition.

This is a bootstrap execution lane, not a second state machine and not an
ordinary content-repair lane. It activates only after the ordinary baseline
repair budget has been exhausted and the baseline frame is NEEDS_USER.

Authority stays where it already lives:
- episode-state.json remains the only stage authority;
- Production Ledger records generation attempts;
- Visual Lock baseline Codex Vision decides PASS/FAIL;
- the first PASS becomes the provisional Pixel Master.
"""
from __future__ import annotations

from pathlib import Path

import image_model_policy
import production_queue_store
import story_json
import storyos_config

ROOT = Path(__file__).resolve().parents[2]
LEDGER_REL = Path("meta/production-ledger.json")
REVIEW_REL = Path("meta/visual-lock-baseline-review.json")
PLAN_REL = Path("meta/visual-lock-plan.json")


def _read(path: Path) -> dict:
    data = story_json.read_json(path, default={})
    return data if isinstance(data, dict) else {}


def _baseline_frame(ep: Path) -> int:
    plan = _read(Path(ep) / PLAN_REL)
    row = next((x for x in (plan.get("items") or [])
                if isinstance(x, dict) and x.get("role") == "ordinary_baseline"), None)
    if not row:
        raise RuntimeError("ordinary_baseline missing from visual-lock-plan")
    return int(row["frame"])


def enabled() -> bool:
    cfg = storyos_config.load_config()
    return storyos_config.get_path(cfg, "production.visual_lock_baseline_pool.enabled") is True


def max_additional_candidates() -> int:
    cfg = storyos_config.load_config()
    return int(storyos_config.get_path(
        cfg, "production.visual_lock_baseline_pool.max_additional_candidates", 0
    ) or 0)


def _ledger_frame(ep: Path, frame: int) -> dict:
    ledger = _read(Path(ep) / LEDGER_REL)
    row = (ledger.get("frames") or {}).get(f"{int(frame):02d}") or {}
    return row if isinstance(row, dict) else {}


def candidate_items(ep: Path) -> list[dict]:
    frame = _baseline_frame(ep)
    q = _read(production_queue_store.read_path(Path(ep)))
    return [
        row for row in (q.get("items") or [])
        if isinstance(row, dict)
        and int(row.get("frame") or -1) == frame
        and row.get("kind") == "baseline_candidate"
        and row.get("scope") == "baseline_candidate"
    ]


def successful_candidate_slots(ep: Path) -> int:
    """Count content candidates, not technical attempts.

    A queue item consumes one pool slot only after a real image was committed.
    Technical failures retry the same queue item and do not consume another slot.
    """
    return sum(
        bool(row.get("output_path"))
        for row in candidate_items(Path(ep).resolve())
    )


def active_candidate(ep: Path) -> dict | None:
    active = [
        row for row in candidate_items(Path(ep).resolve())
        if row.get("status") in {"queued", "running", "tech_failed"}
    ]
    return active[-1] if active else None


def review_attempt(ep: Path) -> int:
    """Monotonic pixel-review attempt based only on real generated candidates."""
    frame = _baseline_frame(ep)
    attempts = _ledger_frame(Path(ep).resolve(), frame).get("attempts") or []
    successful = sum(
        isinstance(row, dict) and row.get("result") == "success" and bool(row.get("candidate"))
        for row in attempts
    )
    return max(1, int(successful))


def _failed_findings(ep: Path) -> list[str]:
    review = _read(Path(ep) / REVIEW_REL)
    findings = [
        str(key) for key, value in (review.get("checks") or {}).items()
        if str(value or "").upper() != "PASS"
    ]
    note = str(review.get("note") or "").strip()
    if note:
        findings.append(note[:120])
    return findings


def _compact_findings(values: list[str]) -> str:
    out: list[str] = []
    for raw in values:
        text = str(raw or "").replace("\n", " ").strip()
        if not text or text in out:
            continue
        out.append(text[:34])
        if len(out) >= 4:
            break
    return "、".join(out) if out else "reality_first、unposed_capture、not_cinematic"


def candidate_prompt(frame: int, slot: int, findings: list[str]) -> str:
    focus = _compact_findings(findings)
    variants = {
        1: (
            "P01前置自拍更近脸，朋友保持自然聊天/侧看，不要三个人齐刷刷看镜头；"
            "背景以普通天界屋檐、台阶、街巷为主，云海仙城只占少量背景；普通晨光，无电影金光。"
        ),
        2: (
            "像刚出门顺手按下快门：轻微构图偏斜和自然裁切，P01表情放松，朋友处在走动/说话动作中；"
            "弱化悬浮奇观和精修感，保留真实皮肤、手机曝光与生活杂物，禁止海报式布光。"
        ),
    }
    variant = variants.get(slot, variants[2])
    text = (
        f"Baseline候选{slot} Frame{frame:02d}。严格保持当前Frame Contract与天界日常故事，不解释规则、不改人物关系。"
        f"针对上轮失败：{focus}。{variant}"
    )
    while len(text) > 250 or len(text.encode("utf-8")) > 860:
        focus = focus[:-6] if len(focus) > 12 else "写实、非摆拍、非电影化"
        text = (
            f"Baseline候选{slot} Frame{frame:02d}。保持Frame Contract与故事。针对：{focus}。{variant}"
        )
        if len(focus) <= 12:
            break
    return text


def can_prepare(ep: Path) -> bool:
    ep = Path(ep).resolve()
    if not enabled() or max_additional_candidates() <= 0:
        return False
    frame = _baseline_frame(ep)
    if str(_ledger_frame(ep, frame).get("status") or "") != "NEEDS_USER":
        return False
    if active_candidate(ep) is not None:
        return False
    return successful_candidate_slots(ep) < max_additional_candidates()


def exhausted(ep: Path) -> bool:
    ep = Path(ep).resolve()
    if not enabled():
        return True
    return successful_candidate_slots(ep) >= max_additional_candidates() and active_candidate(ep) is None


def enqueue_next(ep: Path) -> dict:
    ep = Path(ep).resolve()
    frame = _baseline_frame(ep)
    ledger = _ledger_frame(ep, frame)
    if str(ledger.get("status") or "") != "NEEDS_USER":
        return {"status": "NOT_READY", "frame": frame, "ledger_status": ledger.get("status")}
    active = active_candidate(ep)
    if active is not None:
        return {"status": "REUSED", "frame": frame, "queue_item_id": active.get("id"), "queue_status": active.get("status")}
    used = successful_candidate_slots(ep)
    maximum = max_additional_candidates()
    if used >= maximum:
        return {"status": "EXHAUSTED", "frame": frame, "used": used, "max": maximum}

    slot = used + 1
    prompt_dir = ep / "prompts" / "baseline-candidates"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = prompt_dir / f"{frame:02d}-candidate-{slot}.txt"
    prompt_path.write_text(candidate_prompt(frame, slot, _failed_findings(ep)) + "\n", encoding="utf-8", newline="\n")

    # Local import keeps this helper out of image_scheduler's import cycle.
    import image_scheduler

    policy = image_model_policy.for_episode(ep)
    refs = image_scheduler.contract_references(ep, frame, scope="visual_lock")
    item = image_scheduler.add_item(
        ep,
        frame=frame,
        kind="baseline_candidate",
        prompt_file=prompt_path,
        scope="baseline_candidate",
        references=refs,
        capture_id=f"visual-baseline-candidate-{slot:02d}",
        model=policy["model"],
        quality=policy["quality"],
        strict_model=bool(policy.get("strict_model")),
        depends_on=[],
        replace=True,
    )
    return {
        "status": "PASS",
        "action": "PREPARE_BASELINE_CANDIDATE",
        "frame": frame,
        "slot": slot,
        "max": maximum,
        "queue_item_id": item.get("id"),
        "prompt_file": item.get("prompt_file"),
        "content_repairs_used": int(ledger.get("content_repairs_used") or 0),
    }


def self_test() -> None:
    for slot in (1, 2):
        text = candidate_prompt(1, slot, ["visual_profile_match", "reality_first", "not_cinematic"])
        assert len(text) <= 260
        assert len(text.encode("utf-8")) <= 900
        assert "Frame01" in text and "Baseline候选" in text
    print("BASELINE CANDIDATE POOL SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
