#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""release_preflight preflight verification/compliance domain (B4 split)."""

from __future__ import annotations

import argparse
from pathlib import Path
from story_os_contract import story_os_version
from release_preflight_review import validate_release_review
from release_preflight_core import *

def cmd_init_compliance(args: argparse.Namespace) -> int:
    ep = ep_path(args.episode_dir)
    p = ep / COMPLIANCE_REL
    if p.is_file() and not args.force:
        print("publish-compliance.json already exists")
        return 0
    data = {
        "schema_version": 1,
        "story_os_version": episode_contract_version(ep),
        "ai_generated": True,
        "platform_ai_label_required": True,
        "platform_ai_label_method": "douyin_platform_declaration",
        "fiction_context_notice_required": True,
        "fiction_context_notice": "AI生成剧情内容；故事为虚构创作，真实地点仅作为故事背景。",
        "user_must_confirm_label_at_publish_time": True,
        "prepared_at": now(),
    }
    write_json(p, data)
    print("PUBLISH COMPLIANCE: initialized")
    return 0

def verify_governance(ep: Path) -> list[str]:
    if not guard_required(ep):
        return []
    p = ep / COMPLIANCE_REL
    if not p.is_file():
        return ["meta/publish-compliance.json missing; run init-compliance"]
    try:
        data = read_json(p)
    except Exception as exc:
        return [str(exc)]
    errors = []
    if data.get("ai_generated") is not True:
        errors.append("publish compliance must declare ai_generated=true")
    if data.get("platform_ai_label_required") is not True:
        errors.append("platform_ai_label_required must be true")
    if data.get("platform_ai_label_method") != "douyin_platform_declaration":
        errors.append("platform_ai_label_method must be douyin_platform_declaration")
    if data.get("fiction_context_notice_required") is not True:
        errors.append("fiction_context_notice_required must be true for realistic fictional Story OS releases")
    if not str(data.get("fiction_context_notice") or "").strip():
        errors.append("fiction_context_notice missing")
    if data.get("user_must_confirm_label_at_publish_time") is not True:
        errors.append("publish-time AI label confirmation flag missing")
    return errors

def verify_release_semantic(ep: Path) -> list[str]:
    if not guard_required(ep):
        return []
    p = ep / RELEASE_REVIEW_REL
    if not p.is_file():
        return ["meta/release-semantic-review.json missing; run run-release-critic"]
    try:
        return validate_release_review(ep, read_json(p))
    except Exception as exc:
        return [str(exc)]

def cmd_enable(args: argparse.Namespace) -> int:
    ep = ep_path(args.episode_dir)
    write_json(ep / ENABLE_REL, {
        "schema_version": 1,
        "enabled": True,
        "story_os_version": story_os_version(),
        "enabled_at": now(),
        "reason": args.reason,
    })
    print("RELEASE GUARD ENABLED")
    return 0

