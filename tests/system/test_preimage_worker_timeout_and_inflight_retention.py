from __future__ import annotations

import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
SYSTEM=ROOT/"episodes"/"_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0,str(SYSTEM))

import runtime_dag
from platform.state import storyos_hot_state


def test_preimage_step_never_inherits_long_supervisor_timeout():
    task={"execution_budget":{"timeout_seconds":900}}
    assert runtime_dag.preimage_worker_timeout(task,7200)==900
    assert runtime_dag.preimage_worker_timeout(task,3600)==900
    assert runtime_dag.preimage_worker_timeout(task,600)==600
    assert runtime_dag.preimage_worker_timeout(task,None)==900


@pytest.mark.parametrize("bad", [None,0,-1,900.0,"900",True])
def test_preimage_worker_rejects_undocumented_budget(bad):
    with pytest.raises(ValueError,match="positive timeout_seconds"):
        runtime_dag.preimage_worker_timeout({"execution_budget":{"timeout_seconds":bad}},7200)


def test_inflight_redis_task_does_not_expire_while_runner_owns_it():
    assert storyos_hot_state.SPECS["INFLIGHT"].ttl_seconds is None

    class FakeStore:
        def __init__(self):self.last=None
        def set_state(self,key,value,expire_seconds=None):
            self.last=(key,value,expire_seconds)
    store=FakeStore()
    storyos_hot_state.EpisodeHotStateStore(store).put(
        "EPU_unit_test","INFLIGHT",{"steps":{"STEP":{"request_id":"real"}}})
    assert store.last[2] is None
