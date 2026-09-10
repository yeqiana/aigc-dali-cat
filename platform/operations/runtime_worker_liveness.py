"""Runtime Worker 存活判定（P9.30）。

背景（P9.29 演练 finding worker_liveness_not_critical，HIGH）：

    Worker 进程消失后不会再跑 tick，而 RuntimeHealthMonitor 只看 trace 事实，
    因此「Worker 不在」既不能由 Worker 自己上报，也不能由健康模型表达。
    失联必须由外部观察者判定。

本模块只做纯评估，不做任何 I/O：

    expected = 名册里记录过的 Worker（曾经在线过）
    observed = 本次扫描仍能读到心跳的 Worker
    missing  = expected - observed  ->  CRITICAL worker_liveness_lost

I/O（Redis SCAN、心跳读取、状态落盘）由 scripts/phase9_liveness_watchdog.py 负责，
这样判定口径可以离线单测，不需要真实 Redis。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Callable, Iterable, Mapping


DEFAULT_PREFIX = "storyos:worker:"
HEARTBEAT_KEY_SUFFIX = ":heartbeat"

LIVENESS_ALERT_SOURCE = "liveness_watchdog"
LIVENESS_LOST_REASON = "worker_liveness_lost"
LIVENESS_LEVEL = "CRITICAL"

STATUS_ONLINE = "ONLINE"
STATUS_MISSING = "MISSING"


def heartbeat_key(worker_id: str, prefix: str = DEFAULT_PREFIX) -> str:
    """与 WorkerHeartbeat.PREFIX 保持一致的心跳键。"""
    return prefix + worker_id + HEARTBEAT_KEY_SUFFIX


def worker_id_from_key(key: str, prefix: str = DEFAULT_PREFIX) -> str | None:
    """从心跳键反解 worker_id；不是心跳键时返回 None。"""
    if not key.startswith(prefix) or not key.endswith(HEARTBEAT_KEY_SUFFIX):
        return None
    worker_id = key[len(prefix):-len(HEARTBEAT_KEY_SUFFIX)]
    return worker_id or None


def seconds_since(value, now: datetime) -> float | None:
    """心跳时间到 now 的秒数；无法解析时返回 None，不猜测。"""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None
    return round((now - parsed).total_seconds(), 3)


@dataclass(frozen=True)
class WorkerLivenessRecord:
    worker_id: str
    status: str
    heartbeat_time: str | None = None
    heartbeat_status: str | None = None
    seconds_since_heartbeat: float | None = None


def evaluate_liveness(
    *,
    expected: Iterable[str],
    observed: Iterable[str],
    read_heartbeat: Callable[[str], Mapping[str, Any] | None],
    now: datetime,
) -> dict:
    """expected 与 observed 的差集即失联集合；每个失联 Worker 产生一条 CRITICAL。

    以 read_heartbeat 的真实返回为准（而不是只看 SCAN 结果）：
    SCAN 到键但读不到值，同样算失联。
    """
    expected_ids = sorted({str(item) for item in (expected or ())})
    observed_ids = sorted({str(item) for item in (observed or ())})

    records: list = []
    missing: list = []
    for worker_id in expected_ids:
        value = read_heartbeat(worker_id)
        if value is None:
            missing.append(worker_id)
            records.append(
                WorkerLivenessRecord(worker_id=worker_id, status=STATUS_MISSING)
            )
            continue
        records.append(
            WorkerLivenessRecord(
                worker_id=worker_id,
                status=STATUS_ONLINE,
                heartbeat_time=value.get("heartbeat_time"),
                heartbeat_status=value.get("status"),
                seconds_since_heartbeat=seconds_since(value.get("heartbeat_time"), now),
            )
        )

    alerts = [
        {
            "source": LIVENESS_ALERT_SOURCE,
            "level": LIVENESS_LEVEL,
            "reason": LIVENESS_LOST_REASON,
            "worker_id": worker_id,
            "detail": {
                "worker_id": worker_id,
                "expected_status": STATUS_ONLINE,
                "observed_status": STATUS_MISSING,
            },
        }
        for worker_id in missing
    ]

    return {
        "status": STATUS_MISSING if missing else STATUS_ONLINE,
        "expected": expected_ids,
        "observed": observed_ids,
        "missing": missing,
        "records": [asdict(record) for record in records],
        "alerts": alerts,
    }
