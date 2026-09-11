#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recommendation mapping: risk -> concrete, non-binding suggestions."""
from __future__ import annotations


def build_recommendations(risks: list[dict], dna: dict) -> list[str]:
    """Map risks to ordered recommendation tokens (duplicates removed)."""
    out: list[str] = []

    def add(token: str) -> None:
        if token not in out:
            out.append(token)

    for risk in risks:
        level = risk.get("level")
        dims = risk.get("matched_dimensions") or []
        if risk.get("type") == "similarity":
            if level == "HIGH":
                if "anomaly" in dims:
                    add("redesign_anomaly_mechanism")
                if "setting" in dims:
                    add("avoid_repeated_spatial_expression")
                if "visual_pattern" in dims:
                    add("change_visual_pattern")
            elif level == "MEDIUM":
                add("increase_mechanism_differentiation")
        elif risk.get("type") == "hook":
            if level in {"MEDIUM", "HIGH"}:
                add("strengthen_first_frame_conflict")

    return out


__all__ = ["build_recommendations"]

