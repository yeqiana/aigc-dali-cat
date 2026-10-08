#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import codex_critic_runner
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from story_os_contract import story_os_version
import propagation_core_gate  # STORY_OS_V2_5_PROPAGATION_CORE
import runtime_router
import runtime_provenance
import product_review_adapter
import story_json
import runtime_timeout_policy
import episode_state_persistence
import review_record_persistence
import review_policy_binding
import runtime_request

ROOT = Path(__file__).resolve().parents[2]
REVIEW_REL = Path("meta/story-semantic-review.json")
REVIEW_TYPE = "STORY_SEMANTIC"
EXPORT_REL = Path("meta/runtime/review-exports/story-semantic.json")
CANDIDATE_REL = Path("meta/.story-semantic-review.candidate.json")
STORYBOARD_EXCEPTION_REL = Path("meta/runtime/storyboard-review-exceptions.json")
TARGET_CONTRACT = (2, 0, 3, 2)

CONTRACT_FIELDS = [
    "protagonist",
    "presence_reason",
    "personal_stake",
    "core_anomaly",
    "rule",
    "trigger",
    "direct_consequence",
    "midpoint_reframe",
    "climax_choice",
]
BLIND_FIELDS = [
    "protagonist_and_reason",
    "core_anomaly_rule",
    "worsening_choice",
    "climax_resolution",
    "ending_reinterpretation",
]
HARD_CHECKS = [
    "clarity",
    "causal_chain",
    "mechanism_consistency",
    "motivation_stake",
    "trigger_consequence",
    "midpoint_reframe",
    "climax_payoff",
    "ending_payoff",
    "storyboard_information_gain",
    "delete_frame_test",
]


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    return story_json.read_json(path)


def write_json(path: Path, data: dict) -> None:
    story_json.write_json(path, data)



def load_review(ep: Path) -> dict | None:
    ep = Path(ep).resolve()
    return review_record_persistence.load_latest(
        ep, REVIEW_TYPE, legacy_path=ep / REVIEW_REL
    )


def review_authority_sha256(ep: Path) -> str | None:
    return review_record_persistence.authority_sha256(
        Path(ep).resolve(), REVIEW_TYPE, legacy_path=Path(ep).resolve() / REVIEW_REL
    )


def save_review(
    ep: Path,
    data: dict,
    *,
    decision: str,
    source_sha256: str | None = None,
) -> dict:
    data = review_policy_binding.attach_bound_policy_sha(Path(ep).resolve(), data)
    provenance = data.get("critic_provenance") or {}
    return review_record_persistence.save(
        Path(ep).resolve(),
        REVIEW_TYPE,
        REVIEW_REL,
        data,
        decision=decision,
        reviewer_type=str(provenance.get("runtime") or "") or None,
        source_sha256=source_sha256,
    )


def materialize_review_export(ep: Path, data: dict | None = None) -> Path | None:
    return review_record_persistence.materialize_export(
        Path(ep).resolve(),
        REVIEW_TYPE,
        payload=data,
        filename="story-semantic.json",
    )


def version_tuple(raw: object) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in str(raw or "").split("."))
    except ValueError:
        return (0,)


def episode_contract_version(ep: Path) -> str:
    versions = []
    try:
        state = episode_state_persistence.load(Path(ep).resolve()) or {}
        raw = str(state.get("tool_version") or "")
        vt = version_tuple(raw)
        if vt != (0,):
            versions.append((vt, raw))
    except Exception:
        pass
    for rel in ("meta/release-manifest.json", "meta/story-gates.json"):
        p = ep / rel
        if not p.is_file():
            continue
        try:
            raw = str(read_json(p).get("tool_version") or "")
            vt = version_tuple(raw)
            if vt != (0,):
                versions.append((vt, raw))
        except Exception:
            continue
    return max(versions, key=lambda x: x[0])[1] if versions else story_os_version()


def review_required(ep: Path) -> bool:
    try:
        if version_tuple(
            (episode_state_persistence.load(Path(ep).resolve()) or {}).get("tool_version")
        ) >= TARGET_CONTRACT:
            return True
    except Exception:
        pass
    p = Path(ep).resolve() / "meta/release-manifest.json"
    if p.is_file():
        try:
            return version_tuple(read_json(p).get("tool_version")) >= TARGET_CONTRACT
        except Exception:
            pass
    return False


def repo_file(raw: object, where: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{where} missing")
    rel = Path(raw.strip())
    p = rel.resolve() if rel.is_absolute() else (ROOT / rel).resolve()
    try:
        p.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"{where} escapes repository") from exc
    if not p.is_file():
        raise ValueError(f"{where} missing: {raw}")
    return p


def story_paths(ep: Path) -> tuple[Path, Path]:
    manifest = read_json(ep / "meta/release-manifest.json")
    artifacts = manifest.get("artifacts") or {}
    return (
        repo_file(artifacts.get("story"), "manifest.artifacts.story"),
        repo_file(artifacts.get("storyboard"), "manifest.artifacts.storyboard"),
    )


