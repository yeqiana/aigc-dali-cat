#!/usr/bin/env python3
"""Target persistence classifier for legacy Episode assets.

This does not move or delete data.  It is the registry that future migration
jobs use to decide whether a legacy path belongs in MySQL, Redis, or files.
"""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path

MYSQL = "MYSQL"
REDIS = "REDIS"
FILE = "FILE"
EXPORT_ONLY = "EXPORT_ONLY"
UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class StorageDecision:
    target: str
    legacy_file: str
    family: str
    reason: str


_DERIVED_CONFIG_SNAPSHOT_REL = "meta/runtime/" + "effective-" + "config.json"


RULES: tuple[tuple[str, StorageDecision], ...] = (
    ("media/**", StorageDecision(FILE, "KEEP", "media", "binary/media assets stay in file or object storage")),
    ("meta/preimage-revisions/**", StorageDecision(FILE, "MOVE_TO_ARCHIVE", "historical_revision_snapshot", "legacy full-directory revision snapshots belong in history/archive, not active Episode metadata")),
    ("meta/image-workers/**", StorageDecision(FILE, "LOCAL_ONLY", "runtime_worker_log", "raw worker lifecycle/noise logs are local diagnostics; durable attempt facts belong in MySQL")),
    ("meta/provider-receipts/*.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "provider_receipt", "durable provider call history")),
    ("meta/frame-reviews/*.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "frame_review", "queryable frame review history")),
    ("meta/frame-scouts/*.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "frame_scout", "queryable scout review history")),
    ("meta/runtime/contracts/frames/*.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "frame_contract", "versioned frame contract")),
    ("meta/runtime/contracts/character-appearance-anchor.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "episode_contract", "derived character appearance contract")),
    ("meta/runtime/contracts/frame-contract-index.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "frame_contract", "Frame Contract index/projection")),
    ("meta/runtime/reviews/*.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "runtime_review", "durable review request/evidence")),
    ("meta/runtime/host-requests/*.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "host_request", "durable Host/PREIMAGE request history")),
    ("meta/runtime/preimage-candidates/*.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "preimage_candidate", "versioned PREIMAGE candidate")),
    ("meta/runtime/prompt-packages/*.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "prompt_package", "generated prompt package history")),
    ("meta/runtime/execution-capsules/*.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "execution_capsule", "task execution capsule is durable task evidence")),
    ("meta/runtime/rolling-reviews/*.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "runtime_review", "rolling review history")),
    ("meta/runtime/batch-repair-decisions/*.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "review", "durable batch repair decision")),
    ("meta/batch-repair-decisions/*.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "review", "durable batch repair decision")),
    ("meta/production-ledger.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "production", "durable current frame facts plus attempt links")),
    ("meta/runtime-checkpoint.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "workflow", "durable workflow/task evidence")),
    ("meta/runtime-dag-state.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "workflow", "durable workflow projection")),
    ("meta/episode-state.json", StorageDecision(MYSQL, "EXPORT_ONLY", "episode_state", "final authority target; migrate last after dual-write verification")),
    ("meta/runtime-request.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "runtime_request", "durable user/runtime request")),
    ("meta/runtime/preimage-task-state.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "preimage", "durable PREIMAGE task state")),
    ("meta/runtime/preimage-authority-snapshot.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "preimage", "versioned authority snapshot")),
    ("meta/runtime/preimage-committed-snapshot.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "preimage", "committed PREIMAGE authority snapshot")),
    ("meta/runtime/preimage-authority-barrier.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "preimage", "durable authority barrier event")),
    ("meta/runtime/production-commit-journal.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "production", "durable commit journal")),
    ("meta/runtime/production-reconciliation.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "production", "durable reconciliation evidence")),
    ("meta/*-contract.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "episode_contract", "versioned Episode contract")),
    ("meta/*-review.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "review", "durable Episode review")),
    ("meta/*-audit.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "review", "durable audit/review evidence")),
    ("meta/*.draft.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "review_draft", "review draft/version belongs in review history")),
    ("meta/*.json.pre-*.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "review_revision", "legacy pre-change copy should become a versioned review record")),
    ("meta/.*.candidate.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "review_candidate", "temporary review candidate should become task/review evidence")),
    ("meta/story-gates.json", StorageDecision(MYSQL, "EXPORT_ONLY", "gate", "gate evidence is durable queryable authority")),
    ("meta/episode-fingerprint.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "fingerprint", "episode fingerprint is a durable derived fact")),
    ("meta/concept-candidates.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "concept", "concept candidate history is durable creative evidence")),
    ("meta/resource-selection.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "resource_selection", "resolved resource selection is durable workflow input")),
    ("meta/directing-quality.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "episode_contract", "directing quality contract/evidence")),
    ("meta/intro-policy.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "episode_contract", "episode intro policy")),
    ("meta/opening-social-anchor.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "episode_contract", "opening social anchor contract")),
    ("meta/performance-budget.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "episode_contract", "episode performance budget")),
    ("meta/preproduction-handoff.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "preimage", "durable verified preproduction handoff")),
    ("meta/text-audit.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "review", "text audit evidence")),
    ("meta/publish-compliance.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "review", "publish compliance evidence")),
    ("meta/story-dna-trace.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "fingerprint", "Story DNA trace is queryable learning evidence")),
    ("meta/visual-lock-plan.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "episode_contract", "Visual Lock plan is versioned production intent")),
    ("meta/visual-lock-admissions.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "review", "Visual Lock admission decisions are durable evidence")),
    ("meta/visual-lock-final-report.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "review", "Visual Lock final report is durable review evidence")),
    ("meta/visual-critic-runtime.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "review", "critic runtime outcome belongs with review/task evidence")),
    ("meta/visual-final-freeze.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "release", "visual freeze is durable release authority")),
    ("meta/visual-profile.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "episode_contract", "episode visual profile contract")),
    ("meta/visual-narrative-core.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "episode_contract", "visual narrative contract")),
    ("meta/recommendation-fit.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "review", "recommendation review evidence")),
    ("meta/delegated-release.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "release", "delegated release evidence")),
    ("meta/asset-lineage.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "artifact", "artifact lineage is queryable durable metadata")),
    ("meta/media-index.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "artifact", "media index belongs in Artifact metadata")),
    ("meta/temporal-continuity.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "episode_contract", "temporal continuity contract")),
    ("meta/world-state.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "episode_contract", "world state contract")),
    ("meta/world-identity.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "episode_contract", "world identity override contract")),
    ("meta/world_identity.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "episode_contract", "legacy world identity contract")),
    ("meta/Environment_Contract.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "episode_contract", "legacy environment contract")),
    ("contracts/*.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "episode_contract", "legacy Episode contract file")),
    ("meta/subtitle-layout.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "release", "subtitle layout is versioned release intent")),
    ("meta/final-acceptance.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "approval", "final user acceptance is durable approval evidence")),
    ("meta/frame-scout-summary.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "review", "frame scout aggregate review")),
    ("meta/preproduction-validation.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "preimage", "preproduction validation evidence")),
    ("meta/release-package.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "release", "release package metadata")),
    ("meta/DELEGATED_AUTO_REPORT.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "approval", "delegated automation report")),
    ("meta/frame-semantic-*.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "review", "frame semantic review attempt history")),
    ("publish/**/assembly-audit.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "release", "publish assembly audit")),
    ("meta/batch-provider-capability.json", StorageDecision(REDIS, "REMOVE_AFTER_CUTOVER", "hot_state", "provider capability is rebuildable runtime cache")),
    ("meta/codex-subscription-batch-capability.json", StorageDecision(REDIS, "REMOVE_AFTER_CUTOVER", "hot_state", "provider capability is rebuildable runtime cache")),
    ("meta/delegated-approvals.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "approval", "durable delegated approval")),
    ("meta/production-approval.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "approval", "durable production approval")),
    ("meta/episode-performance-ledger.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "metrics", "durable performance facts and aggregate input")),
    ("meta/workflow-performance.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "metrics", "derived performance snapshot")),
    ("meta/workflow-observability.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "metrics", "derived observability snapshot")),
    ("meta/image-scheduler-performance.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "metrics", "scheduler metric snapshot")),
    ("meta/batch-runtime-performance.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "metrics", "batch metric snapshot")),
    ("meta/quota-observability.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "metrics", "quota metric snapshot")),
    ("meta/release-manifest.json", StorageDecision(MYSQL, "EXPORT_ONLY", "release", "release projection should be exportable from durable records")),
    ("meta/final-candidate-snapshot.json", StorageDecision(MYSQL, "EXPORT_ONLY", "release", "frozen release snapshot retained as export view")),
    ("meta/runtime/next-action.json", StorageDecision(REDIS, "REMOVE_AFTER_CUTOVER", "hot_state", "rebuildable current action")),
    ("meta/runtime/driver-beacon.json", StorageDecision(REDIS, "REMOVE_AFTER_CUTOVER", "hot_state", "short-lived driver heartbeat")),
    ("meta/runtime/driver.json", StorageDecision(REDIS, "REMOVE_AFTER_CUTOVER", "hot_state", "current driver projection")),
    ("meta/runtime/circuit-breaker.json", StorageDecision(REDIS, "REMOVE_AFTER_CUTOVER", "hot_state", "rebuildable circuit-breaker state")),
    ("meta/runtime/in-flight-codex.json", StorageDecision(REDIS, "REMOVE_AFTER_CUTOVER", "hot_state", "short-lived in-flight execution pointer")),
    ("meta/runtime/product-host-request.json", StorageDecision(REDIS, "REMOVE_AFTER_CUTOVER", "hot_state", "current Host request pointer; request history stays in MySQL")),
    (_DERIVED_CONFIG_SNAPSHOT_REL, StorageDecision(REDIS, "REMOVE_AFTER_CUTOVER", "hot_state", "rebuildable config projection")),
    ("meta/runtime/runtime-capabilities.json", StorageDecision(REDIS, "REMOVE_AFTER_CUTOVER", "hot_state", "short-lived runtime capability cache")),
    ("meta/runtime/fast-path-state.json", StorageDecision(REDIS, "REMOVE_AFTER_CUTOVER", "hot_state", "rebuildable fast-path state")),
    ("meta/runtime/resume-capsule.json", StorageDecision(REDIS, "REMOVE_AFTER_CUTOVER", "hot_state", "rebuildable resume projection")),
    ("meta/runtime/full-auto-status.json", StorageDecision(REDIS, "REMOVE_AFTER_CUTOVER", "hot_state", "current full-auto status projection")),
    ("meta/runtime/trace-current.json", StorageDecision(REDIS, "REMOVE_AFTER_CUTOVER", "hot_state", "current trace pointer")),
    ("meta/runtime/trace-summary.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "metrics", "trace summary is a durable metric projection")),
    ("meta/runtime-route.json", StorageDecision(REDIS, "REMOVE_AFTER_CUTOVER", "hot_state", "route decision can be rebuilt from request/config")),
    ("meta/runtime-resume-token.json", StorageDecision(REDIS, "REMOVE_AFTER_CUTOVER", "hot_state", "short-lived resume token")),
    ("meta/runtime-runner-state.json", StorageDecision(REDIS, "REMOVE_AFTER_CUTOVER", "hot_state", "current runner projection")),
    ("meta/runtime/raw-candidate-budget.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "budget", "candidate budget must survive Redis loss; hot counters may be cached")),
    ("meta/runtime/raw-candidate-budget-override.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "budget", "budget override is auditable authorization")),
    ("meta/runtime/runtime-execution.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "workflow", "runtime execution history/projection")),
    ("meta/runtime-execution.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "workflow", "legacy runtime execution history/projection")),
    ("meta/runtime/transport-state.json", StorageDecision(REDIS, "REMOVE_AFTER_CUTOVER", "hot_state", "current transport state is rebuildable")),
    ("meta/transport-state.json", StorageDecision(REDIS, "REMOVE_AFTER_CUTOVER", "hot_state", "current transport state is rebuildable")),
    ("meta/runtime/image-model-migration.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "migration", "image-model migration audit record")),
    ("meta/runtime/frame-contract-projection-migrations.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "migration", "Frame Contract projection migration audit")),
    ("meta/runtime/provisional-release.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "release", "provisional release projection")),
    ("meta/.release-critic-request-stdout.json", StorageDecision(FILE, "LOCAL_ONLY", "runtime_worker_log", "raw critic stdout is local diagnostic; durable review result belongs in MySQL")),
    ("meta/production-queue.json", StorageDecision(REDIS, "REMOVE_AFTER_CUTOVER", "hot_state", "hot queue belongs in Redis; durable attempts/tasks belong in MySQL")),
    ("meta/character-pixel-master.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "artifact", "pixel-master metadata belongs in DB; image bytes stay in media")),
    ("meta/character-master-crops.json", StorageDecision(MYSQL, "REMOVE_AFTER_CUTOVER", "artifact", "crop manifest belongs in DB; crop images stay in media")),
)


def classify(rel_path: str | Path) -> StorageDecision:
    rel = Path(rel_path).as_posix().lstrip("./")
    for pattern, decision in RULES:
        if fnmatch.fnmatch(rel, pattern):
            return decision
    if rel.startswith("meta/tests/") and rel.endswith(".json"):
        return StorageDecision(FILE, "MOVE_TO_TEST_FIXTURES", "test_fixture", "test fixtures must not live in production Episode metadata")
    if rel.endswith(".json"):
        return StorageDecision(UNKNOWN, "AUDIT_REQUIRED", "unclassified_json", "new long-lived Episode JSON requires explicit storage ownership")
    return StorageDecision(FILE, "KEEP", "source_or_media", "non-JSON source or media asset")


def inventory_episode(episode_dir: str | Path) -> dict[str, int]:
    ep = Path(episode_dir)
    counts = {MYSQL: 0, REDIS: 0, FILE: 0, EXPORT_ONLY: 0, UNKNOWN: 0}
    for path in ep.rglob("*"):
        if not path.is_file():
            continue
        decision = classify(path.relative_to(ep))
        counts[decision.target] = counts.get(decision.target, 0) + 1
        if decision.legacy_file == "EXPORT_ONLY":
            counts[EXPORT_ONLY] += 1
    return counts

