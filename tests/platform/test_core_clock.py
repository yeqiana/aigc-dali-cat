from datetime import datetime, timedelta, timezone

from platform.core.clock import to_naive_utc, utc_now, utc_now_iso


def test_utc_now_is_naive_and_tracks_real_utc():
    now = utc_now()
    real = datetime.now(timezone.utc).replace(tzinfo=None)
    assert now.tzinfo is None
    assert abs((real - now).total_seconds()) < 5


def test_utc_now_iso_is_naive_and_parsable():
    text = utc_now_iso()
    parsed = datetime.fromisoformat(text)
    assert parsed.tzinfo is None
    assert parsed.year == utc_now().year


def test_utc_now_iso_supports_seconds_timespec():
    assert len(utc_now_iso('seconds')) == 19


def test_to_naive_utc_converts_aware_datetime_to_utc_wall_clock():
    shanghai = timezone(timedelta(hours=8))
    aware = datetime(2026, 9, 10, 20, 34, 56, 789012, tzinfo=shanghai)
    converted = to_naive_utc(aware)
    assert converted == datetime(2026, 9, 10, 12, 34, 56, 789012)
    assert converted.tzinfo is None


def test_to_naive_utc_passes_other_values_through():
    naive = datetime(2026, 9, 10, 12, 0, 0)
    assert to_naive_utc(naive) is naive
    assert to_naive_utc('not-a-datetime') == 'not-a-datetime'
    assert to_naive_utc(None) is None


def test_mysql_connection_reexports_the_same_helper():
    from platform.core.clock import to_naive_utc as from_clock
    from platform.repository.mysql.mysql_connection import to_naive_utc as from_mysql

    assert from_mysql is from_clock


def test_runtime_fact_sources_do_not_use_deprecated_utcnow():
    """Runtime 事实链路必须统一用 platform.core.clock，不再用弃用的 utcnow。"""
    import inspect

    from platform.agent.runtime import agent_runtime, execution_recorder
    from platform.core.models import identifiers
    from platform.observer import artifact_observer, event_observer, trace_observer
    from platform.state import worker_heartbeat
    from platform.validation import ep_runtime_probe

    modules = (
        identifiers,
        worker_heartbeat,
        execution_recorder,
        agent_runtime,
        ep_runtime_probe,
        event_observer,
        trace_observer,
        artifact_observer,
    )
    for module in modules:
        assert 'datetime.utcnow()' not in inspect.getsource(module), module.__name__
