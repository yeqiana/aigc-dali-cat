#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fresh isolated semantic equivalence review for Recent-5 fingerprint comparisons."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

WEIGHTS = {
    "core_anomaly_mechanism": 25,
    "story_engine": 15,
    "entry_mode": 10,
    "anomaly_carrier": 10,
    "primary_visual_space": 10,
    "middle_escalation": 10,
    "climax_form": 10,
    "relationship": 5,
    "reality_residue": 5,
}
FINGERPRINT_KEYS = tuple(WEIGHTS)
VETO_KEYS = ("core_anomaly_mechanism", "middle_escalation", "climax_form")
REVIEW_REL = Path("meta/recent5-semantic-review.json")
CANDIDATE_REL = Path("meta/.recent5-semantic-review.candidate.json")
LOG_REL = Path("meta/recent5-semantic-critic.jsonl")

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return data

def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def repo_rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()

def version_tuple(raw: object) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in str(raw or "").split("."))
    except Exception:
        return (0,)

def required(contract_version: str) -> bool:
    return version_tuple(contract_version) >= (2, 0, 3, 6)

def resolve_codex(raw: str | None) -> Path:
    value = raw or shutil.which("codex") or shutil.which("codex.exe") or shutil.which("codex.cmd")
    if not value:
        raise RuntimeError("Codex CLI not found for semantic Recent-5 critic")
    return Path(value).expanduser().resolve()

def prefix(codex: Path) -> list[str]:
    if codex.suffix.lower() == ".py":
        return [sys.executable, str(codex)]
    if os.name == "nt" and codex.suffix.lower() in {".cmd", ".bat"}:
        return ["cmd.exe", "/d", "/c", str(codex)]
    return [str(codex)]

def score_from_flags(flags: dict) -> tuple[int, bool, list[str]]:
    matched = [k for k in FINGERPRINT_KEYS if flags.get(k) is True]
    score = sum(WEIGHTS[k] for k in matched)
    veto = all(flags.get(k) is True for k in VETO_KEYS)
    return score, veto, matched

def history_ids(history: list[dict]) -> list[str]:
    ids = []
    for row in history:
        eid = str(row.get("episode_id") or "").strip()
        if not eid:
            raise ValueError("historical fingerprint missing episode_id")
        ids.append(eid)
    if len(set(ids)) != len(ids):
        raise ValueError("historical fingerprint episode_id duplicated")
    return ids

