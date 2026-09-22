from platform.operations.operations_console_integration import (
    OperationsConsoleIntegration,
)


def test_operations_console_view_available():
    integration = OperationsConsoleIntegration()

    view = integration.build_view(runtime="v3-runtime")

    assert view.status == "AVAILABLE"
    assert view.readonly is True
    assert "health_view" in view.capabilities


def test_operations_console_view_unavailable():
    integration = OperationsConsoleIntegration()

    view = integration.build_view(
        runtime="v3-runtime",
        available=False,
    )

    assert view.status == "UNAVAILABLE"
