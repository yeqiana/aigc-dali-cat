#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from capture_profile import validate
from story_regression import run
from auto_production import validate_plan
class V2(unittest.TestCase):
    def test_capture(self): self.assertEqual(validate(),[])
    def test_regression(self): self.assertEqual(run(),[])
    def test_plan(self):
        d={"frame_count":4,"aspect_ratio":"4:5","calibration_frames":[1,2,3],"visual_admission_frames":[1,2,3,4],
        "frames":[{"number":i,"prompt":f"真实手机随手拍{i}","caption":""} for i in range(1,5)]}
        self.assertTrue(validate_plan(d))
if __name__=="__main__":unittest.main()
