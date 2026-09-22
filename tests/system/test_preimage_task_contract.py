from __future__ import annotations
import json, sys, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"episodes/_system"))
import preimage_authority_snapshot as snapshots
import preimage_task_contract as contract

class PreimageTaskContractTest(unittest.TestCase):
 def test_four_tasks_bind_one_snapshot_and_disjoint_scopes(self):
  with tempfile.TemporaryDirectory() as raw:
   ep=Path(raw); (ep/"meta").mkdir(); (ep/"meta/story-gates.json").write_text(json.dumps({"story":{},"visual":{}}),encoding="utf-8")
   snap=snapshots.build(ep,write=True); tasks=contract.plan_tasks(ep,snap)
   self.assertEqual(len(tasks),4); self.assertEqual(len({x["task_id"] for x in tasks}),4)
   self.assertEqual({x["snapshot_id"] for x in tasks},{snap["snapshot_id"]})
   self.assertEqual(len({x["candidate_output"] for x in tasks}),4)
   contract.validate_patch_scopes(tasks)
   self.assertTrue(all(x["target"]=="candidate_only_no_shared_authority_write" for x in tasks))

 def test_missing_or_extra_payload_scope_is_rejected(self):
  with tempfile.TemporaryDirectory() as raw:
   ep=Path(raw); (ep/"meta").mkdir(); (ep/"meta/story-gates.json").write_text(json.dumps({"story":{},"visual":{}}),encoding="utf-8")
   task=next(x for x in contract.plan_tasks(ep,snapshots.build(ep)) if x["task_type"]=="ENVIRONMENT_PREPARE")
   missing=contract.candidate_template(task,{"visual.environment_contract":{"baseline":{"x":1}}})
   self.assertTrue(contract.verify_candidate(missing,task))
   extra=contract.candidate_template(task,contract.valid_payload(task)); extra["payload"]["story"]={"override":True}
   self.assertTrue(contract.verify_candidate(extra,task))

if __name__=="__main__": unittest.main()
