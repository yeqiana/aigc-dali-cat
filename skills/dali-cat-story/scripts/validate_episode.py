from __future__ import annotations

import argparse
from pathlib import Path
from _common import Report, STAGES, frame_numbers, load_yaml, stage_at_least


def validate(manifest_path: Path, *, release: bool = False) -> Report:
    r = Report("episode manifest")
    try:
        d = load_yaml(manifest_path)
    except Exception as e:
        r.error(str(e)); return r

    if d.get("schema_version") != 1:
        r.error("schema_version 必须为 1")

    stage = str(d.get("stage", ""))
    if stage not in STAGES:
        r.error(f"stage 非法: {stage!r}")
        stage = "candidate"

    ep = d.get("episode") or {}
    if not isinstance(ep, dict):
        r.error("episode 必须是 mapping"); ep = {}
    for key in ("id", "title"):
        if not str(ep.get(key, "")).strip() or str(ep.get(key)).startswith("__"):
            r.error(f"episode.{key} 未填写")

    fmt = d.get("format") or {}
    if not isinstance(fmt, dict):
        r.error("format 必须是 mapping"); fmt = {}
    if fmt.get("publish_mode") != "image_carousel":
        r.error("当前 story 冷启动形态锁定为 image_carousel")
    if str(fmt.get("ratio")) != "9:16":
        r.error("format.ratio 必须为 9:16")
    if fmt.get("width") != 1080 or fmt.get("height") != 1920:
        r.error("正式发布尺寸必须为 1080×1920")
    total = fmt.get("frame_count")
    if isinstance(total, bool) or not isinstance(total, int) or total < 1:
        r.error("format.frame_count 必须为正整数")
        total = 1

    story = d.get("story") or {}
    if not isinstance(story, dict):
        r.error("story 必须是 mapping"); story = {}
    hook = frame_numbers(story.get("hook_frames"), r, "story.hook_frames", total)
    va = frame_numbers(story.get("visual_admission_frames"), r, "story.visual_admission_frames", total)
    frame_numbers(story.get("escalation_frames"), r, "story.escalation_frames", total)
    for name in ("climax_frame", "payoff_frame"):
        value = story.get(name)
        if value is not None and (isinstance(value, bool) or not isinstance(value, int) or not (1 <= value <= total)):
            r.error(f"story.{name} 必须在 1..{total} 范围内")

    story_gate = stage_at_least(stage, "story_locked", release=release)
    if story_gate:
        if not hook:
            r.error("进入 story_locked 后必须指定 hook_frames")
        if not story.get("task_closed"):
            r.error("进入 story_locked 后 task_closed 必须为 true")
        ce = story.get("competing_explanations", 0)
        if not isinstance(ce, int) or ce < 2:
            r.error("进入 story_locked 后 competing_explanations 至少为 2")
        if story.get("climax_frame") is None or story.get("payoff_frame") is None:
            r.error("进入 story_locked 后必须锁定 climax_frame 与 payoff_frame")

        anti = d.get("anti_homogeneity") or {}
        if not isinstance(anti, dict):
            r.error("anti_homogeneity 必须是 mapping"); anti = {}
        if anti.get("mechanism_skin_swap_veto") is True:
            r.error("已触发机制换皮一票否决：选题必须退回")
        if anti.get("recent5_checked") is not True:
            r.error("最近5篇账号级同质化检查尚未通过")
        diff = anti.get("four_locks_diff_count", 0)
        if not isinstance(diff, int) or diff < 2:
            r.error("四把锁至少需要 2 把不同")

    if stage_at_least(stage, "visual_admission", release=release):
        if len(va) != 4 or len(set(va)) != 4:
            r.error("visual_admission_frames 必须恰好 4 个且互不重复")

    if stage_at_least(stage, "production", release=release):
        anchors = ((d.get("continuity") or {}).get("anchors") or {})
        if not isinstance(anchors, dict):
            r.error("continuity.anchors 必须是 mapping")
        else:
            filled = [k for k,v in anchors.items() if str(v or "").strip()]
            if not filled:
                r.warn("production 阶段没有填写任何 continuity anchor；返修时容易漂移")

    if release or stage_at_least(stage, "release_ready"):
        if stage not in {"release_ready", "published"} and not release:
            r.warn(f"当前 stage={stage}，尚未标记 release_ready")

    return r


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--release", action="store_true")
    args = ap.parse_args()
    r = validate(args.manifest.resolve(), release=args.release)
    r.print(); return 0 if r.ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
