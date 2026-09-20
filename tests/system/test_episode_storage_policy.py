from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import episode_storage_policy as policy


def test_high_volume_json_families_target_mysql():
    for rel in (
        "meta/provider-receipts/01-1.json",
        "meta/frame-reviews/01.json",
        "meta/frame-scouts/01.json",
        "meta/runtime/contracts/frames/01.json",
        "meta/runtime/host-requests/host-1.json",
        "meta/runtime/prompt-packages/01.json",
    ):
        assert policy.classify(rel).target == policy.MYSQL


def test_rebuildable_runtime_state_targets_redis():
    for rel in (
        "meta/runtime/next-action.json",
        "meta/runtime/driver-beacon.json",
        "meta/runtime/circuit-breaker.json",
        "meta/runtime/product-host-request.json",
        "meta/production-queue.json",
    ):
        assert policy.classify(rel).target == policy.REDIS


def test_media_remains_file_and_unknown_json_fails_classification():
    assert policy.classify("media/approved/01.png").target == policy.FILE
    unknown = policy.classify("meta/surprise-new-state.json")
    assert unknown.target == policy.UNKNOWN
    assert unknown.legacy_file == "AUDIT_REQUIRED"


def test_release_projection_is_mysql_with_export_only_legacy_file():
    decision = policy.classify("meta/release-manifest.json")
    assert decision.target == policy.MYSQL
    assert decision.legacy_file == "EXPORT_ONLY"


def test_validation_and_post_publish_reports_have_explicit_ownership():
    for rel, family in (
        ("meta/validation/bootstrap_validation_report.json", "validation"),
        ("meta/validation/preproduction_validation_report.json", "validation"),
        ("meta/preproduction-validation.json", "validation"),
        ("meta/post-publish-metrics.json", "metrics"),
        ("meta/post-publish-review.json", "review"),
        ("meta/next-story-learning.json", "learning"),
        ("meta/publish-event.json", "publication"),
    ):
        decision = policy.classify(rel)
        assert decision.target == policy.MYSQL
        assert decision.legacy_file == "REMOVE_AFTER_CUTOVER"
        assert decision.family == family


def test_historical_revision_and_worker_logs_leave_active_episode_metadata():
    revision = policy.classify("meta/preimage-revisions/20260909/before/meta/story-gates.json")
    assert revision.target == policy.FILE
    assert revision.legacy_file == "MOVE_TO_ARCHIVE"
    worker = policy.classify("meta/image-workers/03-a1.lifecycle.json")
    assert worker.target == policy.FILE
    assert worker.legacy_file == "LOCAL_ONLY"


def test_gates_budgets_and_runtime_projections_have_explicit_targets():
    assert policy.classify("meta/story-gates.json").target == policy.MYSQL
    assert policy.classify("meta/runtime/raw-candidate-budget.json").target == policy.MYSQL
    assert policy.classify("meta/runtime/trace-current.json").target == policy.REDIS
    assert policy.classify("meta/runtime/trace-summary.json").target == policy.MYSQL
    assert policy.classify("meta/runtime-execution.json").target == policy.MYSQL


def test_runtime_metric_documents_target_mysql():
    decision = policy.classify("meta/runtime/metrics/workflow_performance-deadbeef.json")
    assert decision.target == policy.MYSQL
    assert decision.legacy_file == "REMOVE_AFTER_CUTOVER"
    assert decision.family == "metrics"


def test_externalized_runtime_documents_stay_file_artifacts():
    for rel, family in (
        ("meta/runtime/approvals/DELEGATED_BUNDLE-deadbeef.json", "approval_document"),
        ("meta/runtime/releases/DELEGATED_DELIVERY-deadbeef.json", "release_document"),
        ("meta/runtime/review-documents/frame-semantic-deadbeef.json", "review_document"),
        ("meta/runtime/checkpoint-events/deadbeef.json", "checkpoint_document"),
    ):
        decision = policy.classify(rel)
        assert decision.target == policy.FILE
        assert decision.family == family
def test_phase95_historical_unknown_inventory_has_explicit_owners():
    expected = {
        "02_折多山守夜人/scripts/sub_data.json": (policy.FILE, "historical_source_data"),
        "09_旧物怪谈/01_回村中巴捡MP4/docs/manifest.json": (policy.FILE, "historical_document_manifest"),
        "10_彼此的天上/01_不存在的夜行路/publish/_manual_20260903_approved_test_album/assembly-audit.json": (policy.MYSQL, "release"),
        "meta/series-character-identity.json": (policy.MYSQL, "series_identity_contract"),
        "meta/v21-narrative-upgrade.json": (policy.MYSQL, "migration"),
        "11_仲夏夜惊魂/01_惊魂/contracts/Character_Appearance_Anchor.json": (policy.MYSQL, "episode_contract"),
        "11_仲夏夜惊魂/01_惊魂/contracts/Character_Contract.json": (policy.MYSQL, "episode_contract"),
        "meta/asset-manifest.json": (policy.MYSQL, "artifact"),
        "meta/chapter-lock.json": (policy.MYSQL, "episode_contract"),
        "meta/episode-blueprint.json": (policy.MYSQL, "episode_contract"),
        "_archive/.storyos-non-episode.json": (policy.FILE, "archive_metadata"),
        "meta/episode-abandoned.json": (policy.FILE, "archive_metadata"),
        "_archive/relocations.json": (policy.FILE, "archive_metadata"),
        "_system/MODULE_INDEX.json": (policy.FILE, "system_manifest"),
    }

    for rel, (target, family) in expected.items():
        decision = policy.classify(rel)
        assert decision.target == target, rel
        assert decision.family == family, rel
        assert decision.target != policy.UNKNOWN, rel
