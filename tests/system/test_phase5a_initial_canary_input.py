from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import phase5a_initial_canary_input as prep


def test_initial_canary_refuses_unclaimed_other_id_without_writing(tmp_path):
    with patch.object(prep.canary, "validate_workspace", return_value=(tmp_path, {})):
        with pytest.raises(prep.InitialCanaryPreparationError, match="INITIAL_CANARY_ID_NOT_ALLOWLISTED"):
            prep.prepare(tmp_path, canary_id="unknown-canary")
    assert not list(tmp_path.iterdir())


def test_initial_canary_refuses_stage_file_before_claim(tmp_path):
    (tmp_path / "meta").mkdir()
    (tmp_path / "meta/episode-state.json").write_text("{}", encoding="utf-8")
    with patch.object(prep.canary, "validate_workspace", return_value=(tmp_path, {})):
        with pytest.raises(prep.InitialCanaryPreparationError, match="STAGE_AUTHORITY_FORBIDDEN"):
            prep.prepare(tmp_path, canary_id=prep.INITIAL_CLAIM_ID)


def test_initial_canary_refuses_non_test_db_before_model_or_attempt(tmp_path):
    with (
        patch.object(prep.canary, "validate_workspace", return_value=(tmp_path, {})),
        patch.object(prep.storage_config, "mysql_connection_kwargs", return_value={
            "host": "example.com", "port": 3306, "database": "story_os_runtime",
        }),
        patch.object(prep.canary, "claim_global_canary") as claim,
        patch.object(prep.generation_attempt_authority, "load_asset_state") as attempts,
    ):
        with pytest.raises(prep.InitialCanaryPreparationError, match="TEST_DB_REQUIRED"):
            prep.prepare(tmp_path, canary_id=prep.INITIAL_CLAIM_ID)
    claim.assert_not_called()
    attempts.assert_not_called()
    assert not list(tmp_path.iterdir())