def critic_prompt(root: Path, ep: Path, fp_path: Path, registry_path: Path, current: dict, history: list[dict], candidate: Path) -> str:
    rel_ep = repo_rel(root, ep)
    rel_out = repo_rel(root, candidate)
    rel_fp = repo_rel(root, fp_path)
    rel_reg = repo_rel(root, registry_path)
    pairs = []
    for row in history:
        pairs.append({
            "episode_id": row.get("episode_id"),
            "title": row.get("title"),
            "dimensions": row.get("dimensions") or {},
        })
    return f"""You are an adversarial semantic de-duplication critic in a fresh isolated session.

Goal:
Detect whether the CURRENT episode reuses the same underlying story mechanism as each recent historical episode even when the wording, nouns, location, era, or props are changed.

Do NOT edit any repository file except the requested candidate JSON.
Do NOT score anything yourself. Python computes scores from your booleans.
Do NOT mark a dimension equivalent merely because both stories share the same genre or mood.

Current episode:
{json.dumps({"episode_id": current.get("episode_id"), "title": current.get("title"), "dimensions": current.get("dimensions") or {}}, ensure_ascii=False, indent=2)}

Recent historical fingerprints:
{json.dumps(pairs, ensure_ascii=False, indent=2)}

Interpret each dimension by underlying audience-facing role:
- core_anomaly_mechanism: what impossible rule/event actually drives the story.
- story_engine: the causal storytelling engine, not the surface setting.
- entry_mode: how the protagonist enters/encounters the abnormal situation.
- anomaly_carrier: the object/person/place/system that carries the abnormality.
- primary_visual_space: the dominant visual environment/function, not just place name.
- middle_escalation: how the anomaly escalates through the middle.
- climax_form: what irreversible/highest-intensity reveal/action forms the climax.
- relationship: the protagonist/other-person relationship structure driving decisions.
- reality_residue: what evidence/consequence remains in ordinary reality afterward.

For every historical episode and every dimension, return true only when the underlying function/mechanism is substantially the same despite paraphrase or skin-swap. Return false when similarity is only genre, tone, broad setting, or incidental vocabulary.

Important examples:
- "进入地图上不存在的村子" vs "沿着一条导航里没有的路走进陌生村落" can be equivalent entry/anomaly mechanisms even though text differs.
- "旧手机提前出现明天的照片" vs "MP4里出现未来影像" can be semantically equivalent anomaly carriers/mechanisms depending on their actual role.
- "都发生在山里" is NOT enough to mark primary_visual_space or mechanism equivalent by itself.
- If core_anomaly_mechanism + middle_escalation + climax_form are all equivalent, this is a likely skin-swap and Python will veto it.

Write ONLY valid JSON to {rel_out} in this exact shape:
{{
  "comparisons": [
    {{
      "episode_id": "<one exact historical episode_id>",
      "equivalent_dimensions": {{
        "core_anomaly_mechanism": false,
        "story_engine": false,
        "entry_mode": false,
        "anomaly_carrier": false,
        "primary_visual_space": false,
        "middle_escalation": false,
        "climax_form": false,
        "relationship": false,
        "reality_residue": false
      }},
      "match_reasons": {{
        "<only keys marked true>": "brief concrete reason"
      }}
    }}
  ]
}}

Repository evidence being compared:
- current fingerprint: {rel_fp}
- account registry: {rel_reg}
- episode: {rel_ep}

Requirements:
- Include exactly one comparison for every supplied historical episode_id.
- Keep every equivalent_dimensions value strictly boolean.
- match_reasons may contain only dimensions marked true; if none are true, use an empty object.
- Never invent a historical episode or change an episode_id.
"""

def validate_candidate(candidate: dict, history: list[dict]) -> tuple[list[dict], list[str]]:
    errors = []
    expected_ids = history_ids(history)
    rows = candidate.get("comparisons")
    if not isinstance(rows, list):
        return [], ["candidate.comparisons must be a list"]
    got_ids = [str(x.get("episode_id") or "") for x in rows if isinstance(x, dict)]
    if got_ids != expected_ids:
        errors.append(f"candidate comparison ids/order mismatch: expected {expected_ids!r}, got {got_ids!r}")
    normalized_rows = []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"comparison[{idx}] must be object")
            continue
        flags = row.get("equivalent_dimensions")
        if not isinstance(flags, dict):
            errors.append(f"comparison[{idx}].equivalent_dimensions must be object")
            continue
        if set(flags) != set(FINGERPRINT_KEYS):
            errors.append(f"comparison[{idx}] must contain exactly the nine fingerprint dimensions")
            continue
        bad = [k for k in FINGERPRINT_KEYS if not isinstance(flags.get(k), bool)]
        if bad:
            errors.append(f"comparison[{idx}] non-boolean dimensions: {bad}")
            continue
        reasons = row.get("match_reasons")
        if not isinstance(reasons, dict):
            errors.append(f"comparison[{idx}].match_reasons must be object")
            continue
        invalid_reason_keys = [k for k in reasons if k not in FINGERPRINT_KEYS or flags.get(k) is not True]
        if invalid_reason_keys:
            errors.append(f"comparison[{idx}] invalid match_reasons keys: {invalid_reason_keys}")
            continue
        missing_reasons = [k for k in FINGERPRINT_KEYS if flags.get(k) is True and not str(reasons.get(k) or "").strip()]
        if missing_reasons:
            errors.append(f"comparison[{idx}] missing reasons for true dimensions: {missing_reasons}")
            continue
        score, veto, matched = score_from_flags(flags)
        normalized_rows.append({
            "episode_id": str(row.get("episode_id") or ""),
            "equivalent_dimensions": {k: bool(flags[k]) for k in FINGERPRINT_KEYS},
            "match_reasons": {k: str(reasons[k]).strip() for k in matched},
            "semantic_similarity_score": score,
            "semantic_mechanism_veto": veto,
            "semantic_matched_dimensions": matched,
        })
    return normalized_rows, errors

