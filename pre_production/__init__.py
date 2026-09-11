#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS Pre Production Intelligence (MVP).

Story Lock -> Story DNA -> Similarity Analysis -> Advisor Report -> Memory.

This package is an advisory layer only:
- it never mutates episode-state.json or story-gates.json,
- it never blocks or rewrites the Production Runtime,
- it only emits PASS / WARNING / NEEDS_REVISION reports backed by evidence,
- it never emits a numeric similarity score.

See pre_production/README.md for the frozen boundaries and usage.
"""
from __future__ import annotations

__all__ = [
    "story_dna",
    "similarity_analysis",
    "advisor",
    "memory_adapter",
    "shadow_mode",
]

MODULE_ID = "pre_production_intelligence"
MODULE_VERSION = "0.1.0"

