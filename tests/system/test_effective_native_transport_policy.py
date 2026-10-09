from __future__ import annotations
import os
import sys
from pathlib import Path
from unittest.mock import patch
SYSTEM=Path(__file__).resolve().parents[2]/"episodes"/"_system"
if str(SYSTEM) not in sys.path: sys.path.insert(0,str(SYSTEM))
import effective_config

def test_native_default_policy_not_claimed_as_tool_attested():
    with patch.dict(os.environ,{"STORY_OS_IMAGE_PROVIDER_ROUTE":""}):
        row=effective_config.snapshot()["image_transport_policy"]
    assert row["required"]=="native_codex"
    assert row["status"]=="POLICY_ALLOWED_NOT_ATTESTED"
    assert row["session_image_tool_attested"] is None

def test_proxy_environment_is_visible_as_policy_blocked():
    with patch.dict(os.environ,{"STORY_OS_IMAGE_PROVIDER_ROUTE":"opencodex"}):
        row=effective_config.snapshot()["image_transport_policy"]
    assert row["requested"]=="opencodex"
    assert row["status"]=="BLOCKED"
    assert row["reason"]=="CODEX_NATIVE_IMAGE_PROVIDER_REQUIRED"