def validate_review(root: Path, ep: Path, fp_path: Path, registry_path: Path, history: list[dict], contract_version: str, data: dict) -> list[str]:
    errors = []
    if data.get("schema_version") != 1:
        errors.append("semantic recent5 schema_version must be 1")
    if data.get("story_os_version") != contract_version:
        errors.append("semantic recent5 story_os_version mismatch")
    if str(data.get("candidate_fingerprint_path") or "") != repo_rel(root, fp_path):
        errors.append("semantic recent5 candidate fingerprint path mismatch")
    if str(data.get("candidate_fingerprint_sha256") or "").lower() != sha256_file(fp_path).lower():
        errors.append("semantic recent5 candidate fingerprint SHA drift")
    if str(data.get("registry_path") or "") != repo_rel(root, registry_path):
        errors.append("semantic recent5 registry path mismatch")
    if str(data.get("registry_sha256") or "").lower() != sha256_file(registry_path).lower():
        errors.append("semantic recent5 registry SHA drift")
    expected_ids = history_ids(history)
    if data.get("history_episode_ids") != expected_ids:
        errors.append("semantic recent5 history episode set/order drift")

    prov = data.get("critic_provenance") or {}
    if prov.get("runtime") != "CODEX_ISOLATED" or prov.get("isolated_session") is not True:
        errors.append("semantic recent5 critic must be fresh CODEX_ISOLATED")
    log_raw = prov.get("log")
    if not isinstance(log_raw, str) or not log_raw.strip():
        errors.append("semantic recent5 critic log path missing")
    else:
        log_path = (root / log_raw).resolve()
        try:
            log_path.relative_to(root.resolve())
        except ValueError:
            errors.append("semantic recent5 critic log escapes repository")
        else:
            if not log_path.is_file():
                errors.append("semantic recent5 critic log missing")
            elif str(prov.get("log_sha256") or "").lower() != sha256_file(log_path).lower():
                errors.append("semantic recent5 critic log SHA drift")

    rows = data.get("comparisons")
    if not isinstance(rows, list):
        errors.append("semantic recent5 comparisons must be list")
        return errors
    got_ids = [str(x.get("episode_id") or "") for x in rows if isinstance(x, dict)]
    if got_ids != expected_ids:
        errors.append("semantic recent5 comparison ids/order mismatch")
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"semantic comparison[{idx}] invalid")
            continue
        flags = row.get("equivalent_dimensions")
        if not isinstance(flags, dict) or set(flags) != set(FINGERPRINT_KEYS):
            errors.append(f"semantic comparison[{idx}] dimension set invalid")
            continue
        if any(not isinstance(flags.get(k), bool) for k in FINGERPRINT_KEYS):
            errors.append(f"semantic comparison[{idx}] dimensions must be booleans")
            continue
        score, veto, matched = score_from_flags(flags)
        if row.get("semantic_similarity_score") != score:
            errors.append(f"semantic comparison[{idx}] score is not Python-derived")
        if row.get("semantic_mechanism_veto") is not veto:
            errors.append(f"semantic comparison[{idx}] veto is not Python-derived")
        if row.get("semantic_matched_dimensions") != matched:
            errors.append(f"semantic comparison[{idx}] matched dimension list drift")
        reasons = row.get("match_reasons")
        if not isinstance(reasons, dict):
            errors.append(f"semantic comparison[{idx}] match_reasons missing")
        else:
            invalid = [k for k in reasons if k not in matched or not str(reasons.get(k) or "").strip()]
            missing = [k for k in matched if not str(reasons.get(k) or "").strip()]
            if invalid or missing:
                errors.append(f"semantic comparison[{idx}] match reasons inconsistent")
    return errors

