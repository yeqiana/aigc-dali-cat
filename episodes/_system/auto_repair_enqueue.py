#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bounded automatic content-repair enqueue for Story OS image lanes.

This module does not judge pixels and never advances gates/stages. It only turns
an already-verified content failure into the repository's existing one-shot
repair transaction:

ready candidate -> CONTENT_FAILED -> REPAIR_AUTHORIZED -> queued repair item

The Production Ledger remains the repair-budget authority; Image Scheduler
remains the execution authority.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import image_model_policy
import ledger_call
import story_json

ROOT = Path(__file__).resolve().parents[2]
QUEUE_REL = Path("meta/production-queue.json")
LEDGER_REL = Path("meta/production-ledger.json")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def _read(path: Path) -> dict:
    data = story_json.read_json(path, default={})
    return data if isinstance(data, dict) else {}


def _ledger_frame(ep: Path, frame: int) -> dict:
    data = _read(ep / LEDGER_REL)
    rows = data.get("frames") or {}
    row = rows.get(f"{int(frame):02d}") or rows.get(str(int(frame))) or {}
    return row if isinstance(row, dict) else {}


def _queue_items(ep: Path, frame: int) -> list[dict]:
    q = _read(ep / QUEUE_REL)
    return [
        row for row in (q.get("items") or [])
        if isinstance(row, dict) and int(row.get("frame") or -1) == int(frame)
    ]


def repair_pending(ep: Path, frame: int) -> bool:
    return any(
        row.get("kind") == "repair" and row.get("status") in {"queued", "running", "tech_failed"}
        for row in _queue_items(Path(ep).resolve(), frame)
    )


def generated_repair(ep: Path, frame: int) -> bool:
    return any(
        row.get("kind") == "repair" and row.get("status") == "generated"
        for row in _queue_items(Path(ep).resolve(), frame)
    )


def enqueue_marked_repairs(ep: Path) -> dict:
    """Convert queue ``scout_repair`` markers into executable repair items.

    Production Batch Review/Fast Scout already own the pixel decision. This
    helper only bridges their marker into the existing Ledger + Scheduler
    repair transaction so ``REPAIR_FAILED_IMAGES`` cannot become an empty loop.
    """
    ep = Path(ep).resolve()
    q = _read(ep / QUEUE_REL)
    marked = [row for row in (q.get("items") or []) if isinstance(row, dict) and row.get("status") == "scout_repair"]
    results = []
    supersede_ids: set[str] = set()
    for row in marked:
        frame = int(row.get("frame") or 0)
        if frame <= 0:
            continue
        findings: list[str] = []
        for source in (row.get("work_batch_review"), row.get("scout"), row.get("repair_assessment")):
            if not isinstance(source, dict):
                continue
            findings.extend(str(x) for x in (source.get("issue_codes") or []) if str(x))
            if source.get("reason"):
                findings.append(str(source.get("reason")))
            if source.get("notes"):
                findings.append(str(source.get("notes")))
        result = enqueue(
            ep,
            frame=frame,
            findings=findings,
            source="PRODUCTION_REVIEW",
            review_note="Production actual-pixel review authorized content repair",
        )
        results.append(result)
        if result.get("status") in {"REPAIR_ENQUEUED", "REPAIR_ALREADY_PENDING"}:
            supersede_ids.add(str(row.get("id") or ""))
    if supersede_ids:
        latest = _read(ep / QUEUE_REL)
        for row in latest.get("items") or []:
            if str(row.get("id") or "") in supersede_ids and row.get("status") == "scout_repair":
                row["status"] = "superseded"
                row["superseded_reason"] = "bounded content repair enqueued"
        story_json.write_json(ep / QUEUE_REL, latest)
    return {"marked": len(marked), "results": results, "repair_items_ready": sum(r.get("status") in {"REPAIR_ENQUEUED", "REPAIR_ALREADY_PENDING"} for r in results)}


def authority_refresh_prompt(frame: int) -> str:
    text = (
        f"权威刷新Frame{int(frame):02d}。上游 Visual Profile / World Identity / Frame Contract 已合法更新。"
        "丢弃旧候选的视觉合同语义，严格按当前 Frame Contract 重新生成同一故事帧；不新增剧情、不把权威刷新当内容返修。"
        "保持人物身份与故事连续性，以当前合同中的拍摄者、设备位置、生活动作、环境物理和视觉档案为唯一生成依据。"
    )
    while len(text) > 250 or len(text.encode("utf-8")) > 860:
        text = text.replace("上游 Visual Profile / World Identity / Frame Contract 已合法更新。", "上游权威合同已合法更新。")
        if len(text) <= 250 and len(text.encode("utf-8")) <= 860:
            break
        text = text[:240]
    return text