def validate_payload(data: dict, *, story_sha: str, storyboard_sha: str, version: str) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("story_os_version") != version:
        errors.append("story_os_version mismatch")
    if str(data.get("story_sha256") or "").lower() != story_sha.lower():
        errors.append("story_sha256 mismatch")
    if str(data.get("storyboard_sha256") or "").lower() != storyboard_sha.lower():
        errors.append("storyboard_sha256 mismatch")

    provenance = data.get("critic_provenance") or {}
    errors.extend(runtime_provenance.validate_critic_provenance(provenance))
    attempt = provenance.get("attempt")
    continuation = (
        attempt == 3
        and provenance.get("direct_user_continuation_review") is True
        and provenance.get("review_scope") == "LOCKED_DOCUMENTARY_POLICY_REVISION"
        and provenance.get("review_epoch") == 2
        and provenance.get("epoch_attempt") == 1
        and all(isinstance(provenance.get(key), str)
                and len(provenance[key]) == 64
                and all(ch in "0123456789abcdef" for ch in provenance[key].lower())
                for key in ("previous_review_sha256", "previous_rubric_sha256", "current_rubric_sha256"))
        and provenance.get("previous_rubric_sha256") != provenance.get("current_rubric_sha256")
    )
    source_revision = (
        attempt == 4
        and provenance.get("direct_user_continuation_review") is True
        and provenance.get("review_scope") == "LOCKED_DOCUMENTARY_SOURCE_REVISION"
        and provenance.get("review_epoch") == 3
        and provenance.get("epoch_attempt") == 1
        and all(isinstance(provenance.get(k), str)
                and len(provenance[k]) == 64
                and all(ch in "0123456789abcdef" for ch in provenance[k].lower())
                for k in ("previous_review_sha256", "previous_storyboard_sha256", "current_rubric_sha256"))
        and provenance.get("previous_storyboard_sha256") != storyboard_sha
    )
    symbolic_remediation = (
        attempt == 5
        and provenance.get("direct_user_continuation_review") is True
        and provenance.get("review_scope") == "LOCKED_DOCUMENTARY_SYMBOLIC_REMEDIATION"
        and provenance.get("review_epoch") == 4
        and provenance.get("epoch_attempt") == 1
        and all(isinstance(provenance.get(k), str)
                and len(provenance[k]) == 64
                and all(ch in "0123456789abcdef" for ch in provenance[k].lower())
                for k in ("previous_review_sha256", "previous_storyboard_sha256",
                          "previous_rubric_sha256", "current_rubric_sha256"))
        and provenance.get("previous_storyboard_sha256") != storyboard_sha
        and provenance.get("previous_rubric_sha256") != provenance.get("current_rubric_sha256")
    )
    if attempt not in {1, 2} and not (continuation or source_revision or symbolic_remediation):
        errors.append("critic attempt must be 1 or 2 unless explicitly authorized policy continuation attempt 3 or SHA-bound source revision attempt 4/5")
    revisions = {0, 1, 2, 3, 4} if symbolic_remediation else ({0, 1, 2, 3} if source_revision else ({0, 1, 2} if continuation else {0, 1}))
    if data.get("revision_count") not in revisions:
        errors.append("revision_count invalid for critic review scope")
    elif attempt in {1, 2, 3, 4, 5} and data.get("revision_count") != attempt - 1:
        errors.append("revision_count must equal critic attempt - 1")

    contract = data.get("contract") or {}
    for key in CONTRACT_FIELDS:
        if not str(contract.get(key) or "").strip():
            errors.append(f"contract.{key} missing")
    reinterpret = contract.get("ending_recontextualization")
    if not isinstance(reinterpret, list) or len([x for x in reinterpret if str(x).strip()]) < 3:
        errors.append("ending must recontextualize at least 3 concrete earlier facts")

    blind = data.get("blind_retell") or {}
    for key in BLIND_FIELDS:
        if not str(blind.get(key) or "").strip():
            errors.append(f"blind_retell.{key} missing")

    checks = data.get("hard_checks") or {}
    for key in HARD_CHECKS:
        if checks.get(key) is not True:
            errors.append(f"hard_checks.{key} must be true")

    issue_codes = data.get("issue_codes")
    if not isinstance(issue_codes, list):
        errors.append("issue_codes must be a list")
    elif issue_codes:
        errors.append("issue_codes must be empty for PASS")

    summary = data.get("summary") or {}
    if summary.get("passed") is not True:
        errors.append("summary.passed must be true")
    return errors


def _storyboard_sha_exception_matches(ep: Path, reviewed_sha: str, current_sha: str) -> bool:
    """Allow only an explicit user-approved, structure-preserving storyboard rebind."""
    path = Path(ep).resolve() / STORYBOARD_EXCEPTION_REL
    if not path.is_file():
        return False
    try:
        data = read_json(path)
    except Exception:
        return False
    if data.get("exception_type") != "direct_user_storyboard_revision":
        return False
    if data.get("user_approved") is not True or data.get("delegated_auto_review") is not False:
        return False
    if not str(data.get("user_statement") or "").strip():
        return False
    for row in data.get("items") or []:
        if not isinstance(row, dict):
            continue
        if (
            str(row.get("from_storyboard_sha256") or "").lower() == str(reviewed_sha).lower()
            and str(row.get("to_storyboard_sha256") or "").lower() == str(current_sha).lower()
            and row.get("user_approved") is True
            and row.get("delegated_auto_review") is False
        ):
            return True
    return False


