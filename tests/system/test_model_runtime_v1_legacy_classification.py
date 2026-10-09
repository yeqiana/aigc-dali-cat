from __future__ import annotations
import sys
from pathlib import Path
SYSTEM=Path(__file__).resolve().parents[2]/"episodes"/"_system"
if str(SYSTEM) not in sys.path:sys.path.insert(0,str(SYSTEM))
from model_runtime_v1 import legacy_classification as lc

def test_proxy_must_be_retired_but_not_blindly_deleted():
    row=lc.classify("codex_user_runner")
    assert row["route_kind"]=="DYNAMIC_OPENCODEX_FALLBACK"
    assert row["can_delete"] is False
    assert row["production_route_retired"] is False

def test_webcodex_workspace_not_same_as_model_provider():
    assert lc.classify("webcodex_workspace")["route_kind"]=="WORKSPACE_PROVIDER"

def test_official_image_api_should_not_be_deleted():
    assert lc.classify("openai_images_provider")["action"]=="KEEP_AS_POTENTIAL_API_IMAGE_ADAPTER"

def test_unknown_route_does_not_authorize_cleanup():
    assert lc.classify("made_up")["can_delete"] is False
