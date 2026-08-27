from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from _common import Report, frame_numbers, load_yaml, normalize_frame_map, resolve_episode_path, stage_at_least

VOICE_REQUIRED = [
    "person","age","role","education_and_knowledge_boundary","usual_terms",
    "recording_reason","knows_now","does_not_know","allowed_technical_terms",
    "forbidden_technical_terms","stress_language","fear_language_change",
]
AI_STARTS = ["我发现", "更怪的是", "更可怕的是", "直到这时", "直到那时", "这证明", "这意味着"]


def validate(manifest_path: Path, *, release: bool = False) -> Report:
    r=Report("subtitles")
    try: d=load_yaml(manifest_path)
    except Exception as e: r.error(str(e)); return r
    cfg=d.get("subtitles") or {}
    if cfg.get("required") is not True:
        r.note("本集 subtitles.required != true，跳过字幕覆盖门禁")
        return r
    stage=str(d.get("stage","candidate"))
    need = release or stage_at_least(stage,"subtitled")
    path=resolve_episode_path(manifest_path,(d.get("paths") or {}).get("subtitles_file"))
    if path is None or not path.exists():
        (r.error if need else r.note)(f"字幕源文件不存在: {path}")
        return r
    try: s=load_yaml(path)
    except Exception as e: r.error(str(e)); return r

    voice=s.get("voice_card") or {}
    if not isinstance(voice,dict): r.error("voice_card 必须是 mapping"); voice={}
    missing_voice=[k for k in VOICE_REQUIRED if not str(voice.get(k,"")).strip()]
    if missing_voice:
        msg="声音卡未完成: "+", ".join(missing_voice)
        (r.error if need else r.warn)(msg)
    if cfg.get("sound_card_completed") is not True:
        (r.error if need else r.warn)("episode.yaml 中 subtitles.sound_card_completed 尚未设为 true")

    frames=normalize_frame_map(s.get("frames"),r)
    total=int((d.get("format") or {}).get("frame_count") or 0)
    silent=frame_numbers(s.get("silent_frames") or [],r,"silent_frames",total)
    silent_set=set(silent)
    for idx in frames:
        if idx<1 or idx>total: r.error(f"字幕图号越界: {idx}")
        if idx in silent_set: r.error(f"图 {idx:02d} 同时有字幕又标记 silent")
    uncovered=[i for i in range(1,total+1) if not frames.get(i,"").strip() and i not in silent_set]
    if uncovered:
        msg="既无字幕也未标静默的图: "+", ".join(f"{x:02d}" for x in uncovered)
        (r.error if need else r.warn)(msg)

    texts=[t.strip() for t in frames.values() if t.strip()]
    duplicates=[t for t,c in Counter(texts).items() if c>1]
    if duplicates: r.warn("存在完全重复字幕: "+" | ".join(duplicates[:3]))
    for start in AI_STARTS:
        hits=sum(1 for t in texts if t.startswith(start))
        if hits>=3: r.warn(f"AI腔风险：{hits} 帧以“{start}”开头")
    first_words=Counter(t[:4] for t in texts if len(t)>=4)
    repeated=[(x,c) for x,c in first_words.items() if c>=4]
    if repeated: r.warn("连续海报腔风险，重复句首较多: "+", ".join(f"{x}×{c}" for x,c in repeated[:5]))

    max_lines=cfg.get("max_lines")
    max_chars=cfg.get("max_chars_per_line")
    for idx,text in frames.items():
        if not text: continue
        lines=text.splitlines() or [text]
        if isinstance(max_lines,int) and len(lines)>max_lines:
            r.warn(f"图 {idx:02d} 字幕 {len(lines)} 行，manifest 提醒上限 {max_lines}")
        if isinstance(max_chars,int):
            for ln in lines:
                if len(ln.replace(" ",""))>max_chars:
                    r.warn(f"图 {idx:02d} 单行 {len(ln.replace(' ',''))} 字，超过提醒值 {max_chars}")

    clues=s.get("clues") or []
    if not isinstance(clues,list): r.error("clues 必须是数组"); clues=[]
    for i,c in enumerate(clues,1):
        if not isinstance(c,dict): r.error(f"clues[{i}] 必须是 mapping"); continue
        name=str(c.get("name","")).strip() or f"#{i}"
        first=c.get("first_frame")
        pay=c.get("payoff_frames") or []
        if not isinstance(first,int) or not 1<=first<=total: r.error(f"线索 {name} first_frame 非法")
        if not isinstance(pay,list) or not pay: r.error(f"线索 {name} 没有 payoff_frames")
        else:
            for x in pay:
                if not isinstance(x,int) or not 1<=x<=total: r.error(f"线索 {name} 回收图号非法: {x}")
        if not str(c.get("payoff_type","")).strip(): r.warn(f"线索 {name} 未填写 payoff_type")
    return r


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("manifest",type=Path); ap.add_argument("--release",action="store_true")
    a=ap.parse_args(); r=validate(a.manifest.resolve(),release=a.release); r.print(); return 0 if r.ok else 1
if __name__=="__main__": raise SystemExit(main())
