from enum import Enum


class EntityType(str, Enum):
    """Story OS 平台基础实体类型。"""

    PROJECT = "PROJECT"
    EPISODE = "EPISODE"
    WORKFLOW = "WORKFLOW"
    TASK = "TASK"
    ARTIFACT = "ARTIFACT"
