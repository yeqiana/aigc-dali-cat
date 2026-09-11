#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""release_preflight release review + critic prompt domain (B4 split)."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
import caption_image_audit
import codex_critic_runner
import subtitle_layout
import runtime_router
import runtime_provenance
import product_review_adapter
from release_preflight_core import *

def load_manifest(ep: Path) -> dict:
    return read_json(ep / "meta/release-manifest.json")

def release_artifacts(ep: Path) -> dict[str, Path]:
    manifest = load_manifest(ep)
    release = manifest.get("release") or {}
    artifacts = manifest.get("artifacts") or {}
    publish_dir_raw = release.get("publish_dir")
    if not isinstance(publish_dir_raw, str) or not publish_dir_raw.strip():
        raise ValueError("manifest.release.publish_dir missing")
    publish_dir = (ROOT / publish_dir_raw).resolve()
    body_glob = str(release.get("body_glob") or "").strip()
    if not body_glob:
        raise ValueError("manifest.release.body_glob missing")
    body = sorted(p for p in publish_dir.glob(body_glob) if p.is_file())
    if len(body) < 3:
        raise ValueError("release requires at least 3 final body images")
    cover = repo_file(release.get("cover_path"), "manifest.release.cover_path")
    captions = repo_file(artifacts.get("captions"), "manifest.artifacts.captions")
    publish_copy = repo_file(artifacts.get("publish_copy"), "manifest.artifacts.publish_copy")
    propagation = repo_file(artifacts.get("propagation_card"), "manifest.artifacts.propagation_card")
    gates = read_json(ep / "meta/story-gates.json")
    story = gates.get("story") or {}
    climax = story.get("climax_frame")
    payoff = story.get("payoff_frame")
    def frame_for(n: object) -> Path:
        if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= len(body):
            raise ValueError(f"invalid story frame reference: {n!r}")
        return body[n - 1]
    rows = {"cover": cover}
    rows.update({f"body{i:02d}": path for i, path in enumerate(body, start=1)})
    rows.update({
        "climax": frame_for(climax),
        "payoff": frame_for(payoff),
        "captions": captions,
        "publish_copy": publish_copy,
        "propagation_card": propagation,
    })
    return rows

def release_hashes(ep: Path) -> dict[str, dict]:
    return {
        role: {"path": repo_rel(path), "sha256": sha256_file(path)}
        for role, path in release_artifacts(ep).items()
    }

def release_review_rows(rows: dict[str, dict]) -> dict[str, dict]:
    """Keep the final critic on release semantics; all-body subtitle pixels are chunk-audited separately."""
    roles = ("cover", "body01", "body02", "body03", "climax", "payoff", "captions", "publish_copy", "propagation_card")
    return {role: rows[role] for role in roles if role in rows}

def resolve_codex(raw: str | None) -> Path:
    value = raw or shutil.which("codex") or shutil.which("codex.exe") or shutil.which("codex.cmd")
    if not value:
        raise RuntimeError("Codex CLI not found")
    return Path(value).expanduser().resolve()

def prefix(codex: Path) -> list[str]:
    if codex.suffix.lower() == ".py":
        return [sys.executable, str(codex)]
    if os.name == "nt" and codex.suffix.lower() in {".cmd", ".bat"}:
        return ["cmd.exe", "/d", "/c", str(codex)]
    return [str(codex)]

