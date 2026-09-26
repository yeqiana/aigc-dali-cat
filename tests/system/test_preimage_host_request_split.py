from __future__ import annotations
import json, shutil, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"episodes/_system"))
import product_runtime_adapter as adapter
import preimage_task_contract as tasks
import preimage_execution_persistence as shadow_execution

class PreimageHostRequestSplitTest(unittest.TestCase):
 def test_storyboard_locked_emits_four_independent_requests(self):
  base=ROOT/".storyos-tmp"; base.mkdir(exist_ok=True); raw=tempfile.mkdtemp(dir=base)
  try:
   ep=Path(raw); (ep/"meta").mkdir(); (ep/"meta/episode-state.json").write_text(json.dumps({"current_state":"STORYBOARD_LOCKED"}),encoding="utf-8")
   (ep/"meta/story-gates.json").write_text(json.dumps({"story":{"locked":True},"visual":{}}),encoding="utf-8")
   requests=adapter.build_preimage_requests(ep,runtime="WORK",mode="full_auto",resume=True,source="test")
   self.assertEqual(len(requests),4)
   self.assertEqual(len({r["request_id"] for r in requests}),4)
   self.assertTrue(all(r["next_step"]!="PREIMAGE_COMPILE" for r in requests))
   self.assertEqual({r["task"]["task_type"] for r in requests},{"CHARACTER_FINALIZE","ENVIRONMENT_PREPARE","WORLD_PREPARE","VISUAL_NARRATIVE_PREPARE"})
  finally: shutil.rmtree(raw,ignore_errors=True)

 def test_task_set_declares_parallel_start_then_collect_host_contract(self):
  base=ROOT/".storyos-tmp"; base.mkdir(exist_ok=True); raw=tempfile.mkdtemp(dir=base)
  try:
   ep=Path(raw); (ep/"meta").mkdir(); (ep/"meta/episode-state.json").write_text(json.dumps({"current_state":"STORYBOARD_LOCKED"}),encoding="utf-8")
   (ep/"meta/story-gates.json").write_text(json.dumps({"story":{"locked":True},"visual":{}}),encoding="utf-8")
   request=adapter.build_request(ep,runtime="WORK",mode="full_auto",resume=True,source="test")
   self.assertEqual(request["next_step"],"PREIMAGE_TASK_SET")
   dispatch=request["host_dispatch_contract"]
   self.assertEqual(dispatch["strategy"],"parallel_start_then_collect")
   self.assertEqual(dispatch["max_parallel"],4)
   self.assertTrue(dispatch["start_all_before_wait"])
   self.assertEqual(dispatch["completion_order"],"any")
   self.assertEqual(dispatch["authority_commit"],"single_writer_after_barrier")
   self.assertTrue(dispatch["host_owned_concurrency"])
   self.assertEqual(len(request["requests"]),4)
   for child in request["requests"]:
    contract=child["host_contract"]
    self.assertEqual(contract["dispatch_group"],"PREIMAGE_TASK_SET")
    self.assertTrue(contract["independent_parallelizable"])
    self.assertFalse(contract["wait_for_siblings_before_start"])
  finally: shutil.rmtree(raw,ignore_errors=True)

 def test_independent_completion_resume_only_returns_unfinished_task(self):
  base=ROOT/".storyos-tmp"; base.mkdir(exist_ok=True); raw=tempfile.mkdtemp(dir=base)
  try:
   ep=Path(raw); (ep/"meta").mkdir(); (ep/"meta/episode-state.json").write_text(json.dumps({"current_state":"STORYBOARD_LOCKED"}),encoding="utf-8")
   (ep/"meta/story-gates.json").write_text(json.dumps({"story":{"locked":True},"visual":{}}),encoding="utf-8")
   requests=adapter.build_preimage_requests(ep,runtime="WORK",mode="full_auto",resume=True,source="test")
   for index,request in enumerate(requests[:-1],1):
    task=request["task"]; payload=tasks.valid_payload(task)
    adapter.mark_preimage_task_running(ep,request["request_id"],worker_id=f"test-worker-{index}")
    done=adapter.complete_preimage_task(ep,request["request_id"],tasks.candidate_template(task,payload))
    self.assertEqual(done["status"],"FINALIZED")
   resumed=adapter.build_preimage_requests(ep,runtime="WORK",mode="full_auto",resume=True,source="test")
   self.assertEqual(len(resumed),1); self.assertEqual(resumed[0]["task"]["task_type"],requests[-1]["task"]["task_type"])
  finally: shutil.rmtree(raw,ignore_errors=True)

 def test_host_completion_requires_explicit_execution_start(self):
  base=ROOT/".storyos-tmp"; base.mkdir(exist_ok=True); raw=tempfile.mkdtemp(dir=base)
  try:
   ep=Path(raw); (ep/"meta").mkdir(); (ep/"meta/episode-state.json").write_text(json.dumps({"current_state":"STORYBOARD_LOCKED"}),encoding="utf-8")
   (ep/"meta/story-gates.json").write_text(json.dumps({"story":{"locked":True},"visual":{}}),encoding="utf-8")
   request=adapter.build_preimage_requests(ep,runtime="WORK",mode="full_auto",resume=True,source="test")[0]
   task=request["task"]; payload=tasks.valid_payload(task)
   with self.assertRaisesRegex(ValueError,"PREIMAGE_HOST_EXECUTION_START_REQUIRED"):
    adapter.complete_preimage_task(ep,request["request_id"],tasks.candidate_template(task,payload))
  finally: shutil.rmtree(raw,ignore_errors=True)

 def test_host_metrics_count_only_real_execution_intervals(self):
  base=ROOT/".storyos-tmp"; base.mkdir(exist_ok=True); raw=tempfile.mkdtemp(dir=base)
  try:
   ep=Path(raw); (ep/"meta").mkdir(); (ep/"meta/episode-state.json").write_text(json.dumps({"current_state":"STORYBOARD_LOCKED"}),encoding="utf-8")
   (ep/"meta/story-gates.json").write_text(json.dumps({"story":{"locked":True},"visual":{}}),encoding="utf-8")
   requests=adapter.build_preimage_requests(ep,runtime="WORK",mode="full_auto",resume=True,source="test")
   for index,request in enumerate(requests[:2],1):
    adapter.mark_preimage_task_running(ep,request["request_id"],worker_id=f"parallel-{index}")
   metrics=adapter.preimage_execution_metrics(ep)
   self.assertEqual(metrics["started"],2)
   self.assertEqual(metrics["inflight_now"],2)
   self.assertEqual(metrics["peak_observed_concurrency"],2)
   self.assertEqual(metrics["unmeasured_requests"],2)
   self.assertEqual(metrics["measurement"],"host_execution_intervals_only")
  finally: shutil.rmtree(raw,ignore_errors=True)

 def test_last_host_completion_calls_serial_authority_commit(self):
  base=ROOT/".storyos-tmp"; base.mkdir(exist_ok=True); raw=tempfile.mkdtemp(dir=base)
  try:
   ep=Path(raw); (ep/"meta").mkdir(); (ep/"meta/episode-state.json").write_text(json.dumps({"current_state":"STORYBOARD_LOCKED"}),encoding="utf-8")
   (ep/"meta/story-gates.json").write_text(json.dumps({"story":{"locked":True},"visual":{}}),encoding="utf-8")
   requests=adapter.build_preimage_requests(ep,runtime="WORK",mode="full_auto",resume=True,source="test")
   completed=[]
   for index,request in enumerate(requests,1):
    task=request["task"]; payload=tasks.valid_payload(task)
    adapter.mark_preimage_task_running(ep,request["request_id"],worker_id=f"test-worker-{index}")
    completed.append(adapter.complete_preimage_task(ep,request["request_id"],tasks.candidate_template(task,payload)))
   self.assertEqual(completed[-1]["authority_commit"]["status"],"PASS")
   self.assertTrue((ep/"meta/runtime/preimage-authority-barrier.json").is_file())
  finally: shutil.rmtree(raw,ignore_errors=True)

 def test_shadow_feature_off_keeps_legacy_request_shape(self):
  base=ROOT/".storyos-tmp"; base.mkdir(exist_ok=True); raw=tempfile.mkdtemp(dir=base)
  try:
   ep=Path(raw); (ep/"meta").mkdir(); (ep/"meta/episode-state.json").write_text(json.dumps({"current_state":"STORYBOARD_LOCKED"}),encoding="utf-8")
   (ep/"meta/story-gates.json").write_text(json.dumps({"story":{"locked":True},"visual":{}}),encoding="utf-8")
   with patch.object(adapter,"character_finalize_shadow_enabled",return_value=False), patch.object(adapter,"character_finalize_production_enabled",return_value=False), patch.object(adapter,"world_prepare_shadow_enabled",return_value=False):
    request=adapter.build_request(ep,runtime="WORK",mode="full_auto",resume=True,source="test")
   self.assertEqual(len(request["requests"]),4)
   self.assertNotIn("shadow_requests",request)
   self.assertNotIn("shadow_host_task_count",request)
  finally: shutil.rmtree(raw,ignore_errors=True)

 def test_character_shadow_is_noncanonical_and_reconciles_after_legacy(self):
  base=ROOT/".storyos-tmp"; base.mkdir(exist_ok=True); raw=tempfile.mkdtemp(dir=base)
  try:
   ep=Path(raw); (ep/"meta").mkdir(); (ep/"meta/episode-state.json").write_text(json.dumps({"current_state":"STORYBOARD_LOCKED"}),encoding="utf-8")
   (ep/"meta/story-gates.json").write_text(json.dumps({"story":{"locked":True},"visual":{}}),encoding="utf-8")
   with patch.object(adapter,"character_finalize_shadow_enabled",return_value=True), patch.object(adapter,"character_finalize_production_enabled",return_value=False), patch.object(adapter,"world_prepare_shadow_enabled",return_value=False), patch.object(shadow_execution,"mode",return_value="json"):
    request=adapter.build_request(ep,runtime="WORK",mode="full_auto",resume=True,source="test")
    self.assertEqual(len(request["requests"]),4)
    self.assertEqual(len(request["shadow_requests"]),1)
    shadow=request["shadow_requests"][0]
    self.assertTrue(shadow["shadow"])
    self.assertEqual(shadow["task"]["task_type"],"CHARACTER_FINALIZE")
    self.assertNotIn("current_request_path",shadow)
    current=adapter._read_current_request(ep)
    self.assertEqual(current["request_id"],request["requests"][-1]["request_id"])
    with self.assertRaisesRegex(ValueError,"start-preimage-shadow"):
     adapter.mark_preimage_task_running(ep,shadow["request_id"],worker_id="wrong-path")
    adapter.mark_preimage_shadow_running(ep,shadow["request_id"],worker_id="shadow-worker")
    task=shadow["task"]
    candidate=tasks.candidate_template(task,tasks.valid_payload(task))
    done=adapter.complete_preimage_shadow_task(ep,shadow["request_id"],candidate)
    self.assertEqual(done["status"],"FINALIZED")
    self.assertEqual(done["comparison_status"],"WAITING_FOR_LEGACY")
    self.assertFalse((ep/task["candidate_output"]).is_file())
    metrics=adapter.preimage_execution_metrics(ep)
    self.assertEqual(metrics["requested"],4)
    self.assertEqual(metrics["started"],0)
    replay=adapter.complete_preimage_shadow_task(ep,shadow["request_id"],candidate)
    self.assertEqual(replay["status"],"FINALIZED")
    legacy=next(row for row in request["requests"] if row["task"]["task_type"]=="CHARACTER_FINALIZE")
    adapter.mark_preimage_task_running(ep,legacy["request_id"],worker_id="legacy-worker")
    legacy_done=adapter.complete_preimage_task(ep,legacy["request_id"],candidate)
    self.assertEqual(legacy_done["status"],"FINALIZED")
    refreshed=adapter.host_request_persistence.load(ep,shadow["request_id"])
    self.assertEqual(refreshed["comparison_status"],"COMPARED")
    self.assertTrue(refreshed["shadow_comparison"]["structural_equal"])
    record=shadow_execution.find_execution(ep,task["snapshot_id"],task["task_id"],shadow["agent_execution"]["execution_id"])
    self.assertEqual(record["status"],"SHADOW_COMPLETED")
    self.assertEqual(record["shadow_result"]["comparison_status"],"COMPARED")
    shadow_metrics=adapter.character_shadow_metrics(ep)
    self.assertEqual(shadow_metrics["requested"],1)
    self.assertEqual(shadow_metrics["finalized"],1)
    self.assertEqual(shadow_metrics["compared"],1)
    self.assertEqual(shadow_metrics["structural_equal"],1)
    self.assertFalse(shadow_metrics["canonical_side_effect"])

  finally: shutil.rmtree(raw,ignore_errors=True)

 def test_shadow_failure_does_not_block_or_mutate_legacy_character_task(self):
  base=ROOT/".storyos-tmp"; base.mkdir(exist_ok=True); raw=tempfile.mkdtemp(dir=base)
  try:
   ep=Path(raw); (ep/"meta").mkdir(); (ep/"meta/episode-state.json").write_text(json.dumps({"current_state":"STORYBOARD_LOCKED"}),encoding="utf-8")
   (ep/"meta/story-gates.json").write_text(json.dumps({"story":{"locked":True},"visual":{}}),encoding="utf-8")
   with patch.object(adapter,"character_finalize_shadow_enabled",return_value=True), patch.object(adapter,"character_finalize_production_enabled",return_value=False), patch.object(shadow_execution,"mode",return_value="json"):
    request=adapter.build_request(ep,runtime="WORK",mode="full_auto",resume=True,source="test")
    shadow=request["shadow_requests"][0]
    task=shadow["task"]
    adapter.mark_preimage_shadow_running(ep,shadow["request_id"],worker_id="shadow-fail-worker")
    invalid=tasks.candidate_template(task,tasks.valid_payload(task))
    invalid["payload"]={}
    failed=adapter.complete_preimage_shadow_task(ep,shadow["request_id"],invalid)
    self.assertEqual(failed["status"],"FAILED")
    self.assertFalse((ep/task["candidate_output"]).is_file())
    legacy=next(row for row in request["requests"] if row["task"]["task_type"]=="CHARACTER_FINALIZE")
    valid=tasks.candidate_template(legacy["task"],tasks.valid_payload(legacy["task"]))
    adapter.mark_preimage_task_running(ep,legacy["request_id"],worker_id="legacy-after-shadow-fail")
    done=adapter.complete_preimage_task(ep,legacy["request_id"],valid)
    self.assertEqual(done["status"],"FINALIZED")
    self.assertTrue((ep/legacy["task"]["candidate_output"]).is_file())
    metrics=adapter.character_shadow_metrics(ep)
    self.assertEqual(metrics["failed"],1)

  finally: shutil.rmtree(raw,ignore_errors=True)

if __name__=="__main__": unittest.main()
