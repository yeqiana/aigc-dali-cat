from platform.operations.runtime_operations_observability_api import (
    RuntimeOperationsObservabilityAPI,
)


class MockSnapshot:
    runtime = "v3-runtime"
    operations_status = "HEALTHY"
    health_status = "HEALTHY"
    incident_count = 0
    reliability_status = "HEALTHY"
    cost_status = "NORMAL"
    performance_status = "OPTIMAL"
    learning_status = "READY"


def test_runtime_operations_view_build():
    api = RuntimeOperationsObservabilityAPI()

    view = api.build_view(MockSnapshot())

    assert view.runtime == "v3-runtime"
    assert view.status == "HEALTHY"
    assert view.incidents == 0
