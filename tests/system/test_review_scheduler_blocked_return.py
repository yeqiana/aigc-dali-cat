from __future__ import annotations
import asyncio
import copy
import sys
from pathlib import Path
from unittest.mock import patch
SYSTEM = Path(__file__).resolve().parents[2]/"episodes"/"_system"
if str(SYSTEM) not in sys.path:sys.path.insert(0,str(SYSTEM))
import image_scheduler
import review_queue

def test_generated_image_does_not_hide_quarantined_final_review(tmp_path):
    queued = {"items":[{"frame":1,"status":"generated"}],
              review_queue.QUEUE_KEY:[{
                "review_kind":review_queue.FINAL_SEMANTIC,
                "status":"running","queued_at":"2000-01-01T00:00:00+00:00",
                "lease_expires_at":"2000-01-01T00:00:00+00:00",
                "claim_token":"old","receipt":None}]}
    state=copy.deepcopy(queued)
    def load(_):return copy.deepcopy(state)
    def save(_,value):state.clear();state.update(copy.deepcopy(value))
    with (patch.object(image_scheduler.resource_library,"ensure_fresh"),
          patch.object(image_scheduler.production_recovery,"reconcile_locked"),
          patch.object(image_scheduler.scheduler_core,"terminalize_superseded_history"),
          patch.object(image_scheduler.frame_scout,"required",return_value=True),
          patch.object(image_scheduler,"load_queue",side_effect=load),
          patch.object(image_scheduler,"save_queue",side_effect=save),
          patch.object(image_scheduler,"ready_items",return_value=([],[])),
          patch.object(image_scheduler.model_policy,"resolve",return_value={"model":"test","model_policy_sha256":"a"*64}),
          patch.object(image_scheduler.review_queue,"reconcile_generated",return_value=[])):
        rc=asyncio.run(image_scheduler._run_scheduler_async(tmp_path,1,20,None))
    assert rc==22
    assert state[review_queue.QUEUE_KEY][0]["status"]=="blocked"
    assert state["items"][0]["status"]=="generated"
def test_live_final_semantic_review_does_not_start_duplicate_lane(tmp_path):
    state = {"items": [{"frame": 1, "status": "generated"}],
             review_queue.QUEUE_KEY: [{
               "review_kind": review_queue.FINAL_SEMANTIC,
               "status": "running", "queued_at": "2026-10-09T00:00:00+00:00",
               "lease_expires_at": "2050-01-01T00:00:00+00:00",
               "claim_token": "live-worker", "receipt": None}]}
    def load(_): return copy.deepcopy(state)
    def save(_, value): state.clear(); state.update(copy.deepcopy(value))
    with (patch.object(image_scheduler.resource_library, "ensure_fresh"),
          patch.object(image_scheduler.production_recovery, "reconcile_locked"),
          patch.object(image_scheduler.scheduler_core, "terminalize_superseded_history"),
          patch.object(image_scheduler.frame_scout, "required", return_value=True),
          patch.object(image_scheduler, "load_queue", side_effect=load),
          patch.object(image_scheduler, "save_queue", side_effect=save),
          patch.object(image_scheduler, "ready_items", return_value=([], [])),
          patch.object(image_scheduler.model_policy, "resolve", return_value={"model": "test"}),
          patch.object(image_scheduler.review_queue, "reconcile_generated", return_value=[]),
          patch.object(image_scheduler.review_queue, "run_lane") as run_lane):
        rc = asyncio.run(image_scheduler._run_scheduler_async(tmp_path, 1, 20, None))
    assert rc == 24
    run_lane.assert_not_called()
    assert state[review_queue.QUEUE_KEY][0]["claim_token"] == "live-worker"
    assert state[review_queue.QUEUE_KEY][0]["status"] == "running"
