from platform.operations.runtime_alert_incident_management import RuntimeAlertManager
from platform.operations.runtime_health_monitoring import RuntimeHealthMonitor


def test_create_warning_alert_for_degraded_runtime():
    snapshot = RuntimeHealthMonitor().evaluate(
        agent_success_rate=0.95,
        workflow_success_rate=0.95,
        trace_healthy=False,
        memory_healthy=True,
    )

    alert = RuntimeAlertManager().evaluate(snapshot)

    assert alert.level == "WARNING"


def test_create_critical_incident_for_unhealthy_runtime():
    snapshot = RuntimeHealthMonitor().evaluate(
        agent_success_rate=0,
        workflow_success_rate=0,
        trace_healthy=False,
        memory_healthy=False,
    )

    manager = RuntimeAlertManager()
    incident = manager.create_incident(
        manager.evaluate(snapshot),
        "INC-001",
    )

    assert incident.status == "OPEN"
    assert incident.alert_level == "CRITICAL"
