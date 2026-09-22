from __future__ import annotations
import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"episodes/_system"))
import preimage_task_contract as contract
import preimage_protocol
import preimage_authority_snapshot as snapshots
import json, tempfile

class AuthorityCollisionTest(unittest.TestCase):
 def test_overlap_fails_before_commit(self):
  with self.assertRaisesRegex(ValueError,"scope collision"):
   contract.validate_patch_scopes([{"task_id":"a","authority_scope":["visual.x"]},{"task_id":"b","authority_scope":["visual.x"]}])

 def test_collision_commit_leaves_authority_bytes_unchanged(self):
  with tempfile.TemporaryDirectory() as raw:
   ep=Path(raw); (ep/"meta").mkdir(); gates=ep/"meta/story-gates.json"; gates.write_text(json.dumps({"story":{},"visual":{}}),encoding="utf-8")
   snap=snapshots.build(ep); rows=contract.plan_tasks(ep,snap); rows[1]["authority_scope"]=["character.finalize"]
   before=gates.read_bytes()
   with self.assertRaisesRegex(ValueError,"scope collision"): preimage_protocol.commit_candidates(ep,snap,rows)
   self.assertEqual(gates.read_bytes(),before)

if __name__=="__main__": unittest.main()
