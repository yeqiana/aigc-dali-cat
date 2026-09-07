#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.7 runtime failure classification.

This module only classifies failures. It does not bypass gates or change stage authority.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FailureDecision:
    category: str
    action: str
    retryable: bool
    reason: str


TECH_KEYWORDS = (
    "timeout",
    "websocket",
    "provider",
    "502",
    "503",
    "connection",
    "network",
    "rate limit",
)

CONTENT_KEYWORDS = (
    "visual",
    "identity",
    "character",
    "gate",
    "quality",
    "contract",
)


def classify(return_code: int, note: str = "") -> FailureDecision:
    text = (note or "").lower()

    # Protocol results take precedence over words in a stage/contract name.
    explicit = {
        0: FailureDecision("SUCCESS", "CONTINUE", False, "completed"),
        20: FailureDecision("HOST_WAIT", "WAIT_HOST", False, "host action pending"),
        21: FailureDecision("TECH_FAILED", "RETRY", True, "recoverable execution failure"),
        22: FailureDecision("HUMAN_REQUIRED", "PAUSE", False, "explicit human decision required"),
        23: FailureDecision("HARD_STOP", "STOP", False, "invalid execution state"),
        24: FailureDecision("CAPABILITY_WAIT", "WAIT_CAPABILITY", False, "image capability unavailable"),
    }
    if return_code in explicit:
        return explicit[return_code]
    if return_code in {124, 408, 429, 502, 503}:
        return FailureDecision("TECH_FAILED", "RETRY", True, "known transient runtime code")

    if any(x in text for x in TECH_KEYWORDS):
        return FailureDecision(
            "TECH_FAILED",
            "RETRY",
            True,
            "temporary infrastructure/provider failure",
        )

    if any(x in text for x in CONTENT_KEYWORDS):
        return FailureDecision(
            "CONTENT_FAILED",
            "REPAIR",
            False,
            "content validation failure requires controlled repair",
        )

    return FailureDecision(
        "UNCLASSIFIED_FAILURE", "RETRY", True,
        "unclassified execution error; bounded retry before escalation",
    )


def should_retry(attempt: int, decision: FailureDecision, max_attempts: int = 3) -> bool:
    return decision.retryable and attempt < max_attempts


if __name__ == "__main__":
    print(classify(503, "provider timeout"))