def run_review(root: Path, ep: Path, fp_path: Path, registry_path: Path, history: list[dict], contract_version: str, codex_raw: str | None = None, timeout: int = 1800) -> dict:
    current = read_json(fp_path)
    candidate = ep / CANDIDATE_REL
    review_path = ep / REVIEW_REL
    log_path = ep / LOG_REL
    candidate.unlink(missing_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    before_fp = sha256_file(fp_path)
    before_reg = sha256_file(registry_path)
    codex = resolve_codex(codex_raw)
    cmd = prefix(codex) + [
        "exec", "--skip-git-repo-check", "--ephemeral",
        "-c", 'model_reasoning_effort="high"',
        "-s", "workspace-write", "-C", str(root), "--json", "-"
    ]
    with log_path.open("w", encoding="utf-8", newline="\n") as handle:
        completed = subprocess.run(
            cmd,
            input=critic_prompt(root, ep, fp_path, registry_path, current, history, candidate),
            text=True,
            stdout=handle,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
    if completed.returncode != 0:
        raise RuntimeError(f"semantic recent5 critic failed rc={completed.returncode}; log={log_path}")
    if before_fp != sha256_file(fp_path) or before_reg != sha256_file(registry_path):
        raise RuntimeError("semantic recent5 critic changed fingerprint or registry; review invalid")
    if not candidate.is_file():
        raise RuntimeError("semantic recent5 critic did not produce candidate JSON")

    raw = read_json(candidate)
    rows, errors = validate_candidate(raw, history)
    if errors:
        raise RuntimeError("semantic recent5 candidate invalid: " + "; ".join(errors))

    data = {
        "schema_version": 1,
        "story_os_version": contract_version,
        "episode_id": current.get("episode_id"),
        "reviewed_at": now(),
        "candidate_fingerprint_path": repo_rel(root, fp_path),
        "candidate_fingerprint_sha256": sha256_file(fp_path),
        "registry_path": repo_rel(root, registry_path),
        "registry_sha256": sha256_file(registry_path),
        "history_episode_ids": history_ids(history),
        "critic_provenance": {
            "runtime": "CODEX_ISOLATED",
            "isolated_session": True,
            "log": repo_rel(root, log_path),
            "log_sha256": sha256_file(log_path),
            "reviewed_at": now(),
        },
        "comparisons": rows,
    }
    write_json(review_path, data)
    candidate.unlink(missing_ok=True)
    errors = validate_review(root, ep, fp_path, registry_path, history, contract_version, data)
    if errors:
        raise RuntimeError("semantic recent5 finalized review invalid: " + "; ".join(errors))
    return data

def ensure_review(root: Path, ep: Path, fp_path: Path, registry_path: Path, history: list[dict], contract_version: str, codex_raw: str | None = None, timeout: int = 1800) -> dict:
    p = ep / REVIEW_REL
    if p.is_file():
        try:
            data = read_json(p)
            if not validate_review(root, ep, fp_path, registry_path, history, contract_version, data):
                return data
        except Exception:
            pass
    return run_review(root, ep, fp_path, registry_path, history, contract_version, codex_raw, timeout)

def comparison_index(review: dict) -> dict[str, dict]:
    return {
        str(row.get("episode_id")): row
        for row in review.get("comparisons", [])
        if isinstance(row, dict) and row.get("episode_id")
    }

def self_test() -> int:
    # Exact wording may be completely different while semantics are the same.
    a = "进入地图上不存在的村子"
    b = "沿导航里没有的路走进陌生聚落"
    assert a != b
    flags = {k: False for k in FINGERPRINT_KEYS}
    flags["core_anomaly_mechanism"] = True
    flags["middle_escalation"] = True
    flags["climax_form"] = True
    score, veto, matched = score_from_flags(flags)
    assert score == 45
    assert veto is True
    assert matched == ["core_anomaly_mechanism", "middle_escalation", "climax_form"]

    all_flags = {k: True for k in FINGERPRINT_KEYS}
    score, veto, matched = score_from_flags(all_flags)
    assert score == 100 and veto and len(matched) == 9
    print("FINGERPRINT SEMANTICS SELF-TEST PASS")
    return 0

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test")
    args = ap.parse_args()
    return self_test()

if __name__ == "__main__":
    raise SystemExit(main())
