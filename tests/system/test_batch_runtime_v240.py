#!/usr/bin/env python3
from __future__ import annotations
import sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
SYSTEM=ROOT/"episodes/_system"
if str(SYSTEM) not in sys.path:sys.path.insert(0,str(SYSTEM))

import batch_result_mapper
import batch_runtime_config
import frame_failure_assessment

class BatchConfigTests(unittest.TestCase):
    def test_defaults(self):
        self.assertTrue(batch_runtime_config.enabled())
        self.assertEqual(batch_runtime_config.images_per_batch(),5)
        self.assertEqual(batch_runtime_config.repair_thresholds(),(80,80))

class MapperTests(unittest.TestCase):
    def test_exact_five_mapping(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for i in range(1,6):
                # valid_image only requires >16 bytes and PNG header for mapping stage.
                (root/f"out-{i:02d}.png").write_bytes(b"\x89PNG\r\n\x1a\n"+b"x"*32)
            contract={
                "planned_count":5,
                "frames":[
                    {"output_index":i,"frame":f"{i:02d}","queue_item_id":f"id{i}","frame_contract_sha256":f"sha{i}"}
                    for i in range(1,6)
                ]
            }
            rows=batch_result_mapper.map_outputs(root,contract)
            self.assertEqual([x["frame"] for x in rows],["01","02","03","04","05"])

class RepairGateTests(unittest.TestCase):
    def test_high_high_can_repair_before_barrier(self):
        scout={"decision":"REPAIR_NOW","issue_codes":["IDENTITY_OBVIOUS_DRIFT"],"confidence":0.95}
        with patch("frame_failure_assessment.criticality_score",return_value=90):
            row=frame_failure_assessment.assess(Path("."),13,scout,batch_complete=False)
        self.assertEqual(row["deviation_score"],80)
        self.assertTrue(row["high_high"])
        self.assertEqual(row["action"],"EARLY_SINGLE_REPAIR")

    def test_high_deviation_low_criticality_waits_batch(self):
        scout={"decision":"REPAIR_NOW","issue_codes":["IDENTITY_OBVIOUS_DRIFT"],"confidence":0.95}
        with patch("frame_failure_assessment.criticality_score",return_value=70):
            row=frame_failure_assessment.assess(Path("."),13,scout,batch_complete=False)
        self.assertFalse(row["high_high"])
        self.assertEqual(row["action"],"WAIT_BATCH")

    def test_after_barrier_ordinary_failure_repairs_single(self):
        scout={"decision":"REPAIR_NOW","issue_codes":["WEATHER_OBVIOUS_MISMATCH"],"confidence":0.8}
        with patch("frame_failure_assessment.criticality_score",return_value=90):
            row=frame_failure_assessment.assess(Path("."),13,scout,batch_complete=True)
        self.assertEqual(row["action"],"SINGLE_REPAIR")

if __name__=="__main__":unittest.main()