def release_critic_prompt(ep: Path, candidate: Path, rows: dict[str, dict]) -> str:
    manifest = load_manifest(ep)
    publication = manifest.get("publication") or {}
    title = str(publication.get("actual_title") or "")
    description = str(publication.get("description") or "")
    topics = publication.get("topics") or []
    review_rows = release_review_rows(rows)
    mapping = "\n".join(f"- {role}: {row['path']}" for role, row in review_rows.items())
    rel = ep.relative_to(ROOT).as_posix()
    out = candidate.relative_to(ROOT).as_posix()
    return f"""You are an adversarial FINAL RELEASE Semantic + Governance Critic in a fresh isolated session.
Do NOT edit any file except the requested candidate JSON.
Episode: {rel}

Inspect the ACTUAL final publish assets, not prompts:
{mapping}

Actual title:
{title}

Description:
{description}

Topics:
{json.dumps(topics, ensure_ascii=False)}

Read:
- standards/制作规范_正式版.md
- standards/release_preflight_guard_V2.0.3.5.md
- {rel}/meta/subtitle-layout-audit.json (deterministic all-frame placement/line-count/hash audit)
- {rel}/meta/caption-image-audit.json (all final publish frames reviewed in SHA-bound chunks of up to 5 for caption support + actual subtitle obstruction)
- the episode Story Lock / storyboard / captions / publish copy / propagation card.

Hard release checks:
1. cover_title_match: cover and actual title promise the same core story/anomaly.
2. cover_frame01_handoff: body01 immediately continues or concretely supports the cover promise; no bait-and-switch.
3. first3_coherence: body01-03 form one readable entry path, not three disconnected hooks.
4. climax_upgrade: the actual climax frame is meaningfully stronger/more irreversible than the first hook.
5. payoff_honesty: the payoff is earned by earlier evidence and does not add a brand-new mechanism.
6. description_consistency: description/topics do not claim official fact, real case, or evidence absent from the story.
7. no_caption_invented_core_evidence: final text may add context, but may not invent the core visual evidence.
8. subtitle_left_middle_and_unobstructed: require BOTH SHA-bound all-frame audits above to PASS. subtitle-layout-audit proves left/middle geometry, line count and current publish-output hashes; caption-image-audit proves every final publish frame was pixel-reviewed in chunks and subtitle_unobstructed=true. Do not reopen every body image here; fail if either audit is missing/stale/failed.
9. caption_conversational_hook_quality: captions must sound like a real first-person immediate record, stay concise/eye-catching, avoid novel narration/AI boilerplate, and perform one clear narrative function per frame. Two rendered lines is the hard maximum.

Governance checks:
- This is AI-generated realistic fictional story content.
- Real locations may be used as story backgrounds, but the release must not present invented events as official/verified real incidents.
- No unverifiable dangerous accusation against a real region, ethnicity, religion, organization, or identifiable person.
- Platform AI-generation declaration/label must be planned and not intentionally stripped.
- A fiction-context notice is appropriate for this Story OS format.

PASS only when every release and governance check is true.
Write ONLY valid JSON to {out}:
{{
  "release_checks": {{
    "cover_title_match": true,
    "cover_frame01_handoff": true,
    "first3_coherence": true,
    "climax_upgrade": true,
    "payoff_honesty": true,
    "description_consistency": true,
    "no_caption_invented_core_evidence": true,
    "subtitle_left_middle_and_unobstructed": true,
    "caption_conversational_hook_quality": true
  }},
  "governance_checks": {{
    "ai_generated_declared": true,
    "platform_ai_label_planned": true,
    "fiction_context_not_misrepresented_as_official_fact": true,
    "no_unverifiable_real_group_accusation": true,
    "real_location_handled_as_fictional_story_context": true
  }},
  "issue_codes": [],
  "notes": ["specific final-release evidence"],
  "summary": {{"passed": true}}
}}
"""

def validate_release_review(ep: Path, data: dict) -> list[str]:
    errors = []
    if data.get("schema_version") != 1:
        errors.append("release semantic schema_version must be 1")
    if data.get("story_os_version") != episode_contract_version(ep):
        errors.append("release semantic story_os_version mismatch")
    current = release_hashes(ep)
    if data.get("artifacts") != current:
        errors.append("release semantic artifact SHA set is stale or mismatched")
    prov = data.get("critic_provenance") or {}
    errors.extend(runtime_provenance.validate_critic_provenance(prov))
    checks = data.get("release_checks") or {}
    for key in RELEASE_CHECKS:
        if checks.get(key) is not True:
            errors.append(f"release_checks.{key} must be true")
    gov = data.get("governance_checks") or {}
    for key in GOV_CHECKS:
        if gov.get(key) is not True:
            errors.append(f"governance_checks.{key} must be true")
    if data.get("issue_codes") not in ([], None):
        errors.append(f"release semantic issue_codes not empty: {data.get('issue_codes')}")
    if (data.get("summary") or {}).get("passed") is not True:
        errors.append("release semantic summary.passed must be true")
    return errors

