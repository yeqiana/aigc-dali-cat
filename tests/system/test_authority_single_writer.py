from __future__ import annotations
import hashlib,json,sys,tempfile,threading,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'episodes/_system'))
import authority_commit
class AuthorityWriterTest(unittest.TestCase):
 def test_stale_and_concurrent_patch_are_safe(self):
  with tempfile.TemporaryDirectory() as raw:
   ep=Path(raw);p=ep/'meta/story-gates.json';p.parent.mkdir();p.write_text(json.dumps({'visual':{'a':1}}),encoding='utf-8'); expected=hashlib.sha256(p.read_bytes()).hexdigest()
   rows=[]
   ts=[threading.Thread(target=lambda key=key:rows.append(authority_commit.commit_visual_patch(ep,{key:1},expected_sha=expected,snapshot_id='s'))) for key in ('x','y')]
   [t.start() for t in ts];[t.join() for t in ts]
   self.assertEqual(sum(row['committed'] for row in rows),1)
   self.assertEqual(authority_commit.commit_visual_patch(ep,{'z':1},expected_sha=expected,snapshot_id='old')['status'],'STALE')
