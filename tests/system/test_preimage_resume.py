from __future__ import annotations
import json, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"episodes/_system"))
import preimage_authority_snapshot as snapshots
import preimage_task_contract as contract

class PreimageResumeTest(unittest.TestCase):
 def test_only_failed_task_retries_when_snapshot_is_stable(self):
  with tempfile.TemporaryDirectory() as raw:
   ep=Path(raw); (ep/"meta").mkdir(); (ep/"meta/story-gates.json").write_text(json.dumps({"story":{},"visual":{}}),encoding="utf-8")
   snap=snapshots.build(ep); rows=contract.plan_tasks(ep,snap)
   for row in rows:
    if row["task_type"]=="ENVIRONMENT_PREPARE": contract.update_task_state(ep,row,"FAILED")
    else:
     self.assertEqual(contract.write_candidate(ep,row,contract.candidate_template(row,contract.valid_payload(row))),[]); contract.update_task_state(ep,row,"COMPLETED")
   planned={x["task_type"]:x["status"] for x in contract.plan_tasks(ep,snap,resume=True)}
   self.assertEqual(planned["ENVIRONMENT_PREPARE"],"RETRY")
   self.assertEqual(sum(x=="REUSED" for x in planned.values()),3)

if __name__=="__main__": unittest.main()