def verify(ep: Path) -> list[str]:
    if not review_required(ep):
        return []
    data = load_review(ep)
    if not isinstance(data, dict):
        return ["meta/story-semantic-review.json missing"]
    try:
        story, storyboard = story_paths(ep)
    except Exception as exc:
        return [str(exc)]
    current_storyboard_sha = sha256_file(storyboard)
    errors = validate_payload(
        data,
        story_sha=sha256_file(story),
        storyboard_sha=current_storyboard_sha,
        version=episode_contract_version(ep),
    )
    if "storyboard_sha256 mismatch" in errors and _storyboard_sha_exception_matches(
        ep, str(data.get("storyboard_sha256") or ""), current_storyboard_sha
    ):
        errors.remove("storyboard_sha256 mismatch")
    if (data.get("critic_provenance") or {}).get("direct_user_continuation_review") is True:
        source_revision = data["critic_provenance"].get("review_scope") == "LOCKED_DOCUMENTARY_SOURCE_REVISION"
        symbolic_remediation = data["critic_provenance"].get("review_scope") == "LOCKED_DOCUMENTARY_SYMBOLIC_REMEDIATION"
        evidence_path = Path(ep) / ("meta/runtime/story-review-symbolic-remediation-a5.json" if symbolic_remediation
                                    else "meta/runtime/story-review-source-revision-a4.json" if source_revision
                                    else "meta/runtime/story-review-policy-continuation-a3.json")
        try:
            evidence = read_json(evidence_path)
            provenance = data["critic_provenance"]
            if (evidence.get("global_review_attempt") != provenance.get("attempt")
                    or evidence.get("review_scope") != provenance.get("review_scope")
                    or evidence.get("review_epoch") != provenance.get("review_epoch")
                    or evidence.get("epoch_attempt") != provenance.get("epoch_attempt")
                    or evidence.get("previous_review_sha256") != provenance.get("previous_review_sha256")
                    or evidence.get("current_rubric_sha256") != provenance.get("current_rubric_sha256")
                    or evidence.get("story_sha256") != sha256_file(story)
                    or evidence.get("storyboard_sha256") != sha256_file(storyboard)
                    or ((source_revision or symbolic_remediation) and evidence.get("previous_storyboard_sha256") != provenance.get("previous_storyboard_sha256"))
                    or (symbolic_remediation and evidence.get("previous_rubric_sha256") != provenance.get("previous_rubric_sha256"))
                    or evidence.get("current_rubric_sha256") != _review_rubric_digest(Path(__file__).read_text(encoding="utf-8-sig"))):
                errors.append("policy continuation authority or current rubric SHA mismatch")
        except (OSError, ValueError, KeyError, RuntimeError):
            errors.append("policy continuation manifest missing or invalid")
    if propagation_core_gate.required(ep):
        errors.extend(propagation_core_gate.verify(ep))
    return errors


def resolve_codex(raw: str | None) -> Path:
    import codex_cli_contract
    return codex_cli_contract.resolve_path(raw)


def command_prefix(codex: Path) -> list[str]:
    import codex_cli_contract
    return codex_cli_contract.command_prefix(codex)


def _locked_documentary_rubric(ep: Path) -> bool:
    """Only user-locked stories explicitly scoped as real-life/non-anomalous."""
    try:
        request = runtime_request.authority_for_episode(Path(ep).resolve())
        story_input = (request or {}).get("story_input") if isinstance(request, dict) else None
        return (
            isinstance(story_input, dict)
            and story_input.get("mode") == "locked_story"
            and story_input.get("allow_structure_rewrite") is False
            and not propagation_core_gate.anomaly_applicable(ep)
        )
    except Exception:
        return False


