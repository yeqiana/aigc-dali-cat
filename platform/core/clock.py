"""平台统一时间约定（P9.27）。

规则：
    Runtime 事实与数据库落库时间统一使用 **naive UTC 墙钟值**。
    对外 JSON 证据时间戳（gateway / audit / api 响应）继续使用 aware ISO
    （带 +00:00），因为这类产物需要跨时区自描述。

Runtime 事实链路禁止再使用 `datetime.utcnow()`（Python 3.12 起已弃用）。
"""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """当前 UTC 的 naive 墙钟值。

    语义等价旧的 `datetime.utcnow()`，但不走弃用 API。
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utc_now_iso(timespec: str = "milliseconds") -> str:
    """当前 UTC 的 naive ISO 字符串（JSONL / ExecutionRecorder 用）。"""
    return utc_now().isoformat(timespec=timespec)


def to_naive_utc(value):
    """把 aware datetime 归一化为 naive UTC。

    naive datetime、非 datetime 值原样返回。
    pymysql 写 DATETIME 时会丢弃 tzinfo，这里显式转换，
    避免“带时区写入 + 不带时区读出”的时间漂移。
    """
    if isinstance(value, datetime) and value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value

