"""Single fail-closed clock rule for Story OS review/evidence timestamps."""
from __future__ import annotations

import datetime as dt

MAX_FUTURE_SKEW_SECONDS = 300


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def parse_timestamp(raw: object) -> dt.datetime:
    text = str(raw or "").strip()
    if not text:
        raise ValueError("timestamp missing")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    value = dt.datetime.fromisoformat(text)
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include timezone offset")
    return value.astimezone(dt.timezone.utc)


def validate_timestamp(raw: object, *, field: str, required: bool = True,
                       now_value: dt.datetime | None = None,
                       max_future_skew_seconds: int = MAX_FUTURE_SKEW_SECONDS) -> list[str]:
    text = str(raw or "").strip()
    if not text:
        return [f"{field} missing"] if required else []
    try:
        value = parse_timestamp(text)
    except (TypeError, ValueError) as exc:
        return [f"{field} invalid: {exc}"]
    current = (now_value or now()).astimezone(dt.timezone.utc)
    limit = current + dt.timedelta(seconds=max(0, int(max_future_skew_seconds)))
    if value > limit:
        ahead = int((value - current).total_seconds())
        return [f"{field} is in the future by {ahead}s (allowed clock skew {max_future_skew_seconds}s)"]
    return []