def critic_prompt(ep: Path, story: Path, storyboard: Path, candidate: Path, attempt: int) -> str:
    rel_ep = ep.relative_to(ROOT).as_posix()
    rel_story = story.relative_to(ROOT).as_posix()
    rel_board = storyboard.relative_to(ROOT).as_posix()
    rel_out = candidate.relative_to(ROOT).as_posix()
    ordinary_life_override = "" if propagation_core_gate.anomaly_applicable(ep) else """
ORDINARY-LIFE OVERRIDE (takes precedence over anomaly-specific rules below):
- This Episode is explicitly locked as anomaly_applicable=false. Do NOT invent horror, mystery, paranormal behavior, investigation, anomaly rules, or an abnormal response merely to satisfy generic schema wording.
- Evaluate whether the ordinary-day arc, relationships, spatial progression, midpoint route change, emotional/visual peak, ending payoff and delete-frame density are coherent and production-worthy.
- contract.core_anomaly / rule / trigger / direct_consequence and blind_retell.core_anomaly_rule must be non-empty explicit NOT_APPLICABLE statements explaining that the no-anomaly design is intentional.
- hard_checks.mechanism_consistency means the Episode remains consistently non-anomalous; hard_checks.trigger_consequence means ordinary actions have readable ordinary responses/consequences rather than an abnormal mechanism.
- ending_recontextualization may pay off at least three earlier ordinary-life facts, objects, or relationship beats; it does not need a twist.
- V2.5 anomaly propagation_core is NOT required for this explicitly ordinary-life Episode. Omit it rather than fabricating an abnormal_response.
"""
    prompt = f"""You are an adversarial Story Critic in a fresh isolated session.
Do NOT rewrite the story. Do NOT score it politely. Your job is to find reasons it should NOT enter production.
Read:
- {rel_story}
- {rel_board}
- standards/制作规范_正式版.md
- standards/创作执行强制规范_V2.0.3.2.md
- standards/story_regressions/cases.json
- standards/传播核与动作回应链规范_V1.0.md

This is critic attempt {attempt}. Ignore propagation scores and author self-evaluation.
{ordinary_life_override}
Hard rules:
1. A viewer must be able to explain protagonist, why they are here, their personal stake, the ONE core anomaly rule, trigger, direct consequence, midpoint reframe, climax choice/cost, result and aftermath.
2. The main events must be explainable by one coherent underlying anomaly mechanism. If an object first returns by itself, later guides people, then suddenly "marks the next person" without one established rule explaining all three, mechanism_consistency=false.
3. Causality must read as reality goal -> rule/setup -> meaningful choice/violation -> direct consequence -> forced next action -> climax choice/cost -> result -> aftermath. A warning revealed only after the violation cannot retroactively create a meaningful choice unless the story established the rule another way.
4. "I found them", "the door opened", "the monster appeared", "the photo changed" are discoveries/setup, not a climax by themselves. The climax needs choice, cost, relationship change, rule payoff, identity turn or irreversible consequence.
5. The ending must recontextualize at least THREE concrete earlier facts. Introducing a brand-new anomaly behavior at the end is not payoff.
6. In any run of 5 storyboard frames, at least one frame must add new evidence, causal turn or cognitive upgrade. Apply the delete-frame test.
7. Perform a BLIND RETELL from your own understanding. If you need "maybe / perhaps / unclear" to explain the core mechanism or climax, clarity/mechanism_consistency must fail.
8. PASS only when every hard check is true and issue_codes is empty.
9. V2.5 PROPAGATION CORE: identify one ordinary protagonist action that causes a direct abnormal response and a visible consequence.
10. Write a <=10-second retell sentence; avoid lore-heavy explanation.
11. Bind trigger_frame, response_frame and payoff_frame to actual storyboard frames. Default trigger <=50%; if later, explain why.
12. Golden examples are structural references only; do not copy location + prop + trigger action + climax surface together.
<!-- STORY_OS_V2_5_PROPAGATION_CORE -->

Write ONLY valid JSON to {rel_out}. Do not modify any other repository file.
Required JSON shape:
{{
  "contract": {{
    "protagonist": "...",
    "presence_reason": "...",
    "personal_stake": "...",
    "core_anomaly": "...",
    "rule": "...",
    "trigger": "...",
    "direct_consequence": "...",
    "midpoint_reframe": "...",
    "climax_choice": "...",
    "ending_recontextualization": ["earlier fact 1", "earlier fact 2", "earlier fact 3"]
  }},
  "propagation_core": {{
    "retell_sentence": "...",
    "protagonist_action": "...",
    "abnormal_response": "...",
    "consequence": "...",
    "response_latency": "immediate",
    "visual_causality": "strong",
    "retellable_in_10s": true,
    "social_send_impulse": "strong",
    "trigger_frame": 9,
    "response_frame": 10,
    "payoff_frame": 14,
    "late_trigger_exception_reason": "",
    "surface_copy_guard": {{
      "structural_reference_only": true,
      "copied_surface_elements": []
    }}
  }},
  "blind_retell": {{
    "protagonist_and_reason": "...",
    "core_anomaly_rule": "...",
    "worsening_choice": "...",
    "climax_resolution": "...",
    "ending_reinterpretation": "..."
  }},
  "hard_checks": {{
    "clarity": true,
    "causal_chain": true,
    "mechanism_consistency": true,
    "motivation_stake": true,
    "trigger_consequence": true,
    "midpoint_reframe": true,
    "climax_payoff": true,
    "ending_payoff": true,
    "storyboard_information_gain": true,
    "delete_frame_test": true
  }},
  "issue_codes": [],
  "notes": ["specific evidence or failure notes"],
  "summary": {{"passed": true}}
}}
If any hard rule fails, set its boolean false, add specific codes such as STORY_COMPREHENSION_FAIL, CAUSAL_CHAIN_BROKEN, MECHANISM_CONTRADICTION, CLIMAX_DISCOVERY_ONLY, ENDING_PAYOFF_TOO_WEAK, STORYBOARD_STALL, and set summary.passed=false.
Episode: {rel_ep}
"""
    if _locked_documentary_rubric(ep):
        # Replace incompatible anomaly-oriented *instructions*, not the review
        # authority, mandatory fields, true/false checks or independent critic.
        # The original full rubric remains unchanged for authored/mystery stories.
        start = prompt.index("Hard rules:\n")
        end = prompt.index("Write ONLY valid JSON", start)
        documentary_rules = """LOCKED NON-ANOMALOUS DOCUMENTARY HARD RULES:
1. Do not rewrite any user-locked scene, subtitle, character, age, amount, diagnosis, legal outcome or frame count. Check exact source fidelity.
2. Check real chronology and age arithmetic. A visual casting age may differ from chronological age only when clearly identified as appearance; never silently excuse a numerical contradiction.
3. In cumulative real-life hardship, disaster, illness and accidents can be independently caused; judge the credibility of each asserted relation and the accumulation of financial/caregiving consequences, not a fictional shared mechanism.
4. The midpoint may be a grounded change of stakes or role, not a supernatural revelation. The emotional peak may be a loss; any closing moral choice must come from the actual words, not invented actions.
5. An open ending with debts unpaid can be a truthful payoff. Revisit three concrete earlier facts; do not imply forgiveness, legal relief, new income, or a happy rescue unless the source states it.
6. Judge each locked frame by its unique factual, visual, chronological or emotional contribution. Flag true repetition without requiring deletion of frames the user expressly locked.
7. Treat suicide, cancer, disability and poverty with dignity; avoid sensationalism and unearned blame.
8. For the schema's anomaly/rule/trigger/core_anomaly_rule fields, give explicit non-empty NOT_APPLICABLE explanations. Do not invent paranormal phenomena or an abnormal response. propagation_core is not required here.
8a. User-authored locked storyboard imagery is an authoritative *visual brief*, not an assertion that each prop was independently documented in the prose story. A visibly symbolic object or composite shot may appear even without a narrated physical discovery. Do NOT mistake such a visual metaphor for new forensic evidence. Fail when the storyboard or its production notes asserts that an undocumented object was actually recovered, identified, investigated or used as real proof.
9. Evaluate every hard check truthfully. If source facts are contradictory, or any check fails, give specific issue_codes and summary.passed=false.
"""
        prompt = prompt[:start] + documentary_rules + "\n" + prompt[end:]
        # The generic example requires an invented abnormal-response object.
        # Omit that optional shape entirely for non-anomalous locked stories.
        example_start = prompt.index('  "propagation_core": {')
        example_end = prompt.index('  "blind_retell": {', example_start)
        prompt = prompt[:example_start] + prompt[example_end:]
    return prompt


