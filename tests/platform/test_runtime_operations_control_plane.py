from platform.operations.runtime_operations_control_plane import (
    RuntimeOperationsControlPlane,
)


def test_operations_control_plane_healthy():
    plane = RuntimeOperationsControlPlane()

    snapshot = plane.evaluate(
        runtime="v3-runtime",
        health_status="HEALTHY",
        incident_count=0,
        recovery_ready=True,
        reliability_status="HEALTHY",
        cost_status="NORMAL",
        performance_status="OPTIMAL",
        learning_status="READY",
    )

    assert snapshot.operations_status == "HEALTHY"


def test_operations_control_plane_action_required():
    plane = RuntimeOperationsControlPlane()

    snapshot = plane.evaluate(
        runtime="v3-runtime",
        health_status="DEGRADED",
        incident_count=1,
        recovery_ready=False,
        reliability_status="DEGRADED",
        cost_status="WARNING",
        performance_status="BOTTLENECK",
        learning_status="READY",
    )

    assert snapshot.operations_status == "ACTION_REQUIRED"
    assert "active_incident" in snapshot.reasons
