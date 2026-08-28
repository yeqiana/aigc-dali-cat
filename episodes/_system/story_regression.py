#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CASES=ROOT/"standards"/"story_regressions"/"cases.json"
def evaluate(dim,p):
    if dim=="location_reality": return "fail" if p.get("rural_village") and p.get("public_bus_visible") and not p.get("transport_pre_registered") else "pass"
    if dim=="viewpoint_physics": return "fail" if p.get("first_person_device_fully_visible") and not p.get("second_source_explained") else "pass"
    if dim=="minimal_edit": return "fail" if p.get("edit_mode")=="subtitle_only" and p.get("locked_base_hash_changed") else "pass"
    if dim=="caption_voice": return "warning" if int(p.get("consecutive_i_found",0))>=3 else "pass"
    if dim=="payoff": return "fail" if p.get("major_final_anomaly") and not p.get("setup_exists") else "pass"
    if dim=="homogeneity": return "fail" if all(p.get(k) for k in ("same_core_mechanism","same_middle_escalation","same_climax_form")) else "pass"
    if dim=="mechanism_consistency": return "fail" if p.get("same_anomaly_has_unexplained_return_guidance_marking_behaviors") else "pass"
    if dim=="causal_order": return "fail" if p.get("rule_warning_occurs_after_violation") and not p.get("prior_rule_setup_exists") else "pass"
    if dim=="character_stake": return "fail" if p.get("missing_person_becomes_plot_tool") and p.get("relationship_stake_not_established") else "pass"
    if dim=="climax_payoff": return "fail" if p.get("climax_is_discovery_only") and not p.get("choice_or_cost") else "pass"
    if dim=="ending_payoff": return "fail" if p.get("ending_adds_new_mechanism") and int(p.get("recontextualized_prior_facts",0)) < 3 else "pass"
    if dim=="subtitle_layout":
        return "auto_fix" if not p.get("contains_semantic_character") and p.get("required_action")=="drop_entire_second_line" else "pass"
    return "unknown"
def run():
    d=json.loads(CASES.read_text(encoding="utf-8")); return [c["id"] for c in d["cases"] if evaluate(c["dimension"],c["fixture"])!=c["expected"]]
def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True); sub.add_parser("run"); sub.add_parser("show"); a=ap.parse_args()
    if a.cmd=="show": print(CASES.read_text(encoding="utf-8")); return 0
    e=run()
    if e: [print("FAIL:",x) for x in e]; return 2
    print("STORY REGRESSION PASS"); return 0
if __name__=="__main__": raise SystemExit(main())
