from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class BaseContract:
    """所有平台契约的基础结构。

    Contract 只描述事实，不包含流程控制逻辑。
    """

    id: str
    created_at: datetime
    metadata: dict[str, Any]
