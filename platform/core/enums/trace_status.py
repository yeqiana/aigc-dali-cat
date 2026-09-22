from enum import Enum


class TraceStatus(str, Enum):
    """一次 Trace/Span 执行事实的结果。"""

    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
