from platform.operations.runtime_operations_slo_sla_management import (
    RuntimeOperationsSLOSLAManagement,
)


def test_slo_compliant():
    snapshot = RuntimeOperationsSLOSLAManagement().evaluate(
        runtime="v3-runtime",
        availability=99.9,
        latency_ms=500,
        error_rate=1,
        mttr_minutes=20,
    )

    assert snapshot.status == "COMPLIANT"


def test_slo_warning():
    snapshot = RuntimeOperationsSLOSLAManagement().evaluate(
        runtime="v3-runtime",
        availability=98.5,
        latency_ms=1000,
        error_rate=2,
        mttr_minutes=30,
    )

    assert snapshot.status == "WARNING"
