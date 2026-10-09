from __future__ import annotations

import concurrent.futures
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import generation_attempt_authority as authority
import image_generation_gateway
import raw_candidate_budget
import production_revision_authority as revision_authority
from platform.repository.mysql.mysql_connection import MySqlConnection
from platform.repository.mysql.schema_v2 import DDL_STEPS, DATABASE_NAME


def _test_connection_factory():
    from _isolated_mysql_authority import connection_factory
    return connection_factory()


class GenerationAttemptAuthorityMySqlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.connection_factory = staticmethod(_test_connection_factory())
            conn = cls.connection_factory()
            conn.health_check()
            for name, sql in DDL_STEPS:
                if name in {"create_generation_asset_state", "create_generation_attempt",
                            "create_production_revision", "create_production_revision_head",
                            "create_production_revision_frame"}:
                    conn.execute(sql)
            conn.close()
        except Exception as exc:
            raise RuntimeError("ISOLATED_MYSQL_AUTHORITY_TEST_FAILED") from exc

    def setUp(self):
        self.connection_patch = patch.object(authority, "_connect", self.connection_factory)
        self.connection_patch.start()
        self.revision_connection_patch = patch.object(revision_authority, "_connect", self.connection_factory)
        self.revision_connection_patch.start()
        self.temp = tempfile.TemporaryDirectory(prefix="storyos-generation-authority-")
        self.ep = Path(self.temp.name)
        self.key = authority.frame_key(self.ep, 3)

    def tearDown(self):
        self.connection_patch.stop()
        self.revision_connection_patch.stop()
        self.temp.cleanup()

    def _reserve(self, key=None, **kwargs):
        return authority.reserve(self.ep, key or self.key, {"model_role": "image.payload", "payload_model": "gpt-image-2"}, **kwargs)

    def _revision_context(self, revision_id):
        return {"model_role": "image.payload", "payload_model": "gpt-image-2",
                "production_revision_id": revision_id,
                "frame_contract_sha256": "a" * 64, "prompt_package_sha256": "b" * 64}

    def _prepare_and_activate_revision(self, previous=None):
        row = revision_authority.create_preparing(
            self.ep, input_sha256="c" * 64,
            frames=[{"frame": frame, "frame_contract_sha256": "a" * 64,
                     "prompt_sha256": "b" * 64} for frame in range(1, 26)])
        connection = self.connection_factory()
        try:
            if previous:
                connection.execute("UPDATE TB_PRODUCTION_REVISION SET STATUS='RETIRED',RETIRED_AT=UTC_TIMESTAMP(6) WHERE PRODUCTION_REVISION_ID=%s", (previous,))
            connection.execute("UPDATE TB_PRODUCTION_REVISION SET STATUS='ACTIVE',ACTIVATED_AT=UTC_TIMESTAMP(6) WHERE PRODUCTION_REVISION_ID=%s", (row["production_revision_id"],))
            connection.execute("UPDATE TB_PRODUCTION_REVISION_HEAD SET ACTIVE_REVISION_ID=%s WHERE EPISODE_ID=%s", (row["production_revision_id"], row["episode_id"]))
        finally:
            connection.close()
        return row

    def test_revision_dispatch_binding_keeps_attempt_budget_shared_across_revisions(self):
        first = self._prepare_and_activate_revision()
        first_lease = authority.reserve(self.ep, self.key, self._revision_context(first["production_revision_id"]))
        self._consume(first_lease)
        with self.assertRaisesRegex(authority.AttemptDenied, "PRODUCTION_REVISION_BINDING_REQUIRED"):
            self._reserve()

        second = self._prepare_and_activate_revision(previous=first["production_revision_id"])
        second_lease = authority.reserve(self.ep, self.key, self._revision_context(second["production_revision_id"]))
        self.assertEqual(second_lease["attempt_index"], 2)
        self._consume(second_lease)
        with self.assertRaisesRegex(authority.AttemptDenied, "GENERATION_ATTEMPT_BUDGET_EXHAUSTED"):
            authority.reserve(self.ep, self.key, self._revision_context(second["production_revision_id"]))
        state = authority.load_asset_state(self.ep, self.key)
        self.assertEqual(state["attempts_consumed"], 2)

    def _consume(self, lease):
        authority.commit_dispatch(self.ep, lease, lease["fencing_token"], provider="fake")
        authority.succeed(self.ep, lease, lease["fencing_token"], result_ref="fake://candidate")

    def test_episode_generation_cap_is_only_aggregate_audit(self):
        keys = [f"episode/frame-{index:02d}" for index in range(1, 21)] + ["episode/cover/main"]
        self.assertEqual(authority.episode_hard_generation_cap(keys), 42)
        self.assertEqual(authority.MAX_REAL_IMAGE_GENERATION_ATTEMPTS_PER_ASSET, 2)

    def test_atomic_reserve_single_inflight_and_last_slot_race(self):
        first = self._reserve()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(self._reserve) for _ in range(2)]
            results = []
            for future in futures:
                try:
                    results.append(future.result())
                except authority.AttemptDenied as exc:
                    results.append(exc.code)
        self.assertEqual(sum(isinstance(row, dict) for row in results), 0)
        authority.release_pre_dispatch(self.ep, first, first["fencing_token"], "test")

        self._consume(self._reserve())
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(self._reserve) for _ in range(2)]
            outcomes = []
            for future in futures:
                try:
                    outcomes.append(future.result())
                except authority.AttemptDenied as exc:
                    outcomes.append(exc.code)
        self.assertEqual(sum(isinstance(row, dict) for row in outcomes), 1)
        self.assertTrue(any(value in {"GENERATION_ATTEMPT_ALREADY_ACTIVE", "GENERATION_ATTEMPT_BUDGET_EXHAUSTED"}
                            for value in outcomes if isinstance(value, str)))
        winner = next(row for row in outcomes if isinstance(row, dict))
        self._consume(winner)
        with self.assertRaisesRegex(authority.AttemptDenied, "GENERATION_ATTEMPT_BUDGET_EXHAUSTED"):
            self._reserve()

    def test_fence_expiry_pre_dispatch_and_post_dispatch_crash(self):
        old = self._reserve(lease_seconds=1)
        connection = self.connection_factory()
        connection.execute("UPDATE TB_GENERATION_ATTEMPT SET LEASE_EXPIRES_AT=UTC_TIMESTAMP(6)-INTERVAL 1 SECOND WHERE EPISODE_ID=%s AND LOGICAL_ASSET_KEY=%s AND ATTEMPT_INDEX=1",
                           (old["episode_id"], old["logical_asset_key"]))
        connection.close()
        fresh = self._reserve()
        self.assertEqual(fresh["attempt_index"], 1)
        self.assertGreater(fresh["fencing_token"], old["fencing_token"])
        with self.assertRaisesRegex(authority.AttemptDenied, "STALE_GENERATION_ATTEMPT_FENCE"):
            authority.commit_dispatch(self.ep, old, old["fencing_token"], provider="fake")
        authority.release_pre_dispatch(self.ep, fresh, fresh["fencing_token"], "pre-dispatch crash recovery")
        self.assertEqual(authority.load_asset_state(self.ep, self.key)["attempts_consumed"], 0)

        post = self._reserve()
        authority.commit_dispatch(self.ep, post, post["fencing_token"], provider="fake")
        connection = self.connection_factory()
        connection.execute("UPDATE TB_GENERATION_ATTEMPT SET LEASE_EXPIRES_AT=UTC_TIMESTAMP(6)-INTERVAL 1 SECOND WHERE EPISODE_ID=%s AND LOGICAL_ASSET_KEY=%s AND ATTEMPT_INDEX=1",
                           (post["episode_id"], post["logical_asset_key"]))
        connection.close()
        second = self._reserve()
        self.assertEqual(second["attempt_index"], 2)
        self.assertEqual(authority.load_asset_state(self.ep, self.key)["attempts_consumed"], 1)
        authority.release_pre_dispatch(self.ep, second, second["fencing_token"], "test cleanup")

    def test_duplicate_dispatch_terminal_idempotency_and_shared_scope_key(self):
        visual = authority.frame_key(self.ep, "frame-03")
        production = authority.frame_key(self.ep, 3)
        repair = authority.frame_key(self.ep, "03")
        self.assertEqual({visual, production, repair}, {self.key})
        lease = self._reserve(visual)
        authority.commit_dispatch(self.ep, lease, lease["fencing_token"], provider="fake")
        with self.assertRaises(authority.AttemptDenied):
            authority.commit_dispatch(self.ep, lease, lease["fencing_token"], provider="fake")
        result = authority.succeed(self.ep, lease, lease["fencing_token"], result_ref="fake://candidate")
        self.assertEqual(result["status"], "SUCCEEDED")
        self.assertTrue(authority.succeed(self.ep, lease, lease["fencing_token"], result_ref="same")["idempotent"])
        self.assertEqual(authority.load_asset_state(self.ep, self.key)["attempts_consumed"], 1)

    def test_gateway_requires_lease_and_user_asset_recovery_do_not_consume(self):
        called = []
        with self.assertRaisesRegex(authority.AttemptDenied, "GENERATION_ATTEMPT_LEASE_REQUIRED"):
            image_generation_gateway.provider_generate(self.ep, None, None, "fake", lambda: called.append(1))
        self.assertEqual(called, [])
        adopted = image_generation_gateway.adopt_user_asset(
            self.ep, asset_ref="user://image", logical_asset_key=self.key
        )
        recovered = image_generation_gateway.recover_existing_raw(receipt={"sha256": "a" * 64}, generation_key="old-generation-key")
        self.assertEqual(adopted["source"], "USER_SUPPLIED")
        self.assertEqual(recovered["source"], "EXISTING_PROVIDER_RAW")
        self.assertEqual(authority.load_asset_state(self.ep, self.key)["attempts_consumed"], 0)

    def test_pre_dispatch_release_reuses_same_generation_key_and_legacy_over_cap_fails_closed(self):
        first = self._reserve()
        generation_key = first["generation_key"]
        authority.release_pre_dispatch(self.ep, first, first["fencing_token"], "model unavailable before dispatch")
        retry = authority.reserve(self.ep, self.key, {"model_role": "image.payload", "payload_model": "fallback"})
        self.assertEqual(retry["attempt_index"], 1)
        self.assertEqual(retry["generation_key"], generation_key)
        authority.release_pre_dispatch(self.ep, retry, retry["fencing_token"], "test cleanup")
        with self.assertRaisesRegex(authority.AttemptDenied, "GENERATION_ATTEMPT_BUDGET_EXHAUSTED"):
            authority.reserve(self.ep, self.key, legacy_consumed=3)

    def test_native_batch_commit_is_atomic_and_recovery_closes_same_attempt(self):
        other_key = authority.logical_asset_identity.non_frame_asset_key(self.ep, "cover", "main")
        first = self._reserve()
        second = self._reserve(other_key)
        called = []
        stale_second = {**second, "fencing_token": second["fencing_token"] + 1}
        with self.assertRaisesRegex(authority.AttemptDenied, "STALE_GENERATION_ATTEMPT_FENCE"):
            image_generation_gateway.provider_generate_many(
                self.ep, [first, stale_second], "fake", lambda: called.append("must-not-run"))
        self.assertEqual(called, [])
        self.assertEqual(authority.load_asset_state(self.ep, self.key)["attempts_consumed"], 0)
        result = image_generation_gateway.provider_generate_many(
            self.ep, [first, second], "fake", lambda: called.append("provider") or {"ok": True})
        self.assertEqual(called, ["provider"])
        self.assertEqual(result, {"ok": True})
        self.assertEqual(authority.load_asset_state(self.ep, self.key)["attempts_consumed"], 1)
        recovered = authority.complete_external_generation(
            self.ep, self.key, first["generation_key"], result_ref="fake://recovered-raw")
        self.assertTrue(recovered["attempt_consumed"])
        self.assertTrue(recovered.get("idempotent", False) is False)
        self.assertEqual(authority.load_asset_state(self.ep, self.key)["attempts_consumed"], 1)

    def test_compatibility_facade_uses_mysql_lease_not_json_claim(self):
        ok, row = raw_candidate_budget.claim(
            self.ep, 3, "repair", token="facade-test",
            generation_context={"model_role": "image.payload", "payload_model": "gpt-image-2"},
        )
        self.assertTrue(ok, row)
        self.assertEqual(row["lease"]["logical_asset_key"], self.key)
        self.assertEqual(authority.load_asset_state(self.ep, self.key)["active_attempt_index"], 1)
        released, evidence = raw_candidate_budget.release(self.ep, "facade-test", "pre-dispatch test")
        self.assertTrue(released, evidence)
        self.assertEqual(authority.load_asset_state(self.ep, self.key)["attempts_consumed"], 0)


if __name__ == "__main__":
    unittest.main()
