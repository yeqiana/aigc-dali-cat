from __future__ import annotations

import inspect
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import release_preflight_core
import release_preflight_review
import release_preflight_verify


POLICY_FIELDS = {
    "ai_generated_declared",
    "platform_ai_label_planned",
    "fiction_context_not_misrepresented_as_official_fact",
}


def test_release_semantic_checks_keep_content_safety_but_not_policy_authority():
    checks = set(release_preflight_core.RELEASE_CHECKS)
    assert "no_unverifiable_real_group_accusation" in checks
    assert "real_location_handled_as_fictional_story_context" in checks
    assert checks.isdisjoint(POLICY_FIELDS)
    assert not hasattr(release_preflight_core, "GOV_CHECKS")


def test_release_critic_prompt_schema_has_no_governance_decision_block():
    source = inspect.getsource(release_preflight_review.release_critic_prompt)
    assert "governance_checks" not in source
    assert "platform_ai_label_planned" not in source
    assert "ai_generated_declared" not in source
    assert "publish-compliance.json" in source
    assert "verify_governance" in source


def test_governance_verifier_reads_compliance_not_release_critic_authority():
    source = inspect.getsource(release_preflight_verify.verify_governance)
    assert "COMPLIANCE_REL" in source
    assert "RELEASE_REVIEW_REL" not in source
    assert "release-semantic-review" not in source


def test_legacy_governance_fields_do_not_grant_or_block_release_semantic_authority(tmp_path: Path):
    ep = tmp_path / "episode"
    ep.mkdir()
    data = {
        "schema_version": 1,
        "story_os_version": "2.6.1",
        "artifacts": {"body01": {"path": "x", "sha256": "a"}},
        "critic_provenance": {"legacy": True},
        "release_checks": {key: True for key in release_preflight_core.RELEASE_CHECKS},
        "governance_checks": {
            "ai_generated_declared": False,
            "platform_ai_label_planned": False,
        },
        "issue_codes": [],
        "summary": {"passed": True},
    }
    with mock.patch.object(release_preflight_review, "episode_contract_version", return_value="2.6.1"), \
         mock.patch.object(release_preflight_review, "release_hashes", return_value=data["artifacts"]), \
         mock.patch.object(release_preflight_review.runtime_provenance, "validate_critic_provenance", return_value=[]):
        assert release_preflight_review.validate_release_review(ep, data) == []
