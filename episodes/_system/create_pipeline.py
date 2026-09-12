#!/usr/bin/env python3
"""Story OS create pipeline orchestration.

Natural language create entry orchestration layer.

Flow:
    runtime request
        -> story lock preparation
        -> storyboard preparation
        -> character contract preparation
        -> visual lock preparation

This module only coordinates existing modules. It does not create a second
workflow state machine.

Status (Phase 5.6): this is a legacy planning shim. ``story_os.py create`` no longer
calls it; the canonical one sentence entry is ``production_orchestrator.run_full_auto``,
which hands the Episode to workflow_runner.py. It is kept because it writes placeholder
``status: PREPARED`` documents and never produced a real Story Lock, Storyboard,
Character Contract or Visual Lock. Calling ``run`` on a real Episode would write a
placeholder ``meta/character-contract.json`` that later blocks
``character_contract.prepare``, so do not route production through it.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CreatePipelineResult:
    episode_path: Path
    steps: list[str]
    status: str = "PREPRODUCTION_READY"


class CreatePipeline:
    """One sentence production entry coordinator."""

    def __init__(self, story_root: Path):
        self.story_root = story_root

    def run(self, episode_path: Path, request: dict[str, Any]) -> CreatePipelineResult:
        steps: list[str] = []

        self._prepare_story_lock(episode_path, request, steps)
        self._prepare_storyboard(episode_path, steps)
        self._prepare_character_contract(episode_path, steps)
        self._prepare_visual_lock(episode_path, steps)

        return CreatePipelineResult(
            episode_path=episode_path,
            steps=steps,
        )

    def _prepare_story_lock(
        self,
        episode_path: Path,
        request: dict[str, Any],
        steps: list[str],
    ) -> None:
        meta = episode_path / "meta"
        target = meta / "story-lock.json"

        if not target.exists():
            target.write_text(
                '{\n'
                '  "schema_version": 1,\n'
                '  "status": "PREPARED",\n'
                f'  "request": {request.get("request", "")}\n'
                '}\n',
                encoding="utf-8",
            )
        steps.append("STORY_LOCK_PREPARED")

    def _prepare_storyboard(self, episode_path: Path, steps: list[str]) -> None:
        target = episode_path / "meta" / "storyboard.json"
        if not target.exists():
            target.write_text(
                '{\n'
                '  "schema_version": 1,\n'
                '  "frames": [],\n'
                '  "status": "PREPARED"\n'
                '}\n',
                encoding="utf-8",
            )
        steps.append("STORYBOARD_PREPARED")

    def _prepare_character_contract(self, episode_path: Path, steps: list[str]) -> None:
        target = episode_path / "meta" / "character-contract.json"
        if not target.exists():
            target.write_text(
                '{\n'
                '  "schema_version": 1,\n'
                '  "characters": {},\n'
                '  "status": "PREPARED"\n'
                '}\n',
                encoding="utf-8",
            )
        steps.append("CHARACTER_CONTRACT_PREPARED")

    def _prepare_visual_lock(self, episode_path: Path, steps: list[str]) -> None:
        target = episode_path / "meta" / "visual-lock-request.json"
        if not target.exists():
            target.write_text(
                '{\n'
                '  "schema_version": 1,\n'
                '  "policy": "four_admission_v21",\n'
                '  "frames": [\n'
                '    "ordinary_baseline",\n'
                '    "worst_condition",\n'
                '    "first_anomaly",\n'
                '    "high_impact_admission"\n'
                '  ],\n'
                '  "status": "PREPARED"\n'
                '}\n',
                encoding="utf-8",
            )
        steps.append("VISUAL_LOCK_PREPARED")


def run_create_pipeline(
    story_root: Path,
    episode_path: Path,
    request: dict[str, Any],
) -> CreatePipelineResult:
    return CreatePipeline(story_root).run(episode_path, request)
