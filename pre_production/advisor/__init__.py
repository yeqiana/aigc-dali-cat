#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Advisor: turn similarity evidence into risks, recommendations and a report."""
from __future__ import annotations

from .recommendation import build_recommendations
from .report_generator import build_report, confidence_level, decide
from .risk_assessor import assess_hook_risk, assess_risks, assess_similarity_risks

__all__ = [
    "assess_risks",
    "assess_similarity_risks",
    "assess_hook_risk",
    "build_recommendations",
    "build_report",
    "decide",
    "confidence_level",
]