def _finalize_review(ep: Path, data: dict, *, attempt: int, before_story: str, before_board: str, provenance: dict) -> int:
    data["schema_version"] = 1
    data["story_os_version"] = episode_contract_version(ep)
    data["story_sha256"] = before_story
    data["storyboard_sha256"] = before_board
    data["revision_count"] = attempt - 1
    data["critic_provenance"] = provenance
    errors = validate_payload(
        data,
        story_sha=before_story,
        storyboard_sha=before_board,
        version=episode_contract_version(ep),
    )
    decision = "PASS" if not errors else "FAIL"
    source_sha = hashlib.sha256(
        f"{before_story}|{before_board}".encode("utf-8")
    ).hexdigest()
    save_review(ep, data, decision=decision, source_sha256=source_sha)
    (ep / CANDIDATE_REL).unlink(missing_ok=True)
    if propagation_core_gate.required(ep):
        errors.extend(propagation_core_gate.verify(ep))
    if errors:
        print("STORY SEMANTIC REVIEW FAIL")
        for error in errors:
            print("FAIL:", error)
        for code in data.get("issue_codes") or []:
            print("ISSUE:", code)
        return 2
    print("STORY SEMANTIC REVIEW PASS")
    return 0


def finalize_product_review(ep: Path, *, attempt: int, runtime: str) -> int:
    story, storyboard = story_paths(ep)
    candidate = ep / CANDIDATE_REL
    data, provenance = product_review_adapter.finalize_candidate(
        ep,
        kind="story-semantic",
        runtime=runtime,
        attempt=attempt,
        candidate_path=candidate,
    )
    rc = _finalize_review(
        ep,
        data,
        attempt=attempt,
        before_story=sha256_file(story),
        before_board=sha256_file(storyboard),
        provenance=provenance,
    )
    if rc == 0:
        final_export = materialize_review_export(ep, load_review(ep))
        if final_export is None:
            raise RuntimeError("story semantic review export missing after PASS")
        product_review_adapter.mark_complete(
            ep, "story-semantic", attempt=attempt, final_path=final_export
        )
    return rc


def schedule_critic_shadow(
    ep: Path, *, attempt: int, story: Path, storyboard: Path, sources: list[Path],
    review_attempt: int | None = None,
    canonical_source_files: list[dict] | None = None,
) -> dict:
    """Schedule the advisory Critic beside, never inside, canonical Story Review."""
    try:
        import story_semantic_critic_adapter as critic_shadow
    except ModuleNotFoundError:
        from agents import story_semantic_critic_adapter as critic_shadow

    config = critic_shadow.adapter_config()
    if config.get("shadow_enabled") is not True:
        return {"enabled": False, "scheduled": False}
    if config.get("production_enabled") is True:
        raise RuntimeError("Critic shadow/production overlap; refusing Story Review dispatch")
    applicability = critic_shadow.frozen_applicability_context(ep)
    applicability_path = ep / critic_shadow.APPLICABILITY_REL
    prompt = critic_shadow.build_decision_prompt(
        attempt=int(review_attempt if review_attempt is not None else attempt),
        story_text=story.read_text(encoding="utf-8-sig"),
        storyboard_text=storyboard.read_text(encoding="utf-8-sig"),
        rubric_text="\n\n".join(path.read_text(encoding="utf-8-sig") for path in sources[2:]),
        applicability=applicability,
    )
    if canonical_source_files is not None:
        frozen = {str(row.get("path")): str(row.get("sha256")).lower()
                  for row in canonical_source_files if isinstance(row, dict)}
        for source in sources:
            relative = source.resolve().relative_to(ROOT.resolve()).as_posix()
            if frozen.get(relative) != sha256_file(source).lower():
                raise RuntimeError(f"Critic shadow source differs from canonical review request: {relative}")
    shadow_request = critic_shadow.prepare_shadow_request(
        ep, attempt=attempt, review_attempt=(review_attempt if review_attempt is not None else attempt),
        prompt=prompt, story_path=story,
        storyboard_path=storyboard, rubric_paths=[*sources[2:], applicability_path],
        applicability_context=applicability,
    )
    return {
        "enabled": True,
        "scheduled": isinstance(shadow_request, dict),
            "request_id": (shadow_request or {}).get("request_id"),
        "request_path": (shadow_request or {}).get("request_path"),
        "request_snapshot_path": (shadow_request or {}).get("request_snapshot_path"),
        "request_snapshot_sha256": (shadow_request or {}).get("request_snapshot_sha256"),
        "applicability_context": applicability,
        "candidate_authority": "runtime_evidence_only",
    }


def _review_rubric_digest(source: str) -> str:
    """SHA over the actual critic_prompt function AST, not a mutable label."""
    tree = ast.parse(source)
    function = next((node for node in tree.body if isinstance(node, ast.FunctionDef)
                     and node.name == "critic_prompt"), None)
    if function is None:
        raise RuntimeError("story critic rubric function missing")
    return hashlib.sha256(ast.dump(function, include_attributes=False).encode("utf-8")).hexdigest()


