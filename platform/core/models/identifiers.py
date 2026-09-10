from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from platform.core.clock import utc_now


@dataclass(frozen=True)
class Identifier:
    """平台统一ID模型。"""

    value: str

    @staticmethod
    def create(prefix: str) -> "Identifier":
        return Identifier(f"{prefix}_{uuid4().hex}")


@dataclass(frozen=True)
class PlatformContext:
    """跨模块传递的基础上下文。"""

    request_id: str
    created_at: datetime

    @staticmethod
    def create() -> "PlatformContext":
        return PlatformContext(
            request_id=Identifier.create("req").value,
            created_at=utc_now(),
        )
