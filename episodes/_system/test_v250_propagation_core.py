#!/usr/bin/env python3
import unittest
from propagation_core_gate import validate_payload
def core():
    return {"retell_sentence":"他按了一次按钮，异常立刻回应。","protagonist_action":"按按钮",
    "abnormal_response":"对面所有显示屏同时熄灭","consequence":"出口标识变成同一方向",
    "response_latency":"immediate","visual_causality":"strong","retellable_in_10s":True,
    "social_send_impulse":"strong","trigger_frame":8,"response_frame":9,"payoff_frame":12,
    "late_trigger_exception_reason":"","surface_copy_guard":{"structural_reference_only":True,"copied_surface_elements":[]}}
class T(unittest.TestCase):
    def test_valid(self):self.assertEqual(validate_payload(core(),20),[])
    def test_late(self):
        x=core();x.update(trigger_frame=12,response_frame=13,payoff_frame=14)
        self.assertTrue(any(e.startswith("TRIGGER_TOO_LATE") for e in validate_payload(x,20)))
    def test_late_reason(self):
        x=core();x.update(trigger_frame=12,response_frame=13,payoff_frame=14,late_trigger_exception_reason="前十图必须先建立空间证据。")
        self.assertFalse(any(e.startswith("TRIGGER_TOO_LATE") for e in validate_payload(x,20)))
    def test_weak(self):
        x=core();x["visual_causality"]="weak"
        self.assertTrue(any(e.startswith("VISUAL_CAUSALITY_WEAK") for e in validate_payload(x,20)))
    def test_clone(self):
        x=core();x["surface_copy_guard"]["copied_surface_elements"]=["川西山路"]
        self.assertTrue(any(e.startswith("SURFACE_COPY_GUARD_FAILED") for e in validate_payload(x,20)))
if __name__=="__main__":unittest.main()
