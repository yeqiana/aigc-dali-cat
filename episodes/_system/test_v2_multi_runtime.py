#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, unittest
from pathlib import Path
from capture_profile import validate as validate_capture
from story_regression import run as run_regression
from release_preflight import similarity
class Tests(unittest.TestCase):
    def test_capture(self): self.assertEqual(validate_capture(),[])
    def test_regression(self): self.assertEqual(run_regression(),[])
    def test_similarity(self):
        keys=("core_anomaly_mechanism","story_engine","entry_mode","anomaly_carrier","primary_visual_space","middle_escalation","climax_form","relationship","reality_residue")
        d={k:"same" for k in keys}; score,veto,_=similarity({"dimensions":d},{"dimensions":d}); self.assertEqual(score,100); self.assertTrue(veto)
    def test_contract(self):
        root=Path(__file__).resolve().parents[2]; d=json.loads((root/"runtimes"/"runtime-contract.json").read_text(encoding="utf-8"))
        self.assertEqual(d["routing_order"],["WORK","CODEX","WEB"]); self.assertEqual(d["common_rules"]["default_runtime"],"WORK"); self.assertTrue(d["common_rules"]["work_web_must_not_spawn_local_codex"]); self.assertTrue(d["common_rules"]["do_not_create_second_episode_stage"])
if __name__=="__main__": unittest.main()