def _finalize_release_review(ep: Path, data: dict, provenance: dict) -> int:
    data["schema_version"] = 1
    data["story_os_version"] = episode_contract_version(ep)
    data["artifacts"] = release_hashes(ep)
    data["critic_provenance"] = provenance
    write_json(ep / RELEASE_REVIEW_REL, data)
    (ep / RELEASE_CANDIDATE_REL).unlink(missing_ok=True)
    errors = validate_release_review(ep, data)
    if errors:
        print("RELEASE SEMANTIC REVIEW FAIL")
        for e in errors:
            print("FAIL:", e)
        return 2
    print("RELEASE SEMANTIC REVIEW PASS")
    return 0

def finalize_product_release_review(ep: Path, runtime: str) -> int:
    candidate = ep / RELEASE_CANDIDATE_REL
    data, provenance = product_review_adapter.finalize_candidate(
        ep,
        kind="release-semantic",
        runtime=runtime,
        attempt=1,
        candidate_path=candidate,
    )
    rc = _finalize_release_review(ep, data, provenance)
    if rc == 0:
        product_review_adapter.mark_complete(ep, "release-semantic", attempt=1, final_path=ep / RELEASE_REVIEW_REL)
    return rc

def cmd_run_release_critic(args: argparse.Namespace) -> int:
    ep = ep_path(args.episode_dir)
    rows = release_hashes(ep)
    candidate = ep / RELEASE_CANDIDATE_REL
    candidate.unlink(missing_ok=True)
    active_runtime, _ = runtime_router.detect()
    if active_runtime in {"WORK", "WEB"} and not args.codex:
        review_rows = release_review_rows(rows)
        source_paths = list(dict.fromkeys(ROOT / row["path"] for row in review_rows.values()))
        source_paths += [
            ep / subtitle_layout.REPORT_REL,
            ep / caption_image_audit.REL,
            ROOT / "standards/制作规范_正式版.md",
            ROOT / "standards/release_preflight_guard_V2.0.3.5.md",
        ]
        request = product_review_adapter.prepare(
            ep,
            kind="release-semantic",
            runtime=active_runtime,
            attempt=1,
            prompt=release_critic_prompt(ep, candidate, rows),
            source_paths=source_paths,
            candidate_path=candidate,
        )
        print(json.dumps(request, ensure_ascii=False, indent=2))
        return product_review_adapter.HOST_ACTION_REQUIRED_RC
    codex = resolve_codex(args.codex)
    cmd = prefix(codex) + [
        "exec", "--skip-git-repo-check", "--ephemeral",
        "-c", 'model_reasoning_effort="high"',
        "-s", codex_critic_runner.default_sandbox(), "-C", str(ROOT), "--json", "-"
    ]
    log = ep / "meta/release-critic.jsonl"
    before = {role: row["sha256"] for role, row in rows.items()}
    with log.open("w", encoding="utf-8", newline="\n") as handle:
        completed = subprocess.run(
            cmd,
            input=release_critic_prompt(ep, candidate, rows),
            text=True,
            stdout=handle,
            stderr=subprocess.STDOUT,
            timeout=args.timeout,
            check=False,
        )
    if completed.returncode != 0:
        raise RuntimeError(f"release critic failed rc={completed.returncode}; log={log}")
    after = {role: row["sha256"] for role, row in release_hashes(ep).items()}
    if before != after:
        raise RuntimeError("release critic changed final release assets; review invalid")
    if not candidate.is_file():
        raise RuntimeError("release critic did not produce candidate JSON")
    data = read_json(candidate)
    provenance = runtime_provenance.build_critic_provenance(
        "CODEX", attempt=1, log=repo_rel(log)
    )
    return _finalize_release_review(ep, data, provenance)
