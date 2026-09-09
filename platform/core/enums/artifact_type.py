from enum import Enum


class ArtifactType(str, Enum):
    """Story OS 平台资产类型。"""

    STORY = "STORY"
    FRAME = "FRAME"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    PROMPT = "PROMPT"
    EVIDENCE = "EVIDENCE"
    RELEASE = "RELEASE"
