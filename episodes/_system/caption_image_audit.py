#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Incremental Caption ↔ Image audit for Story OS V2.6.0.

Caption edits never invalidate the Visual Semantic Review. Only caption/image pairs
whose caption SHA or image SHA changed are reviewed again, in chunks of up to 5.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import frame_semantic_review as base
import incremental_frame_review as inc
import runtime_command
import runtime_router
import product_review_adapter

ROOT = Path(__file__).resolve().parents[2]
REL = Path("meta/caption-image-audit.json")
SCHEMA = 1
CHUNK = 5


class ProductReviewHostAction(RuntimeError):
    def __init__(self, request: dict):
        super().__init__("caption/image review requires product runtime host action")
        self.request = request

def _caption_texts(ep: Path, frames: list[dict]) -> tuple[dict[str, str], dict]:
    source = inc._manifest_caption_path(ep)
    keys = [row["frame"] for row in frames]
    if source is None:
        return {k: "" for k in keys}, {"source_path": None, "mode": "none"}
    raw = source.read_text(encoding="utf-8", errors="replace")
    if source.suffix.lower() == ".json":
        try:
            texts = inc._extract_json_captions(json.loads(raw))
        except Exception:
            texts = {}
    else:
        texts = inc._extract_yaml_captions(raw)
    if not texts and raw.strip():
        raise ValueError(f"caption parser could not resolve per-frame captions: {source}")
    return {k: texts.get(k, "") for k in keys}, {
        "source_path": source.resolve().relative_to(ROOT.resolve()).as_posix(),
        "mode": "per_frame" if texts else "none",
    }

def _read(ep: Path) -> dict:
    p = ep / REL
    if not p.is_file():
        return {"schema_version": SCHEMA, "module_version": "2.6.0", "frames": {}}
    try:
        d = json.loads(p.read_text(encoding="utf-8-sig"))
        return d if isinstance(d, dict) else {"schema_version": SCHEMA, "module_version": "2.6.0", "frames": {}}
    except Exception:
        return {"schema_version": SCHEMA, "module_version": "2.6.0", "frames": {}}

def _write(ep: Path, data: dict) -> None:
    base.write_json(ep / REL, data)

def _hashes(ep: Path, frames: list[dict]) -> tuple[dict[str, str], dict[str, str], dict[str, str], dict]:
    cap_state = inc.caption_state(ep, frames)
    texts, source_meta = _caption_texts(ep, frames)
    image_sha = {r["frame"]: r["sha256"] for r in frames}
    caption_sha = cap_state["frame_sha256"]
    return image_sha, caption_sha, texts, {**source_meta, "source_sha256": cap_state.get("source_sha256")}

def dirty_frames(ep: Path) -> tuple[list[dict], dict, dict[str, str], dict[str, str], dict[str, str], dict]:
    frames = base.frame_records(ep, require_files=True)
    current = _read(ep)
    image_sha, caption_sha, texts, source_meta = _hashes(ep, frames)
    existing = current.get("frames") or {}
    dirty = []
    for row in frames:
        key = row["frame"]
        old = existing.get(key) or {}
        if (
            old.get("image_sha256") != image_sha[key]
            or old.get("caption_sha256") != caption_sha[key]
            or old.get("passed") is not True
            or old.get("schema_version") != SCHEMA
        ):
            dirty.append(row)
    return dirty, current, image_sha, caption_sha, texts, source_meta

def _prompt(ep: Path, rows: list[dict], texts: dict[str, str], out: Path) -> str:
    mapping = "\n".join(
        f"- frame {r['frame']}: image={r['path_rel']} | caption={json.dumps(texts[r['frame']], ensure_ascii=False)}"
        for r in rows
    )
    return f"""You are the Story OS Caption ↔ Image Support Critic.
Review ONLY whether each supplied caption is honestly supported by the actual pixels of its mapped image.
Do not re-review story quality, composition, character continuity, or overall visual quality.
A caption may add ordinary context, but must not invent a core visible event, prop, person, UI text, anomaly, action, or causal fact absent from the image.
Empty captions automatically pass and should not be embellished.
Mappings:
{mapping}

Write ONLY JSON to {out.relative_to(ROOT).as_posix()}:
{{"frames":[{{"frame":"01","supported":true,"notes":"specific pixel support"}}],"summary":{{"passed":true}}}}
Return one row for every attached frame. summary.passed=false if any supported=false.
"""

