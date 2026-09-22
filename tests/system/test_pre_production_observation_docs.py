#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pre Production observation docs: the EP004-EP020 runbook and its template.

Docs-only phase: no production code changed, so this test pins the contract the
runbook promises a reader (five steps, six required artifacts, three phases, the
Pattern Learning precondition) plus the fill-in fields of the per-episode
template. It also keeps both documents free of score-like language.
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

RUNBOOK = (ROOT / "docs"
           / "Story_OS_PreProduction_Intelligence_EP004_EP020_Observation_Runbook_V1.0.md")
TEMPLATE = ROOT / "docs" / "templates" / "episode_observation_template.md"
README = ROOT / "pre_production" / "README.md"

FIVE_STEPS = ("Story Lock", "Advisor Analysis", "Observation Record",
              "Production Outcome", "Feedback + Experience Save")
REQUIRED_ARTIFACTS = ("story_fingerprint.yaml", "similarity_report.yaml",
                      "advisor_report.yaml", "observation record",
                      "feedback record", "experience record")
PHASE_IDS = ("EP004", "EP008", "EP009", "EP014", "EP015", "EP020")
TEMPLATE_FIELDS = ("episode_id", "advisor_result", "risk_summary", "creator_decision",
                   "production_result", "experience_status", "learning_notes")
FORBIDDEN_WORDS = ("score", "percent", "percentage", "rank", "threshold")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


class ObservationRunbookTests(unittest.TestCase):

    def test_runbook_exists(self):
        self.assertTrue(RUNBOOK.is_file(), str(RUNBOOK))

    def test_runbook_documents_the_five_fixed_steps(self):
        text = read(RUNBOOK)
        for step in FIVE_STEPS:
            self.assertIn(step, text, step)
        self.assertIn("Step 1", text)
        self.assertIn("Step 5", text)

    def test_runbook_lists_the_six_required_artifacts(self):
        text = read(RUNBOOK)
        for artifact in REQUIRED_ARTIFACTS:
            self.assertIn(artifact, text, artifact)

    def test_runbook_defines_the_three_observation_phases(self):
        text = read(RUNBOOK)
        for phase_id in PHASE_IDS:
            self.assertIn(phase_id, text, phase_id)
        for goal in ("接入验证", "中期观察", "收敛"):
            self.assertIn(goal, text, goal)

    def test_runbook_keeps_pattern_learning_manual(self):
        text = read(RUNBOOK)
        self.assertIn("不自动进入", text)
        self.assertIn("30 – 50", text)
        self.assertIn("重复 Pattern", text)
        self.assertIn("人工确认有效", text)

    def test_runbook_states_the_frozen_boundaries(self):
        text = read(RUNBOOK)
        self.assertIn("blocks_production=false", text)
        self.assertIn("meta/episode-state.json", text)
        self.assertIn("meta/story-gates.json", text)

    def test_runbook_requires_incomplete_instead_of_fabrication(self):
        text = read(RUNBOOK)
        self.assertIn("incomplete", text)
        self.assertIn("禁止补造", text)


class ObservationTemplateTests(unittest.TestCase):

    def test_template_exists(self):
        self.assertTrue(TEMPLATE.is_file(), str(TEMPLATE))

    def test_template_carries_every_required_field(self):
        text = read(TEMPLATE)
        for field in TEMPLATE_FIELDS:
            self.assertIn(field, text, field)

    def test_template_prompts_the_five_review_questions(self):
        text = read(TEMPLATE)
        for question in ("Advisor 是否发现问题", "风险是否真实", "建议是否采用",
                         "最终结果如何", "哪些经验值得保存"):
            self.assertIn(question, text, question)


class DocsHygieneTests(unittest.TestCase):

    def test_readme_points_to_the_runbook_and_template(self):
        text = read(README)
        self.assertIn(RUNBOOK.name, text)
        self.assertIn("episode_observation_template.md", text)

    def test_new_docs_carry_no_score_language(self):
        for path in (RUNBOOK, TEMPLATE):
            text = read(path)
            for word in FORBIDDEN_WORDS:
                self.assertNotIn(word, text.lower(), path.name + " -> " + word)
            self.assertNotIn("%", text, path.name)


if __name__ == "__main__":
    unittest.main()

