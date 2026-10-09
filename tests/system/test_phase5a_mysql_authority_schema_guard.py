"""The Phase5A TEST_ONLY schema must equal the Generation Attempt authority's schema.

Port 3306 isolates Canary from production 3307. MySQL on Windows/Docker can
hold both upper/lower schema names; accepting the lowercase name while
GenerationAttemptAuthority always selects schema_v2.DATABASE_NAME silently
splits Canary reads and writes. These tests never connect to MySQL.
"""
from __future__ import annotations
from contextlib import contextmanager

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import generation_attempt_authority as attempts
import phase5a_collaborative_canary as canary
import phase5a_initial_canary_input as initial
import storage_config
import storyos_config
from platform.repository.mysql.schema_v2 import DATABASE_NAME


@contextmanager
def _isolated_config():
    with (
        patch.object(storyos_config, "load_config", return_value={}),
        patch.object(storyos_config, "validate", return_value=[]),
        patch.object(storyos_config, "get_path", return_value="COLLABORATIVE"),
    ):
        yield


@pytest.mark.parametrize("port,database", [
    (3306, "story_os_runtime"),  # the split-brain source schema
    (3307, DATABASE_NAME),       # the live production instance
    (3306, "unrelated"),
])
def test_canonical_canary_preflight_denies_wrong_authority_database_before_attempt(
    tmp_path, port, database,
):
    with (
        _isolated_config(),
        patch.object(canary, "authorize_entry"),
        patch.object(canary, "authorize_action"),
        patch.object(canary, "validate_workspace", return_value=(tmp_path, {})),
        patch.object(storage_config, "mysql_connection_kwargs",
                     return_value={"host": "127.0.0.1", "port": port,
                                   "database": database}),
        patch.object(attempts, "load_asset_state") as reserved,
    ):
        with pytest.raises(canary.CanaryContractError, match="CANARY_TEST_ONLY_MYSQL_REQUIRED"):
            canary._preflight(tmp_path, "native-image-proof-20261008")
    reserved.assert_not_called()
    assert not list(tmp_path.iterdir())


def test_canonical_canary_v2_schema_passes_database_gate_before_missing_input(tmp_path):
    with (
        _isolated_config(),
        patch.object(canary, "authorize_entry"),
        patch.object(canary, "authorize_action"),
        patch.object(canary, "validate_workspace", return_value=(tmp_path, {})),
        patch.object(storage_config, "mysql_connection_kwargs",
                     return_value={"host": "127.0.0.1", "port": 3306,
                                   "database": DATABASE_NAME}),
    ):
        with pytest.raises(canary.CanaryContractError, match="CANARY_FRAME_CONTRACT_INPUTS_MISSING"):
            canary._preflight(tmp_path, "native-image-proof-20261008")
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("database,port", [
    ("story_os_runtime", 3306),
    (DATABASE_NAME, 3307),
])
def test_initial_canary_denies_split_or_production_before_claim(tmp_path, database, port):
    with (
        _isolated_config(),
        patch.object(initial.canary, "validate_workspace", return_value=(tmp_path, {})),
        patch.object(initial.storage_config, "mysql_connection_kwargs",
                     return_value={"host": "127.0.0.1", "port": port,
                                   "database": database}),
        patch.object(initial.canary, "claim_global_canary") as claim,
        patch.object(attempts, "load_asset_state") as reserved,
    ):
        with pytest.raises(initial.InitialCanaryPreparationError, match="INITIAL_CANARY_TEST_DB_REQUIRED"):
            initial.prepare(tmp_path, canary_id=initial.INITIAL_CLAIM_ID)
    claim.assert_not_called()
    reserved.assert_not_called()


def test_initial_canary_uppercase_3306_gets_past_database_gate(tmp_path):
    with (
        _isolated_config(),
        patch.object(initial.canary, "validate_workspace", return_value=(tmp_path, {})),
        patch.object(initial.storage_config, "mysql_connection_kwargs",
                     return_value={"host": "127.0.0.1", "port": 3306,
                                   "database": DATABASE_NAME}),
        patch.object(initial.canary, "claim_global_canary",
                     side_effect=RuntimeError("CLAIM_GATE_REACHED")) as claim,
    ):
        with pytest.raises(RuntimeError, match="CLAIM_GATE_REACHED"):
            initial.prepare(tmp_path, canary_id=initial.INITIAL_CLAIM_ID)
    claim.assert_called_once()
