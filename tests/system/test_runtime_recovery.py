"""Regression cases exercise real scheduler/runner with isolated external effects."""
import asyncio
import contextlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
sys.path.insert(0, str(SYSTEM))
import batch_scheduler as batch
import episode_runner as runner
import image_scheduler as single
import persistent_runner_daemon as daemon
import product_image_import
import production_recovery
import runner_state_store as store
import runtime_failure_classifier as classifier
from runtime_atomic_store import atomic_write_json


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="storyos-recovery-")
        self.addCleanup(self.tmp.cleanup)
        self.ep = Path(self.tmp.name)
        validator=patch.object(runner.runtime_dag,"validate_target",return_value=(True,"mocked external gates"))
        validator.start(); self.addCleanup(validator.stop)
        root=patch.object(production_recovery,"ROOT",self.ep)
        root.start(); self.addCleanup(root.stop)
        atomic_write_json(self.ep / "meta/episode-state.json", {"current_state": "VISUAL_CALIBRATED"})

    def test_zero_exit_without_progress_is_bounded(self):
        with patch.object(runner,"execute_cycle",return_value=0) as execute:
            self.assertEqual(runner.run_episode(self.ep,interval=0),24)
            self.assertEqual(execute.call_count,3)

    def test_terminal_stage_requires_real_gate_validation(self):
        atomic_write_json(self.ep/"meta/episode-state.json",{"current_state":"PUBLISH_READY"})
        with patch.object(runner.runtime_dag,"validate_target",return_value=(False,"snapshot missing")):
            self.assertEqual(runner.run_episode(self.ep,interval=0),23)
            self.assertNotEqual(store.load(self.ep)["status"],"COMPLETED")

    def test_ready_sibling_precedes_optional_review_and_retry(self):
        self.queue()
        queue=batch.load_queue(self.ep)
        queue["items"][0]["status"]="tech_failed"
        batch.save_queue(self.ep,queue)
        with patch.object(runner.next_action,"ROOT",self.ep.parent), patch.object(runner.next_action,"pending_product_review",return_value={"path":"pending","review_kind":"optional"}), patch.object(runner.next_action.visual_lock_baseline_gate,"awaiting_review",return_value=False), patch.object(runner.next_action.product_runtime_adapter,"reconcile"):
            action=runner.next_action.derive(self.ep)
            self.assertEqual(action["action"],"GENERATE_IMAGES")
            self.assertEqual(action["frames"],[2])

    def test_baseline_still_blocks_dependent_images(self):
        self.queue()
        with patch.object(runner.next_action,"ROOT",self.ep.parent), patch.object(runner.next_action,"pending_product_review",return_value=None), patch.object(runner.next_action.visual_lock_baseline_gate,"awaiting_review",return_value=True), patch.object(runner.next_action.visual_lock_baseline_gate,"baseline_frame",return_value=1), patch.object(runner.next_action.product_runtime_adapter,"reconcile"):
            self.assertEqual(runner.next_action.derive(self.ep)["action"],"REVIEW_ORDINARY_BASELINE")

    def test_explicit_results_override_contract_words(self):
        for code, category in [(20,"HOST_WAIT"),(21,"TECH_FAILED"),(22,"HUMAN_REQUIRED"),
                                (23,"HARD_STOP"),(24,"CAPABILITY_WAIT"),(503,"TECH_FAILED")]:
            self.assertEqual(classifier.classify(code,"visual contract").category, category)

    def test_retry_is_bounded_and_checkpoint_preserved(self):
        atomic_write_json(self.ep / "meta/runtime-checkpoint.json", {"step_runs": [{"step": "KEEP"}]})
        with patch.object(runner,"execute_cycle",return_value=21) as execute:
            self.assertEqual(runner.run_episode(self.ep,interval=0),21)
            self.assertEqual(execute.call_count,3)
        cp=json.loads((self.ep / "meta/runtime-checkpoint.json").read_text())
        self.assertEqual(cp["step_runs"],[{"step":"KEEP"}])
        self.assertEqual(store.load(self.ep)["attempt"],3)

    def test_transient_failure_recovers_and_completes(self):
        calls=[]
        def execute(ep):
            calls.append(1)
            if len(calls)==1: return 21
            atomic_write_json(ep / "meta/episode-state.json", {"current_state":"PUBLISH_READY"})
            return 0
        with patch.object(runner,"execute_cycle",side_effect=execute):
            self.assertEqual(runner.run_episode(self.ep,interval=0),0)
        self.assertEqual(len(calls),2)
        self.assertEqual(store.load(self.ep)["status"],"COMPLETED")

    def test_upper_driver_readmits_waves_until_ready_queue_drained(self):
        rows = [{"id": f"row-{i}", "frame": i, "scope": "batch", "status": "queued",
                 "attempts": 0, "depends_on": []} for i in range(1, 8)]
        atomic_write_json(self.ep / batch.QUEUE_REL,
                          {"schema_version": 1, "items": rows, "waves": []})
        drained = []

        def cycle(ep):
            q = batch.load_queue(ep)
            ready = [x for x in q["items"] if x["status"] == "queued"]
            if ready:
                wave = ready[:3]
                drained.append(len(wave))
                for x in wave:
                    x["status"] = "generated"
                    x["output_path"] = f"mock/{int(x['frame']):02d}.png"
                batch.save_queue(ep, q)
                return 0
            atomic_write_json(ep / "meta/episode-state.json",
                              {"current_state": "PUBLISH_READY"})
            return 0

        with patch.object(runner, "execute_cycle", side_effect=cycle):
            self.assertEqual(runner.run_episode(self.ep, interval=0), 0)
        final = batch.load_queue(self.ep)
        self.assertEqual(drained, [3, 3, 1])
        self.assertTrue(all(x["status"] == "generated" for x in final["items"]))

    def test_wait_and_hard_stop_do_not_spin(self):
        for rc in (20,22,23,24):
            with patch.object(runner,"execute_cycle",return_value=rc) as execute:
                self.assertEqual(runner.run_episode(self.ep,interval=0),rc)
                self.assertEqual(execute.call_count,1)

    def test_daemon_exception_releases_lock(self):
        with patch.object(runner,"run_episode",side_effect=RuntimeError("injected")):
            with self.assertRaises(RuntimeError): daemon.run(self.ep,interval=0)
        self.assertTrue(store.acquire_lock(self.ep))
        store.release_lock(self.ep)

    def test_process_kill_releases_single_owner_lock(self):
        code = "import sys,time; from pathlib import Path; sys.path.insert(0,sys.argv[1]); import runner_state_store as s; print(s.acquire_lock(Path(sys.argv[2])),flush=True); time.sleep(30)"
        proc=subprocess.Popen([sys.executable,"-c",code,str(SYSTEM),str(self.ep)],stdout=subprocess.PIPE,text=True)
        try:
            self.assertEqual(proc.stdout.readline().strip(),"True")
            self.assertFalse(store.acquire_lock(self.ep))
            proc.kill(); proc.wait(timeout=10)
            self.assertTrue(store.acquire_lock(self.ep))
            self.assertFalse(store.acquire_lock(self.ep))
            store.release_lock(self.ep)
        finally:
            if proc.poll() is None: proc.kill(); proc.wait(timeout=10)
            proc.stdout.close()

    def test_direct_queue_mutation_defers_while_scheduler_is_running(self):
        self.queue()
        q=batch.load_queue(self.ep)
        q["items"][0]["status"]="tech_failed"
        batch.save_queue(self.ep,q)
        self.assertTrue(store.acquire_lock(self.ep,lock_rel=single.SCHEDULER_LOCK_REL))
        try:
            with self.assertRaises(single.QueueMutationBusy):
                single.retry_tech(self.ep,1)
            with patch.object(product_image_import,"_import_frame_locked") as import_locked:
                with self.assertRaises(product_image_import.ProductImageImportError):
                    product_image_import.import_frame(self.ep,1,self.ep/"unused.png",runtime="WORK")
                import_locked.assert_not_called()
        finally:
            store.release_lock(self.ep,lock_rel=single.SCHEDULER_LOCK_REL)
        self.assertEqual(batch.load_queue(self.ep)["items"][0]["status"],"tech_failed")
        self.assertEqual(single.retry_tech(self.ep,1)["requeued"],1)

    def _running_item(self):
        return {
            "id":"recover-01", "frame":1, "scope":"batch", "kind":"original",
            "status":"running", "attempts":1, "model":"gpt-image-2", "quality":"high",
            "frame_contract":{"contract_sha256":"contract-a"}, "depends_on":[],
        }

    def _active_ledger(self):
        return {"frames":{"01":{"status":"GENERATING","attempts":[{
            "attempt_id":"attempt-01", "result":"pending", "kind":"original"
        }]}}}

    def test_recovery_retries_only_pre_worker_interruption(self):
        item=self._running_item()
        production_recovery.prepare_execution(self.ep,item)
        production_recovery.mark_worker_pending(self.ep,item)
        atomic_write_json(self.ep / batch.QUEUE_REL,{"items":[item]})
        atomic_write_json(self.ep / "meta/production-ledger.json",self._active_ledger())
        q=batch.load_queue(self.ep)
        report=production_recovery.reconcile_locked(self.ep,q)
        self.assertEqual(report["rows"][0]["outcome"],"PRE_WORKER_INTERRUPTION_RETRYABLE")
        self.assertEqual(q["items"][0]["status"],"tech_failed")
        self.assertEqual(json.loads((self.ep/"meta/production-ledger.json").read_text())["frames"]["01"]["status"],"TECH_FAILED")

    def test_recovery_never_regenerates_unknown_inflight_worker(self):
        item=self._running_item()
        production_recovery.prepare_execution(self.ep,item)
        production_recovery.mark_worker_pending(self.ep,item)
        production_recovery.write_lifecycle(self.ep,item,"BACKEND_INVOKED",worker_pid=99999)
        atomic_write_json(self.ep / batch.QUEUE_REL,{"items":[item]})
        atomic_write_json(self.ep / "meta/production-ledger.json",self._active_ledger())
        q=batch.load_queue(self.ep)
        report=production_recovery.reconcile_locked(self.ep,q)
        self.assertEqual(report["rows"][0]["outcome"],"UNKNOWN_RUNNING_WORKER")
        self.assertEqual(q["items"][0]["status"],"interrupted_unknown")
        frame=json.loads((self.ep/"meta/production-ledger.json").read_text())["frames"]["01"]
        self.assertEqual(frame["status"],"GENERATING")
        self.assertEqual(frame["attempts"][-1]["result"],"pending")

    def test_recovery_replays_ledger_commit_missing_from_queue(self):
        item=self._running_item()
        candidate=self.ep/"candidate.png"; candidate.write_bytes(b"candidate")
        atomic_write_json(self.ep / batch.QUEUE_REL,{"items":[item]})
        atomic_write_json(self.ep / "meta/production-ledger.json",{"frames":{"01":{
            "status":"ORIGINAL_READY", "current_candidate":{"path":str(candidate)}
        }}})
        q=batch.load_queue(self.ep)
        report=production_recovery.reconcile_locked(self.ep,q)
        self.assertEqual(report["rows"][0]["outcome"],"LEDGER_READY_REPLAYED")
        self.assertEqual(q["items"][0]["status"],"generated")
        self.assertTrue(q["items"][0]["output_path"].endswith("candidate.png"))

    def test_recovery_replays_durable_worker_success_once(self):
        item=self._running_item()
        production_recovery.prepare_execution(self.ep,item)
        production_recovery.mark_worker_pending(self.ep,item)
        candidate=self.ep/"candidate-success.png"; candidate.write_bytes(b"candidate")
        result={"output":str(candidate),"payload":{"image_model":{"model":"gpt-image-2","quality":"high"},
                "frame_contract":{"contract_sha256":"contract-a"}}}
        production_recovery.write_lifecycle(self.ep,item,"SUCCEEDED",worker_pid=123,result=result)
        atomic_write_json(self.ep / batch.QUEUE_REL,{"items":[item]})
        atomic_write_json(self.ep / "meta/production-ledger.json",self._active_ledger())
        q=batch.load_queue(self.ep)
        with patch.object(production_recovery.production_ledger,"cmd_success") as success:
            report=production_recovery.reconcile_locked(self.ep,q)
        success.assert_called_once()
        self.assertEqual(report["rows"][0]["outcome"],"WORKER_SUCCESS_REPLAYED")
        self.assertEqual(q["items"][0]["status"],"generated")

    def test_worker_lifecycle_serializes_path_result_evidence(self):
        item=self._running_item()
        production_recovery.prepare_execution(self.ep,item)
        production_recovery.write_lifecycle(self.ep,item,"SUCCEEDED",result={
            "output":self.ep/"candidate.png", "log":self.ep/"worker.jsonl"
        })
        saved=json.loads(production_recovery.lifecycle_path(self.ep,item).read_text())
        self.assertEqual(saved["result"]["output"],str(self.ep/"candidate.png"))
        self.assertEqual(saved["result"]["log"],str(self.ep/"worker.jsonl"))

    def queue(self):
        q={"items":[{"id":str(i),"frame":i,"scope":"batch","status":"queued","attempts":0,"depends_on":[]} for i in (1,2)]}
        atomic_write_json(self.ep / batch.QUEUE_REL,q)
        return q

    def test_corrupt_worker_lifecycle_never_counts_as_success(self):
        item = self._running_item()
        production_recovery.prepare_execution(self.ep, item)
        production_recovery.mark_worker_pending(self.ep, item)
        lifecycle = production_recovery.lifecycle_path(self.ep, item)
        lifecycle.parent.mkdir(parents=True, exist_ok=True)
        lifecycle.write_bytes(b"{broken json")
        atomic_write_json(self.ep / batch.QUEUE_REL, {"items": [item]})
        atomic_write_json(self.ep / "meta/production-ledger.json", self._active_ledger())
        q = batch.load_queue(self.ep)
        report = production_recovery.reconcile_locked(self.ep, q)
        self.assertEqual(report["rows"][0]["outcome"], "PRE_WORKER_INTERRUPTION_RETRYABLE")
        self.assertEqual(q["items"][0]["status"], "tech_failed")

    def test_corrupt_commit_journal_never_forges_success_or_blocks_reconcile(self):
        item = self._running_item()
        production_recovery.prepare_execution(self.ep, item)
        production_recovery.mark_worker_pending(self.ep, item)
        journal = self.ep / production_recovery.JOURNAL_REL
        journal.parent.mkdir(parents=True, exist_ok=True)
        journal.write_bytes(b"{broken json")
        atomic_write_json(self.ep / batch.QUEUE_REL, {"items": [item]})
        atomic_write_json(self.ep / "meta/production-ledger.json", self._active_ledger())
        q = batch.load_queue(self.ep)
        report = production_recovery.reconcile_locked(self.ep, q)
        self.assertEqual(report["rows"][0]["outcome"], "PRE_WORKER_INTERRUPTION_RETRYABLE")
        self.assertEqual(q["items"][0]["status"], "tech_failed")
        fresh = production_recovery._read(journal)
        self.assertIn(item["execution"]["transaction_id"], fresh.get("transactions") or {})

    def test_double_stale_queue_ledger_stays_unknown(self):
        item = self._running_item()
        atomic_write_json(self.ep / batch.QUEUE_REL, {"items": [item]})
        atomic_write_json(self.ep / "meta/production-ledger.json",
                          {"frames": {"01": {"status": "PENDING", "attempts": []}}})
        q = batch.load_queue(self.ep)
        report = production_recovery.reconcile_locked(self.ep, q)
        self.assertEqual(report["rows"][0]["outcome"], "QUEUE_LEDGER_MISMATCH")
        self.assertEqual(q["items"][0]["status"], "interrupted_unknown")

    @contextlib.contextmanager
    def batch_deps(self, capable=True):
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(batch.resource_library,"ensure_fresh"))
            stack.enter_context(patch.object(batch,"ensure_image_capability",return_value=capable))
            stack.enter_context(patch.object(batch,"ROOT",self.ep))
            stack.enter_context(patch.object(batch,"ledger_tech_fail"))
            yield stack

    def test_capability_wait_does_not_consume_frames(self):
        q=self.queue()
        with self.batch_deps(False), patch.object(batch,"ledger_begin") as begin:
            self.assertEqual(asyncio.run(batch._run_async(self.ep,3,60,None)),24)
            begin.assert_not_called()
        self.assertEqual(batch.load_queue(self.ep)["items"],q["items"])

    def test_begin_rejected_frame_never_runs(self):
        self.queue()
        with self.batch_deps(), patch.object(batch,"ledger_begin",return_value=(False,"contract drift")), patch.object(batch.image_worker_pool,"execute") as worker:
            self.assertEqual(asyncio.run(batch._run_async(self.ep,3,60,None)),0)
            self.assertEqual(asyncio.run(batch._run_async(self.ep,3,60,None)),22)
            worker.assert_not_called()

    def test_native_provider_uses_one_batch_call(self):
        self.queue()
        out=self.ep/"native.png"; out.write_bytes(b"mock backend result")
        items=batch.load_queue(self.ep)["items"]
        contract={"planned_count":2,"frames":[{"queue_item_id":x["id"]} for x in items]}
        result={"results":{x["id"]:{"returncode":0,"output":out} for x in items}}
        provider={"provider":"openai_images_api","native_multi_image":True,"execution_mode":"native_n_first"}
        with self.batch_deps(), patch.object(batch.image_provider_runtime,"select_batch_provider",return_value=provider), patch.object(batch.batch_contract,"build",return_value=contract), patch.object(batch,"ledger_begin",return_value=(True,"")), patch.object(batch,"ledger_success",return_value=(True,"")), patch.object(batch.batch_image_worker,"execute_batch",return_value=result) as native, patch.object(batch.image_worker_pool,"execute") as single, patch.object(batch.batch_capability_probe,"record") as record:
            self.assertEqual(asyncio.run(batch._run_async(self.ep,3,60,None)),0)
            self.assertEqual(native.call_count,1)
            single.assert_not_called()
            record.assert_called_once()
            self.assertEqual(record.call_args.kwargs["requested"],2)
            self.assertEqual(record.call_args.kwargs["returned"],2)
            self.assertTrue(record.call_args.kwargs["native_multi_image"])
            self.assertTrue(record.call_args.kwargs["single_http_request"])
        self.assertEqual([x["status"] for x in batch.load_queue(self.ep)["items"]],["generated","generated"])

    def test_native_fallback_does_not_claim_native_multi_image(self):
        self.queue()
        out=self.ep/"fallback.png"; out.write_bytes(b"mock fallback artifact")
        items=batch.load_queue(self.ep)["items"]
        contract={"planned_count":2,"frames":[{"queue_item_id":x["id"]} for x in items]}
        provider={"provider":"openai_images_api","native_multi_image":True,"execution_mode":"native_n_first"}
        def fallback(*_args): return {"returncode":0,"output":out}
        with self.batch_deps(), patch.object(batch.runtime_router,"detect",return_value=("CODEX",{})), patch.object(batch.image_provider_runtime,"select_batch_provider",return_value=provider), patch.object(batch.batch_contract,"build",return_value=contract), patch.object(batch,"ledger_begin",return_value=(True,"")), patch.object(batch,"ledger_success",return_value=(True,"")), patch.object(batch.batch_image_worker,"execute_batch",return_value={"results":{}}) as native, patch.object(batch.image_worker_pool,"execute",side_effect=fallback), patch.object(batch.batch_capability_probe,"record") as record:
            self.assertEqual(asyncio.run(batch._run_async(self.ep,3,60,None)),0)
            self.assertEqual(native.call_count,1)
            self.assertFalse(record.call_args.kwargs["native_multi_image"])
            self.assertFalse(record.call_args.kwargs["single_http_request"])
            self.assertEqual(record.call_args.kwargs["reason"],"NATIVE_BATCH_PARTIAL")

    def test_single_scheduler_reports_worker_error(self):
        import image_scheduler as single
        self.queue()
        ready=batch.load_queue(self.ep)["items"][:1]
        async def fail(*args): return {"returncode":99,"stdout":"network timeout","output":None}
        with patch.object(single.resource_library,"ensure_fresh"), patch.object(single,"ready_items",return_value=(ready,[])), patch.object(single,"ledger_begin",return_value=(True,"")), patch.object(single,"ledger_tech_fail"), patch.object(single,"async_backend_worker",side_effect=fail):
            self.assertEqual(asyncio.run(single._run_scheduler_async(self.ep,3,60,None)),21)
        self.assertEqual(batch.load_queue(self.ep)["items"][0]["status"],"tech_failed")

    def test_failed_commit_returns_failure_and_keeps_sibling(self):
        self.queue()
        out=self.ep / "out.png"; out.write_bytes(b"test external backend artifact")
        def execute(ep,item,timeout,codex):
            return {"returncode":0,"output":out,"payload":{}}
        with self.batch_deps(), patch.object(batch,"verified_image_lane",return_value=True), patch.object(batch,"ledger_begin",return_value=(True,"")), patch.object(batch,"ledger_success",side_effect=[(True,""),(False,"commit rejected")]), patch.object(batch.image_worker_pool,"execute",side_effect=execute):
            self.assertEqual(asyncio.run(batch._run_async(self.ep,3,60,None)),22)
        statuses=[x["status"] for x in batch.load_queue(self.ep)["items"]]
        self.assertEqual(sorted(statuses),["blocked","generated"])
        self.assertEqual(len(batch.ready_items(self.ep,batch.load_queue(self.ep))),0)


if __name__ == "__main__": unittest.main()