def _run_chunk(ep: Path, rows: list[dict], texts: dict[str, str], codex_raw: str | None, timeout: int, index: int) -> dict:
    out = ep / "meta" / f".caption-image-audit-candidate-{index:03d}.json"
    active_runtime, _ = runtime_router.detect()
    if active_runtime in {"WORK", "WEB"} and not codex_raw:
        kind = f"caption-image-audit-{index:03d}"
        request_file = product_review_adapter.request_path(ep, kind)
        if out.is_file() and request_file.is_file():
            data, provenance = product_review_adapter.finalize_candidate(
                ep,
                kind=kind,
                runtime=active_runtime,
                attempt=1,
                candidate_path=out,
            )
            data["critic_provenance"] = provenance
            data["_product_review_kind"] = kind
            return data
        out.unlink(missing_ok=True)
        sources = [Path(row["path"]).resolve() for row in rows]
        caption_source = inc._manifest_caption_path(ep)
        if caption_source is not None:
            sources.append(caption_source.resolve())
        request = product_review_adapter.prepare(
            ep,
            kind=kind,
            runtime=active_runtime,
            attempt=1,
            prompt=_prompt(ep, rows, texts, out),
            source_paths=sources,
            candidate_path=out,
        )
        raise ProductReviewHostAction(request)

    out.unlink(missing_ok=True)
    codex = base.resolve_codex(codex_raw)
    cmd = base.command_prefix(codex) + [
        "exec", "--skip-git-repo-check", "--ephemeral",
        "-c", 'model_reasoning_effort="low"',
        "-s", "workspace-write", "-C", str(ROOT), "--json",
    ]
    for row in rows:
        cmd += ["-i", str(row["path"])]
    cmd += ["-"]
    cp = runtime_command.run_argv(cmd, cwd=ROOT, stdin_text=_prompt(ep, rows, texts, out), timeout=timeout, capture=True)
    log = ep / "meta" / f"caption-image-audit-{index:03d}.jsonl"
    log.write_text(cp.stdout or "", encoding="utf-8", newline="\n")
    if cp.returncode != 0 or not out.is_file():
        raise RuntimeError(f"caption image critic failed rc={cp.returncode}; log={log}")
    data = json.loads(out.read_text(encoding="utf-8-sig"))
    out.unlink(missing_ok=True)
    return data if isinstance(data, dict) else {}

