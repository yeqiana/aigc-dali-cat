from __future__ import annotations
import json, shutil, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"episodes/_system"))
import product_runtime_adapter as adapter
import preimage_task_contract as tasks

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

if __name__=="__main__": unittest.main()