def enqueue_authority_refresh(ep: Path, frame: int) -> dict:
    ep = Path(ep).resolve()
    frame = int(frame)
    if repair_pending(ep, frame):
        return {"status": "AUTHORITY_REFRESH_ALREADY_PENDING", "frame": frame}
    ledger = _ledger_frame(ep, frame)
    if str(ledger.get("status") or "") != "AUTHORITY_REFRESH_AUTHORIZED":
        return {"status": "NOT_AUTHORITY_REFRESHABLE", "frame": frame, "ledger_status": ledger.get("status")}
    prompt_dir = ep / "prompts" / "authority-refresh"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = prompt_dir / f"{frame:02d}-authority-refresh.txt"
    prompt_path.write_text(authority_refresh_prompt(frame) + "\n", encoding="utf-8", newline="\n")

    import image_scheduler
    import visual_lock_baseline_gate
    source_item = _source_item(ep, frame)
    policy = image_model_policy.for_episode(ep)
    # Authority refresh of the ordinary baseline bootstraps a new identity master.
    # It must not depend on the stale master that this refresh is replacing.
    try:
        is_baseline = frame == int(visual_lock_baseline_gate.baseline_frame(ep))
    except Exception:
        is_baseline = False
    refs = [] if is_baseline else image_scheduler.contract_references(ep, frame, scope="repair")
    item = image_scheduler.add_item(
        ep,
        frame=frame,
        kind="repair",
        prompt_file=prompt_path,
        scope="repair",
        references=refs,
        capture_id=f"authority-refresh-{frame:02d}",
        model=policy["model"],
        quality=policy["quality"],
        strict_model=bool(policy.get("strict_model")),
        depends_on=[int(x) for x in (source_item.get("depends_on") or [])],
        # Authority refresh is a new SHA-bound transaction under refreshed
        # upstream authority. Historical generated repairs remain audit evidence
        # but must not dedupe the new request; supersede them in the queue.
        replace=True,
    )
    return {
        "status": "AUTHORITY_REFRESH_ENQUEUED",
        "frame": frame,
        "queue_item_id": item.get("id"),
        "prompt_file": item.get("prompt_file"),
        "content_repairs_used": int(ledger.get("content_repairs_used") or 0),
        "at": now(),
    }


def enqueue_authority_refreshes(ep: Path) -> dict:
    ep = Path(ep).resolve()
    ledger = _read(ep / LEDGER_REL)
    frames = sorted(
        int(key) for key, row in (ledger.get("frames") or {}).items()
        if isinstance(row, dict) and row.get("status") == "AUTHORITY_REFRESH_AUTHORIZED"
    )
    targets = list(frames)
    # When Visual Lock identity bootstrap itself changed authority, regenerate only
    # the ordinary baseline first. The remaining admissions must wait for the new
    # baseline actual-pixel PASS and provisional Pixel Master, exactly like initial
    # production. This prevents stale-master reuse and identity-free dependents.
    try:
        import character_visual_contract
        import visual_lock_baseline_gate
        baseline = int(visual_lock_baseline_gate.baseline_frame(ep))
        if baseline in frames and character_visual_contract.pixel_master_required(ep):
            targets = [baseline]
    except Exception:
        pass
    rows = [enqueue_authority_refresh(ep, frame) for frame in targets]
    return {
        "frames": targets,
        "pending_authority_refresh_frames": frames,
        "results": rows,
        "enqueued": sum(r.get("status") == "AUTHORITY_REFRESH_ENQUEUED" for r in rows),
    }


def review_attempt(ep: Path, frame: int) -> int:
    """Attempt 1 for originals, attempt 2 after the one ordinary repair."""
    row = _ledger_frame(Path(ep).resolve(), frame)
    return 2 if int(row.get("content_repairs_used") or 0) > 0 else 1


def _source_item(ep: Path, frame: int) -> dict:
    rows = [row for row in _queue_items(ep, frame) if row.get("status") == "generated"]
    if not rows:
        rows = _queue_items(ep, frame)
    if not rows:
        raise RuntimeError(f"no queue source item for frame {frame:02d}")
    # Queue order is chronological; a generated repair appended later must win.
    return rows[-1]


def _compact_findings(findings: list[str]) -> str:
    cleaned: list[str] = []
    for raw in findings:
        text = str(raw or "").strip().replace("\n", " ")
        if not text or text in cleaned:
            continue
        cleaned.append(text[:42])
        if len(cleaned) >= 6:
            break
    return "、".join(cleaned) if cleaned else "实际像素审核未通过"


