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
import persistent_runner_daemon as daemon
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

    def queue(self):
        q={"items":[{"id":str(i),"frame":i,"scope":"batch","status":"queued","attempts":0,"depends_on":[]} for i in (1,2)]}
        atomic_write_json(self.ep / batch.QUEUE_REL,q)
        return q

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
        with self.batch_deps(), patch.object(batch.image_provider_runtime,"select_batch_provider",return_value={"provider":"openai_images_api"}), patch.object(batch.batch_contract,"build",return_value=contract), patch.object(batch,"ledger_begin",return_value=(True,"")), patch.object(batch,"ledger_success",return_value=(True,"")), patch.object(batch.batch_image_worker,"execute_batch",return_value=result) as native, patch.object(batch.image_worker_pool,"execute") as single:
            self.assertEqual(asyncio.run(batch._run_async(self.ep,3,60,None)),0)
            self.assertEqual(native.call_count,1)
            single.assert_not_called()
        self.assertEqual([x["status"] for x in batch.load_queue(self.ep)["items"]],["generated","generated"])

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
