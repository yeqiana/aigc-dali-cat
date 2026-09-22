from platform.adapter.contracts import SubmitTaskRequest
from platform.adapter.runtime_adapter import RuntimeAdapter


def test_adapter_keeps_runtime_boundary():
    adapter = RuntimeAdapter()

    result = adapter.submit_task(
        SubmitTaskRequest(
            task_type="IMAGE_GENERATION",
            episode_id="ep002",
            payload={},
        )
    )

    assert result == "ADAPTER_ONLY"


def test_query_task_returns_adapter_result():
    result = RuntimeAdapter().query_task("task001")

    assert result.task_id == "task001"
    assert result.status == "UNKNOWN"
