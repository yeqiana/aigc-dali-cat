#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shadow Observation: episode observation ledger + human advisor feedback.

This subpackage is additive and manual. It never runs as part of the production
Runtime and never touches episode state or story gates.
"""
from __future__ import annotations

from .feedback import (
    DEFAULT_FEEDBACK_DIR,
    build_feedback,
    feedback_id_for,
    list_feedback,
    load_feedback,
    report_sha256,
    save_feedback,
    unknown_evidence_refs,
)
from .ledger import (
    DEFAULT_LEDGER_PATH,
    append_entry,
    build_entry,
    entry_key,
    find_entry,
    highest_risk_level,
    index_by_episode,
    observation_id,
    read_entries,
    scan_ledger,
    summarize,
)

__all__ = [
    "DEFAULT_LEDGER_PATH",
    "DEFAULT_FEEDBACK_DIR",
    "append_entry",
    "build_entry",
    "build_feedback",
    "entry_key",
    "feedback_id_for",
    "find_entry",
    "highest_risk_level",
    "index_by_episode",
    "list_feedback",
    "load_feedback",
    "observation_id",
    "read_entries",
    "report_sha256",
    "save_feedback",
    "scan_ledger",
    "summarize",
    "unknown_evidence_refs",
]

