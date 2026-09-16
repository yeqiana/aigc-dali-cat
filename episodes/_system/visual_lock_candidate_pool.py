#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bounded competitive candidates for non-baseline Visual Lock admissions.

This lane is intentionally separate from the ordinary one-shot content repair.
It activates only when a Visual Lock admission frame has already consumed its
ordinary repair and the latest four-admission Codex Vision review still fails.
The candidate does not alter Story/Frame Contract or episode stage; only a later
Codex Vision PASS can admit it into Visual Lock.
"""
from __future__ import annotations

from pathlib import Path

import image_model_policy
import story_json
import storyos_config
import visual_lock_admission_state

QUEUE_REL = Path("meta/production-queue.json")
LEDGER_REL = Path("meta/production-ledger.json")
REVIEW_REL = Path("meta/visual-profile-review.json")
PLAN_REL = Path("meta/visual-lock-plan.json")


def _read(path: Path) -> dict:
    data = story_json.read_json(path, default={})
    return data if isinstance(data, dict) else {}


def enabled() -> bool:
    cfg = storyos_config.load_config()
    return storyos_config.get_path(cfg, "production.visual_lock_admission_pool.enabled") is True


def max_additional_candidates_per_frame() -> int:
    cfg = storyos_config.load_config()
    return int(storyos_config.get_path(
        cfg, "production.visual_lock_admission_pool.max_additional_candidates_per_frame", 0
    ) or 0)


def baseline_frame(ep: Path) -> int:
    plan = _read(Path(ep) / PLAN_REL)
    row = next((x for x in (plan.get("items") or [])
                if isinstance(x, dict) and x.get("role") == "ordinary_baseline"), None)
    if not row:
        raise RuntimeError("ordinary_baseline missing from visual-lock-plan")
    return int(row["frame"])


def failed_rows(ep: Path) -> list[dict]:
    review = _read(Path(ep) / REVIEW_REL)
    rows = []
    for row in review.get("calibration") or []:
        if not isinstance(row, dict):
            continue
        if visual_lock_admission_state.valid_pass_for_gate_row(ep, row):
            continue
        checks = row.get("checks") or {}
        failed = row.get("issues") not in ([], None) or any(value is not True for value in checks.values())
        if failed:
            rows.append(row)
    return rows


def candidate_items(ep: Path, frame: int) -> list[dict]:
    q = _read(Path(ep) / QUEUE_REL)
    return [
        row for row in (q.get("items") or [])
        if isinstance(row, dict)
        and int(row.get("frame") or -1) == int(frame)
        and row.get("kind") == "baseline_candidate"
        and str(row.get("capture_id") or "").startswith("visual-lock-candidate-")
    ]


def successful_slots(ep: Path, frame: int) -> int:
    return sum(bool(row.get("output_path")) for row in candidate_items(ep, frame))


def active_candidate(ep: Path, frame: int) -> dict | None:
    rows = [
        row for row in candidate_items(ep, frame)
        if row.get("status") in {"queued", "running", "tech_failed", "external_blocked", "interrupted_unknown"}
    ]
    return rows[-1] if rows else None


def _ledger_frame(ep: Path, frame: int) -> dict:
    ledger = _read(Path(ep) / LEDGER_REL)
    row = (ledger.get("frames") or {}).get(f"{int(frame):02d}") or {}
    return row if isinstance(row, dict) else {}


def prepareable_frames(ep: Path) -> list[int]:
    ep = Path(ep).resolve()
    if not enabled():
        return []
    try:
        base = baseline_frame(ep)
    except RuntimeError:
        return []
    maximum = max_additional_candidates_per_frame()
    out = []
    for row in failed_rows(ep):
        try:
            frame = int(row.get("frame"))
        except Exception:
            continue
        if frame == base:
            continue
        ledger = _ledger_frame(ep, frame)
        if str(ledger.get("status") or "") != "NEEDS_USER":
            continue
        if active_candidate(ep, frame) is not None:
            continue
        if successful_slots(ep, frame) >= maximum:
            continue
        out.append(frame)
    return sorted(set(out))


def exhausted_frames(ep: Path) -> list[int]:
    ep = Path(ep).resolve()
    if not enabled():
        return []
    try:
        base = baseline_frame(ep)
    except RuntimeError:
        return []
    maximum = max_additional_candidates_per_frame()
    out = []
    for row in failed_rows(ep):
        try:
            frame = int(row.get("frame"))
        except Exception:
            continue
        if frame == base:
            continue
        ledger = _ledger_frame(ep, frame)
        if str(ledger.get("status") or "") != "NEEDS_USER":
            continue
        if active_candidate(ep, frame) is not None:
            continue
        if successful_slots(ep, frame) >= maximum:
            out.append(frame)
    return sorted(set(out))


def _row_for_frame(ep: Path, frame: int) -> dict:
    return next((r for r in failed_rows(ep) if int(r.get("frame") or -1) == int(frame)), {})


def _compact(values: list[str], limit: int = 3) -> str:
    out: list[str] = []
    for raw in values:
        text = str(raw or "").replace("\n", " ").strip()
        if not text or text in out:
            continue
        out.append(text[:22])
        if len(out) >= limit:
            break
    return "、".join(out)


def candidate_prompt(ep: Path, frame: int, slot: int) -> str:
    row = _row_for_frame(ep, frame)
    checks = row.get("checks") or {}
    findings = [str(k) for k, value in checks.items() if value is not True]
    findings.extend(str(x) for x in (row.get("issues") or []))
    focus = _compact(findings) or "reality_first、unposed_capture、not_cinematic"
    role = str(row.get("role") or "visual_lock_admission")
    variants = {
        "worst_capture_condition": (
            "真实逆光/遮挡/走动模糊，脸可偏暗或局部过曝；禁止金色日落、HDR、整齐站位和旅游宣传构图。"
        ),
        "first_major_anomaly": (
            "走路随手拍，异常必须在普通生活画面里一眼可辨；允许边缘遮挡和非完美构图，但异常核心形态/动作/反差必须清楚。禁止大全景、极深景深和海报式奇观。"
        ),
        "first_major_visual_contrast": (
            "走路随手拍，首个视觉反差必须在普通生活画面里清楚可辨；允许局部遮挡，但关键反差不能被屋檐/行人/水汽完全遮没。禁止大全景、极深景深和海报式奇观。"
        ),
        "high_impact_admission": (
            "保留大尺度但像偶然记录：主体偏心、前景遮挡/裁切、曝光不完美，人物仍做日常动作；禁止居中落日和海报构图。"
        ),
    }
    fallback = "手机随手拍优先：动作不中断、轻微偏斜/遮挡、自然曝光与真实皮肤；禁止宣传片、电影海报、HDR和摆拍。"
    variant = variants.get(role, fallback)
    if slot >= 2:
        variant += " 第二候选再降精修感，增加生活杂物与非完美瞬间。"
    text = (
        f"VL候选{slot} F{int(frame):02d} 角色={role}。保持Frame Contract、身份、服装、事件，不改剧情。"
        f"修正：{focus}。{variant}"
    )
    while len(text) > 245 or len(text.encode("utf-8")) > 850:
        focus = focus[:-8] if len(focus) > 18 else "写实、非摆拍、非电影化"
        text = (
            f"Visual Lock候选{slot} Frame{int(frame):02d}。保持Frame Contract与身份。针对：{focus}。{variant}"
        )
        if len(focus) <= 18:
            break
    return text


def enqueue_frame(ep: Path, frame: int) -> dict:
    ep = Path(ep).resolve()
    ledger = _ledger_frame(ep, frame)
    if str(ledger.get("status") or "") != "NEEDS_USER":
        return {"status": "NOT_READY", "frame": frame, "ledger_status": ledger.get("status")}
    active = active_candidate(ep, frame)
    if active:
        return {"status": "REUSED", "frame": frame, "queue_item_id": active.get("id"), "queue_status": active.get("status")}
    used = successful_slots(ep, frame)
    maximum = max_additional_candidates_per_frame()
    if used >= maximum:
        return {"status": "EXHAUSTED", "frame": frame, "used": used, "max": maximum}
    slot = used + 1
    prompt_dir = ep / "prompts" / "visual-lock-candidates"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = prompt_dir / f"{int(frame):02d}-candidate-{slot}.txt"
    prompt_path.write_text(candidate_prompt(ep, frame, slot) + "\n", encoding="utf-8", newline="\n")
    import image_scheduler
    policy = image_model_policy.for_episode(ep)
    refs = image_scheduler.contract_references(ep, frame, scope="repair")
    item = image_scheduler.add_item(
        ep,
        frame=int(frame),
        kind="baseline_candidate",
        prompt_file=prompt_path,
        scope="repair",
        references=refs,
        capture_id=f"visual-lock-candidate-{int(frame):02d}-{slot:02d}",
        model=policy["model"],
        quality=policy["quality"],
        strict_model=bool(policy.get("strict_model")),
        depends_on=[baseline_frame(ep)],
        replace=True,
    )
    return {
        "status": "PASS",
        "frame": int(frame),
        "slot": slot,
        "max": maximum,
        "queue_item_id": item.get("id"),
        "prompt_file": item.get("prompt_file"),
        "content_repairs_used": int(ledger.get("content_repairs_used") or 0),
    }


def enqueue_ready(ep: Path) -> dict:
    frames = prepareable_frames(ep)
    rows = [enqueue_frame(ep, frame) for frame in frames]
    return {"status": "PASS" if rows else "REUSED", "frames": frames, "candidates": rows}


def review_attempt(ep: Path) -> int:
    base = 2
    slots = 0
    for row in failed_rows(ep):
        try:
            frame = int(row.get("frame"))
        except Exception:
            continue
        if frame == baseline_frame(ep):
            continue
        slots = max(slots, successful_slots(ep, frame))
    return base + slots


def self_test() -> None:
    assert max_additional_candidates_per_frame() >= 0
    print("VISUAL LOCK CANDIDATE POOL SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