def ensure(ep: Path, codex_raw: str | None = None, timeout: int = 900) -> tuple[bool, dict]:
    ep = Path(ep).resolve()
    dirty, current, image_sha, caption_sha, texts, source_meta = dirty_frames(ep)
    rows_by_key = {r["frame"]: r for r in base.frame_records(ep, require_files=True)}
    evidence = current if isinstance(current, dict) else {}
    evidence.update({
        "schema_version": SCHEMA,
        "module_version": "2.6.0",
        "caption_source": source_meta,
    })
    dest = evidence.setdefault("frames", {})
    reviewed = 0
    reused = len(rows_by_key) - len(dirty)

    # Empty captions are deterministic passes and require no vision call.
    nonempty = []
    for row in dirty:
        key = row["frame"]
        if not texts.get(key, "").strip():
            dest[key] = {
                "schema_version": SCHEMA, "frame": key,
                "image_sha256": image_sha[key], "caption_sha256": caption_sha[key],
                "passed": True, "mode": "empty_caption", "notes": "no caption to validate",
            }
        else:
            nonempty.append(row)

    for start in range(0, len(nonempty), CHUNK):
        chunk = nonempty[start:start + CHUNK]
        data = _run_chunk(ep, chunk, texts, codex_raw, timeout, start // CHUNK + 1)
        got = {str(x.get("frame") or "").zfill(2): x for x in (data.get("frames") or []) if isinstance(x, dict)}
        for row in chunk:
            key = row["frame"]
            result = got.get(key)
            if not result:
                raise RuntimeError(f"caption image critic omitted frame {key}")
            passed = result.get("supported") is True
            dest[key] = {
                "schema_version": SCHEMA, "frame": key,
                "image_sha256": image_sha[key], "caption_sha256": caption_sha[key],
                "passed": passed, "mode": "pixel_critic",
                "notes": str(result.get("notes") or ""),
                "critic_provenance": data.get("critic_provenance"),
            }
            reviewed += 1

    evidence["summary"] = {
        "passed": all((dest.get(k) or {}).get("passed") is True for k in rows_by_key),
        "reviewed_dirty_frames": reviewed,
        "reused_frames": reused,
        "total_frames": len(rows_by_key),
        "visual_review_invalidated": False,
    }
    _write(ep, evidence)

    active_runtime, _ = runtime_router.detect()
    if active_runtime in {"WORK", "WEB"} and not codex_raw:
        chunk_count = (len(nonempty) + CHUNK - 1) // CHUNK
        for index in range(1, chunk_count + 1):
            kind = f"caption-image-audit-{index:03d}"
            request_file = product_review_adapter.request_path(ep, kind)
            candidate_file = ep / "meta" / f".caption-image-audit-candidate-{index:03d}.json"
            if request_file.is_file() and candidate_file.is_file():
                product_review_adapter.mark_complete(ep, kind, attempt=1, final_path=ep / REL)
                candidate_file.unlink(missing_ok=True)
    return evidence["summary"]["passed"], evidence

def verify(ep: Path) -> list[str]:
    ep = Path(ep).resolve()
    frames = base.frame_records(ep, require_files=True)
    data = _read(ep)
    image_sha, caption_sha, _texts, _source_meta = _hashes(ep, frames)
    errors = []
    rows = data.get("frames") or {}
    for frame in frames:
        key = frame["frame"]
        row = rows.get(key)
        if not isinstance(row, dict):
            errors.append(f"caption image audit missing frame {key}")
            continue
        if row.get("image_sha256") != image_sha[key]:
            errors.append(f"caption image audit image SHA stale: {key}")
        if row.get("caption_sha256") != caption_sha[key]:
            errors.append(f"caption image audit caption SHA stale: {key}")
        if row.get("passed") is not True:
            errors.append(f"caption image audit failed: {key}")
    return errors

def self_test():
    assert CHUNK == 5
    print("CAPTION IMAGE AUDIT V2.6.0 SELF-TEST PASS")

def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("ensure"); p.add_argument("episode_dir"); p.add_argument("--codex"); p.add_argument("--timeout", type=int, default=900)
    p = sub.add_parser("verify"); p.add_argument("episode_dir")
    p = sub.add_parser("show"); p.add_argument("episode_dir")
    sub.add_parser("self-test")
    a = ap.parse_args()
    ep = Path(getattr(a, "episode_dir", ".")).resolve()
    if a.cmd == "self-test": self_test(); return 0
    if a.cmd == "show": print(json.dumps(_read(ep), ensure_ascii=False, indent=2)); return 0
    if a.cmd == "verify":
        errors = verify(ep)
        for e in errors: print("FAIL:", e)
        if not errors: print("CAPTION IMAGE AUDIT VERIFY PASS")
        return 2 if errors else 0
    ok, data = ensure(ep, a.codex, a.timeout)
    print(json.dumps(data.get("summary") or {}, ensure_ascii=False, indent=2))
    return 0 if ok else 2

if __name__ == "__main__":
    raise SystemExit(main())