def repair_prompt(frame: int, findings: list[str]) -> str:
    """Short derived prompt; the locked Frame Contract carries scene authority."""
    focus = _compact_findings(findings)
    text = (
        f"返修Frame{frame:02d}。严格保持当前Frame Contract、人物身份/服装/地点/事件与世界设定，不改故事。"
        f"重点修复：{focus}。改成可信的普通手机随手拍：自然不对称构图、真实皮肤与曝光、非电影布光、非海报化；"
        "保留生活杂物和轻微摄影瑕疵，天界设定照合同保留但不过度特效化。"
    )
    # Repository generation budget is <=260 chars / <=900 UTF-8 bytes.
    while len(text) > 250 or len(text.encode("utf-8")) > 860:
        if len(focus) <= 24:
            break
        focus = focus[:-4]
        text = (
            f"返修Frame{frame:02d}。严格保持当前Frame Contract、人物身份/服装/地点/事件与世界设定，不改故事。"
            f"重点修复：{focus}。普通手机随手拍，自然不对称构图、真实皮肤与曝光、非电影布光、非海报化；"
            "天界设定照合同保留但不过度特效化。"
        )
    return text


def enqueue(
    ep: Path,
    *,
    frame: int,
    findings: list[str],
    source: str,
    review_note: str,
) -> dict:
    ep = Path(ep).resolve()
    frame = int(frame)
    if repair_pending(ep, frame):
        return {"status": "REPAIR_ALREADY_PENDING", "frame": frame, "attempt": review_attempt(ep, frame)}

    ledger = _ledger_frame(ep, frame)
    status = str(ledger.get("status") or "")
    if status == "REPAIR_READY":
        # A repaired candidate failed content review. The ordinary one-shot
        # budget is exhausted; Production Ledger must move it to NEEDS_USER.
        ok, msg = ledger_call.review(ep, frame=frame, decision="repair", notes=review_note)
        return {"status": "NEEDS_USER" if ok else "ERROR", "frame": frame, "ledger": msg[-800:]}

    if status == "ORIGINAL_READY":
        ok, msg = ledger_call.review(ep, frame=frame, decision="repair", notes=review_note)
        if not ok:
            return {"status": "ERROR", "frame": frame, "ledger": msg[-800:]}
        status = str(_ledger_frame(ep, frame).get("status") or "")

    if status == "CONTENT_FAILED":
        ok, msg = ledger_call.authorize_repair(
            ep,
            frame=frame,
            note=f"{source}: delegated actual-pixel critic authorized one bounded content repair",
            delegated_auto=True,
        )
        if not ok:
            return {"status": "ERROR", "frame": frame, "ledger": msg[-800:]}
        status = str(_ledger_frame(ep, frame).get("status") or "")

    if status != "REPAIR_AUTHORIZED":
        return {"status": "NOT_REPAIRABLE", "frame": frame, "ledger_status": status}

    prompt_dir = ep / "prompts" / "repairs"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = prompt_dir / f"{frame:02d}-{source.lower().replace('_', '-')}-a2.txt"
    prompt_path.write_text(repair_prompt(frame, findings) + "\n", encoding="utf-8", newline="\n")

    # Local import avoids a baseline_gate <-> image_scheduler import cycle.
    import image_scheduler

    source_item = _source_item(ep, frame)
    policy = image_model_policy.for_episode(ep)
    refs = image_scheduler.contract_references(ep, frame, scope="repair")
    item = image_scheduler.add_item(
        ep,
        frame=frame,
        kind="repair",
        prompt_file=prompt_path,
        scope="repair",
        references=refs,
        capture_id=f"auto-repair-{source}-{frame:02d}",
        model=policy["model"],
        quality=policy["quality"],
        strict_model=bool(policy.get("strict_model")),
        depends_on=[int(x) for x in (source_item.get("depends_on") or [])],
        replace=False,
    )
    return {
        "status": "REPAIR_ENQUEUED",
        "frame": frame,
        "queue_item_id": item.get("id"),
        "prompt_file": item.get("prompt_file"),
        "ledger_status": str(_ledger_frame(ep, frame).get("status") or ""),
        "at": now(),
    }


def self_test() -> None:
    prompt = repair_prompt(1, ["reality_first", "not_cinematic", "capture_credibility"])
    assert len(prompt) <= 260
    assert len(prompt.encode("utf-8")) <= 900
    assert "Frame01" in prompt and "不改故事" in prompt
    refresh = authority_refresh_prompt(5)
    assert len(refresh) <= 260 and len(refresh.encode("utf-8")) <= 900
    assert "Frame05" in refresh and "权威刷新" in refresh
    print("AUTO REPAIR ENQUEUE SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