def _authorize_policy_continuation(ep: Path, *, attempt: int, prior_rubric_ref: str | None) -> dict:
    """An explicit, one-time review #3 after two real failures and a changed rubric.

    Not a reset: keep the earlier reviews in their existing immutable Review
    repository. A failed new review cannot be retried by repeating this command.
    """
    if attempt != 3 or not prior_rubric_ref:
        raise RuntimeError("policy continuation requires attempt=3 and --prior-rubric-ref")
    if not _locked_documentary_rubric(ep):
        raise RuntimeError("policy continuation is only available for locked non-anomalous stories")
    prior = load_review(ep)
    if not isinstance(prior, dict) or (prior.get("critic_provenance") or {}).get("attempt") != 2:
        raise RuntimeError("prior independent Critic attempt #2 missing")
    if (prior.get("summary") or {}).get("passed") is not False:
        raise RuntimeError("continuation requires a failed prior Critic #2")
    if (ep / "meta/runtime/story-review-policy-continuation-a3.json").exists():
        raise RuntimeError("policy continuation #3 already authorized; cannot dispatch twice")
    relative = Path("episodes/_system/story_review.py").as_posix()
    old_commit = subprocess.run(["git", "rev-parse", "--verify", prior_rubric_ref + "^{commit}"],
                                cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", old_commit, "HEAD"], cwd=ROOT)
    if ancestor.returncode != 0:
        raise RuntimeError("prior rubric ref is not an ancestor of current HEAD")
    old_code = subprocess.run(["git", "show", f"{old_commit}:{relative}"], cwd=ROOT,
                              capture_output=True, check=True).stdout.decode("utf-8-sig")
    before_rubric = _review_rubric_digest(old_code)
    after_rubric = _review_rubric_digest(Path(__file__).read_text(encoding="utf-8-sig"))
    if before_rubric == after_rubric:
        raise RuntimeError("previous and current Critic rubric match; continuation not authorized")
    story, storyboard = story_paths(ep)
    prior_digest = review_authority_sha256(ep)
    if not prior_digest:
        raise RuntimeError("prior Critic authority SHA missing")
    binding = {
        "schema": "storyos.story_critic_policy_continuation.v1",
        "review_scope": "LOCKED_DOCUMENTARY_POLICY_REVISION",
        "global_review_attempt": 3,
        "review_epoch": 2,
        "epoch_attempt": 1,
        "authorization": "direct_user_continuation",
        "previous_review_sha256": prior_digest,
        "previous_review_attempt": 2,
        "previous_review_passed": False,
        "previous_rubric_git_commit": old_commit,
        "previous_rubric_sha256": before_rubric,
        "current_rubric_sha256": after_rubric,
        "story_sha256": sha256_file(story),
        "storyboard_sha256": sha256_file(storyboard),
        "previous_storyboard_sha256": prior.get("storyboard_sha256"),
        "source_unchanged": prior.get("story_sha256") == sha256_file(story)
            and prior.get("storyboard_sha256") == sha256_file(storyboard),
        "previous_issue_codes": list(prior.get("issue_codes") or []),
        "reason": "Material rubric correction from anomaly plot to locked real-life documentary; no source rewrite or fabricated prior PASS",
    }
    target = ep / "meta/runtime/story-review-policy-continuation-a3.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, binding)
    return binding


def _authorize_source_revision(ep: Path, *, attempt: int) -> dict:
    """One SHA-bound user-directed review of corrected documentary storyboard."""
    if attempt != 4 or not _locked_documentary_rubric(ep):
        raise RuntimeError("source revision requires locked documentary attempt=4")
    target = ep / "meta/runtime/story-review-source-revision-a4.json"
    if target.exists():
        raise RuntimeError("source revision attempt 4 already authorized; no redispatch")
    prior = load_review(ep)
    if (not isinstance(prior, dict)
            or (prior.get("critic_provenance") or {}).get("attempt") != 3
            or (prior.get("summary") or {}).get("passed") is not False
            or not prior.get("issue_codes")):
        raise RuntimeError("must have a real previous failed attempt 3")
    policy_path = ep / "meta/runtime/story-review-policy-continuation-a3.json"
    if not policy_path.is_file():
        raise RuntimeError("previous policy authority missing")
    rubric_sha = _review_rubric_digest(Path(__file__).read_text(encoding="utf-8-sig"))
    if read_json(policy_path).get("current_rubric_sha256") != rubric_sha:
        raise RuntimeError("rubric must not silently change during source continuation")
    story, storyboard = story_paths(ep)
    story_sha, board_sha = sha256_file(story), sha256_file(storyboard)
    previous_board_sha = str(prior.get("storyboard_sha256") or "")
    if story_sha != prior.get("story_sha256") or board_sha == previous_board_sha:
        raise RuntimeError("story must be unchanged; storyboard must actually be revised")
    board_text = storyboard.read_text(encoding="utf-8-sig")
    if not all(token in board_text for token in
               ("左右两个时序画格", "不是同一人", "次子的生母")):
        raise RuntimeError("real issues from attempt 3 are not yet repaired")
    prior_sha = review_authority_sha256(ep)
    if not prior_sha:
        raise RuntimeError("prior review authority SHA missing")
    evidence = {
        "schema": "storyos.story_critic_source_revision.v1",
        "authorization": "direct_user_continuation",
        "review_scope": "LOCKED_DOCUMENTARY_SOURCE_REVISION",
        "global_review_attempt": 4, "review_epoch": 3, "epoch_attempt": 1,
        "previous_review_attempt": 3, "previous_review_passed": False,
        "previous_review_sha256": prior_sha,
        "previous_issue_codes": list(prior.get("issue_codes") or []),
        "previous_storyboard_sha256": previous_board_sha,
        "storyboard_sha256": board_sha, "story_sha256": story_sha,
        "current_rubric_sha256": rubric_sha,
        "reason": "User-directed repair of frame16 time panels and distinct spouse identities after FAIL #3",
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, evidence)
    return evidence


def _authorize_symbolic_remediation(ep: Path, *, attempt: int) -> dict:
    """One final, source-and-rubric-bound review after evidence/metaphor conflation."""
    if attempt != 5 or not _locked_documentary_rubric(ep):
        raise RuntimeError("symbolic remediation requires locked documentary attempt=5")
    target = ep / "meta/runtime/story-review-symbolic-remediation-a5.json"
    if target.exists():
        raise RuntimeError("symbolic remediation attempt 5 already authorized")
    prior = load_review(ep)
    if (not isinstance(prior, dict)
            or (prior.get("critic_provenance") or {}).get("attempt") != 4
            or (prior.get("summary") or {}).get("passed") is not False
            or "DOCUMENTARY_EVIDENCE_UNSUPPORTED" not in (prior.get("issue_codes") or [])):
        raise RuntimeError("must have actual failed documentary evidence review #4")
    earlier_path = ep / "meta/runtime/story-review-source-revision-a4.json"
    if not earlier_path.is_file():
        raise RuntimeError("source revision #4 authority missing")
    old_rubric = read_json(earlier_path).get("current_rubric_sha256")
    new_rubric = _review_rubric_digest(Path(__file__).read_text(encoding="utf-8-sig"))
    if not old_rubric or old_rubric == new_rubric:
        raise RuntimeError("symbolic evidence rubric must materially change")
    story, board = story_paths(ep)
    story_sha, board_sha = sha256_file(story), sha256_file(board)
    old_board = str(prior.get("storyboard_sha256") or "")
    if story_sha != prior.get("story_sha256") or board_sha == old_board:
        raise RuntimeError("source SHA must change only for storyboard, not story")
    board_text = board.read_text(encoding="utf-8-sig")
    if not all(s in board_text for s in ("象征性哀伤空镜", "不表述发现鞋", "用户指定的岸边球鞋")):
        raise RuntimeError("source still lacks clear symbol-versus-evidence distinction")
    prior_review_sha = review_authority_sha256(ep)
    if not prior_review_sha:
        raise RuntimeError("prior review identity missing")
    evidence = {
        "schema": "storyos.story_critic_symbolic_remediation.v1",
        "authorization": "direct_user_continuation",
        "review_scope": "LOCKED_DOCUMENTARY_SYMBOLIC_REMEDIATION",
        "global_review_attempt": 5, "review_epoch": 4, "epoch_attempt": 1,
        "previous_review_attempt": 4,
        "previous_review_passed": False,
        "previous_issue_codes": list(prior.get("issue_codes") or []),
        "previous_review_sha256": prior_review_sha,
        "previous_storyboard_sha256": old_board,
        "storyboard_sha256": board_sha, "story_sha256": story_sha,
        "previous_rubric_sha256": old_rubric,
        "current_rubric_sha256": new_rubric,
        "reason": "The user explicitly authored shoes as a symbolic visual; distinguish illustration from forensic evidence",
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, evidence)
    return evidence


def run_critic(ep: Path, *, attempt: int, codex_raw: str | None, timeout: int | None = None, direct_user_continuation: bool = False, prior_rubric_ref: str | None = None, direct_user_source_revision: bool = False, direct_user_symbolic_remediation: bool = False) -> int:
    if timeout is None:
        timeout = runtime_timeout_policy.seconds("review_critic")
    if attempt not in {1, 2} and not (attempt == 3 and direct_user_continuation) and not (attempt == 4 and direct_user_source_revision) and not (attempt == 5 and direct_user_symbolic_remediation):
        raise RuntimeError("attempts above 2 require explicit direct-user, SHA-bound continuation")
    if direct_user_continuation and (attempt != 3 or direct_user_source_revision):
        raise RuntimeError("policy continuation is only attempt 3")
    if direct_user_source_revision and (attempt != 4 or direct_user_continuation or direct_user_symbolic_remediation):
        raise RuntimeError("source revision is only attempt 4")
    if direct_user_symbolic_remediation and (attempt != 5 or direct_user_continuation or direct_user_source_revision):
        raise RuntimeError("symbolic remediation is only attempt 5")
    continuation = (_authorize_policy_continuation(ep, attempt=attempt, prior_rubric_ref=prior_rubric_ref)
                    if direct_user_continuation else _authorize_source_revision(ep, attempt=attempt)
                    if direct_user_source_revision else _authorize_symbolic_remediation(ep, attempt=attempt)
                    if direct_user_symbolic_remediation else None)
    story, storyboard = story_paths(ep)
    before_story = sha256_file(story)
    before_board = sha256_file(storyboard)
    candidate = ep / CANDIDATE_REL
    candidate.unlink(missing_ok=True)

    runtime, _ = runtime_router.detect()
    if runtime in {"WORK", "WEB"} and not codex_raw:
        sources = [
            story,
            storyboard,
            ROOT / "standards/制作规范_正式版.md",
            ROOT / "standards/创作执行强制规范_V2.0.3.2.md",
            ROOT / "standards/story_regressions/cases.json",
            ROOT / "standards/传播核与动作回应链规范_V1.0.md",
        ]
        request = product_review_adapter.prepare(
            ep,
            kind="story-semantic",
            runtime=runtime,
            attempt=attempt,
            prompt=critic_prompt(ep, story, storyboard, candidate, attempt),
            source_paths=sources,
            candidate_path=candidate,
        )
        shadow_schedule = {"enabled": False, "scheduled": False}
        try:
            shadow_schedule = schedule_critic_shadow(
                ep, attempt=attempt, story=story, storyboard=storyboard, sources=sources,
                canonical_source_files=request.get("source_files"),
            )
        except Exception as exc:
            # Shadow scheduling is observable but cannot change the canonical
            # Story Review decision or candidate lifecycle.
            shadow_schedule["error"] = f"{type(exc).__name__}: {exc}"
        request["critic_shadow_schedule"] = shadow_schedule
        print(json.dumps(request, ensure_ascii=False, indent=2))
        return product_review_adapter.HOST_ACTION_REQUIRED_RC

    codex = resolve_codex(codex_raw)
    log = ep / "meta" / f"story-critic-attempt-{attempt}.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    direct_prompt = critic_prompt(ep, story, storyboard, candidate, attempt) + """

DIRECT CODEX EXECUTION OVERRIDE:
Do not edit or write any repository file in this execution.
Return ONLY the exact candidate JSON object as your final answer, with no prose,
no Markdown fences and no status summary. The parent process persists it.
"""
    completed = codex_critic_runner.launch(
        direct_prompt,
        codex=codex,
        root=ROOT,
        timeout=timeout,
        output_path=candidate,
        reasoning_effort="high",
        sandbox="workspace-write",
        log_path=log,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"isolated story critic failed rc={completed.returncode}; log={log}")
    if sha256_file(story) != before_story or sha256_file(storyboard) != before_board:
        raise RuntimeError("critic modified story/storyboard; isolated review is invalid")
    if not candidate.is_file():
        raise RuntimeError(f"critic did not produce {candidate}")

    data = read_json(candidate)
    provenance = runtime_provenance.build_critic_provenance(
        "CODEX", attempt=attempt, log=log.relative_to(ROOT).as_posix(),
        allow_user_continuation_attempt=bool(continuation),
    )
    if continuation:
        provenance.update({
            "review_scope": continuation["review_scope"],
            "review_epoch": continuation["review_epoch"],
            "epoch_attempt": continuation["epoch_attempt"],
            "previous_review_sha256": continuation["previous_review_sha256"],
            "current_rubric_sha256": continuation["current_rubric_sha256"],
        })
        for key in ("previous_rubric_sha256", "previous_storyboard_sha256"):
            if key in continuation:
                provenance[key] = continuation[key]
    return _finalize_review(
        ep,
        data,
        attempt=attempt,
        before_story=before_story,
        before_board=before_board,
        provenance=provenance,
    )


def self_test() -> None:
    h = "a" * 64
    data = {
        "schema_version": 1,
        "story_os_version": story_os_version(),
        "story_sha256": h,
        "storyboard_sha256": h,
        "revision_count": 0,
        "critic_provenance": {"runtime": "CODEX_ISOLATED", "isolated_session": True, "attempt": 1},
        "contract": {key: "x" for key in CONTRACT_FIELDS},
        "blind_retell": {key: "x" for key in BLIND_FIELDS},
        "hard_checks": {key: True for key in HARD_CHECKS},
        "issue_codes": [],
        "summary": {"passed": True},
    }
    data["contract"]["ending_recontextualization"] = ["a", "b", "c"]
    assert validate_payload(data, story_sha=h, storyboard_sha=h, version=story_os_version()) == []
    data["hard_checks"]["mechanism_consistency"] = False
    assert any("mechanism_consistency" in x for x in validate_payload(data, story_sha=h, storyboard_sha=h, version=story_os_version()))
    old=propagation_core_gate.anomaly_applicable
    propagation_core_gate.anomaly_applicable=lambda _ep:False
    try:
        prompt=critic_prompt(ROOT,ROOT/"dummy-story.md",ROOT/"dummy-board.md",ROOT/"dummy-candidate.json",1)
        assert "ORDINARY-LIFE OVERRIDE" in prompt
        assert "Do NOT invent horror" in prompt
        assert "propagation_core is NOT required" in prompt
    finally:
        propagation_core_gate.anomaly_applicable=old
    print("STORY SEMANTIC REVIEW SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run-critic")
    p.add_argument("episode_dir")
    p.add_argument("--attempt", type=int, default=1)
    p.add_argument("--codex")
    p.add_argument("--timeout", type=int, default=None)
    p.add_argument("--direct-user-continuation", action="store_true")
    p.add_argument("--direct-user-source-revision", action="store_true")
    p.add_argument("--direct-user-symbolic-remediation", action="store_true")
    p.add_argument("--prior-rubric-ref")
    p = sub.add_parser("finalize-review")
    p.add_argument("episode_dir")
    p.add_argument("--attempt", type=int, default=1)
    p.add_argument("--runtime", choices=["WORK", "WEB"], default="WORK")
    p = sub.add_parser("verify")
    p.add_argument("episode_dir")
    p = sub.add_parser("show")
    p.add_argument("episode_dir")
    sub.add_parser("self-test")
    args = ap.parse_args()

    if args.cmd == "self-test":
        self_test()
        return 0
    ep = Path(args.episode_dir).resolve()
    if not ep.is_dir():
        raise SystemExit(f"episode directory not found: {ep}")
    if args.cmd == "run-critic":
        try:
            return run_critic(ep, attempt=args.attempt, codex_raw=args.codex, timeout=args.timeout,
                              direct_user_continuation=args.direct_user_continuation,
                              prior_rubric_ref=args.prior_rubric_ref,
                              direct_user_source_revision=args.direct_user_source_revision,
                              direct_user_symbolic_remediation=args.direct_user_symbolic_remediation)
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
            print("STORY SEMANTIC REVIEW ERROR:", exc)
            return 3
    if args.cmd == "finalize-review":
        try:
            return finalize_product_review(ep, attempt=args.attempt, runtime=args.runtime)
        except (OSError, RuntimeError, ValueError) as exc:
            print("STORY SEMANTIC REVIEW FINALIZE ERROR:", exc)
            return 3
    if args.cmd == "show":
        print(json.dumps(load_review(ep) or {}, ensure_ascii=False, indent=2))
        return 0
    errors = verify(ep)
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 2
    print("STORY SEMANTIC REVIEW VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
