from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))

import raw_candidate_budget as budget
import machine_action_executor
import next_action
import scheduler_core


def test_episode_budget_authorize_then_terminate_is_auditable_and_effective():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        data = budget.authorize_episode_budget(ep, max_total=40, source="direct_user:test", note="continue episode")
        assert data["status"] == "AUTHORIZED"
        resolved = budget.resolve_limit(ep)
        assert resolved["limit"] == 40
        assert resolved["override_applied"] is True
        closed = budget.terminate_override(ep, source="direct_user:test", reason="stop further generation")
        assert closed["status"] == "TERMINATED"
        status = budget.override_status(ep)
        assert status["active"] is False
        assert budget.resolve_limit(ep)["limit"] == 35


def test_frame_budget_authorization_is_bounded_and_termination_disables_it():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        budget.authorize_frame_budget(ep, frame=7, kind="repair", additional=1, source="direct_user:frame07")
        row = budget.authorized_frame_raise(ep, "07", "repair")
        assert row["extra"] == 1
        assert row["sources"] == ["direct_user:frame07"]
        budget.terminate_override(ep, source="direct_user:frame07", reason="authorization completed")
        assert budget.authorized_frame_raise(ep, "07", "repair")["extra"] == 0


def test_authorization_never_infers_user_approval():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        with pytest.raises(ValueError, match="source"):
            budget.authorize_episode_budget(ep, max_total=40, source="")
        with pytest.raises(ValueError, match="positive"):
            budget.authorize_frame_budget(ep, frame=1, kind="repair", additional=0, source="user")


def test_episode_authorization_resumes_machine_authorized_authority_refresh_lane():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        (ep / "meta").mkdir(parents=True)
        budget.story_json.write_json(ep / "meta/episode-state.json", {"current_state": "PUBLISH_READY"})
        budget.story_json.write_json(ep / "meta/release-manifest.json", {"release": {"body_frame_count": 1}})
        budget.story_json.write_json(ep / "meta/production-ledger.json", {
            "frames": {
                "01": {
                    "authority_refresh_authorization": {
                        "frame_contract_sha256": "current-contract-sha",
                        "approval_text": "direct user authority refresh",
                        "approval_basis": "direct_user_authority_contract_refresh",
                    }
                }
            }
        })
        item = {
            "id": "authority-refresh-blocked-01",
            "frame": 1,
            "kind": "repair",
            "capture_id": "authority-refresh-01",
            "status": "blocked",
            "technical_failure_code": "EPISODE_IMAGE_LOOP_GUARD",
            "frame_contract": {"contract_sha256": "current-contract-sha"},
        }

        # The semantic lane has a configured base limit of zero by design, but a
        # matching authority authorization grants one candidate. The read-side
        # recovery context must mirror claim() and expose that candidate as resumable.
        context = budget.blocked_queue_context(ep, [item])
        assert context["resumable_frames"] == [1]
        row = context["items"][0]
        assert row["kind"] == "authority_refresh"
        assert row["base_limit"] == 0
        assert row["frame_capacity_available"] == 1
        assert row["semantic_authorization_approved"] is True
        assert row["semantic_duplicate"] is False
        assert context["authorization_required"] is False


@pytest.mark.parametrize("failure_code", [
    "RAW_CANDIDATE_BUDGET_EXHAUSTED",
    "EPISODE_IMAGE_LOOP_GUARD",
])
def test_exhausted_frame_budget_routes_to_user_then_machine_resume_after_authorization(failure_code):
    # This test exercises logical Episode behavior, not repository-local path
    # routing. Keep the fixture outside the checkout so W-77 production guards
    # remain strict for every repository-local Episode path.
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        (ep / "meta").mkdir(parents=True)
        budget.story_json.write_json(ep / "meta/episode-state.json", {"current_state": "VISUAL_CALIBRATED"})
        budget.story_json.write_json(ep / "meta/release-manifest.json", {"release": {"body_frame_count": 1}})
        # Consume the ordinary repair lane's two retained candidates.
        for idx in (1, 2):
            ok, row = budget.claim(ep, 1, "repair", token=f"repair-{idx}")
            assert ok, row
            ok, row = budget.commit(ep, f"repair-{idx}")
            assert ok, row
        item = {
            "id": "repair-blocked-01", "frame": 1, "kind": "repair", "scope": "batch",
            "status": "blocked", "technical_failure_code": failure_code,
            "last_error": f"{failure_code}: STOP_IMAGE_LOOP",
        }
        scheduler_core.save_queue(ep, {"schema_version": 1, "items": [item], "waves": []})

        blocked = next_action.derive(ep)
        assert blocked["action"] == "USER_DECISION_REQUIRED"
        assert blocked["decision_kind"] == "CANDIDATE_BUDGET_EXHAUSTED"
        assert blocked["budget"]["authorization_required"] is True
        assert any(row["kind"] == "frame" and row["frame"] == 1 for row in blocked["budget"]["authorization_options"])

        budget.authorize_frame_budget(ep, frame=1, kind="repair", additional=1, source="direct_user:test")
        resumable = next_action.derive(ep)
        assert resumable["action"] == "RESUME_BUDGET_AUTHORIZED_IMAGES"
        assert resumable["executor"] == "MACHINE"
        result = machine_action_executor.execute(ep, resumable)
        assert result["status"] == "PASS"
        queue = scheduler_core.load_queue(ep)
        assert queue["items"][0]["status"] == "queued"
        assert queue["items"][0].get("technical_failure_code") is None
