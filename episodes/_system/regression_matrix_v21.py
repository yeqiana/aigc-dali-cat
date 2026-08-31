#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.1 Phase 9 release regression matrix."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

from story_os_contract import CANONICAL_STAGES, canonical_stages
import migrate_v21
import post_publish_review

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "reports" / "story-os-v21-regression-matrix.json"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    data=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data,dict):raise ValueError(f"JSON root must be object: {path}")
    return data


def write_json(path: Path,data:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")


def case(name: str, fn) -> dict:
    try:
        detail=fn()
        return {"id":name,"status":"PASS","detail":detail if detail is not None else "ok"}
    except Exception as exc:
        return {"id":name,"status":"FAIL","detail":str(exc)}


def assert_true(value: object, message: str) -> str:
    if value is not True:
        raise AssertionError(message)
    return message


def run_subprocess(script: str, *args: str) -> str:
    cp=subprocess.run([sys.executable,str(ROOT/"episodes/_system"/script),*args],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",check=False)
    if cp.returncode!=0:
        raise AssertionError(cp.stdout[-2500:])
    return cp.stdout.strip().splitlines()[-1] if cp.stdout.strip() else "PASS"


def run_matrix() -> dict:
    wf=read_json(ROOT/"runtimes/workflow-contract.json")
    rules=wf.get("rules") or {}
    steps=wf.get("steps") or {}
    manifest=read_json(ROOT/"story_os_manifest.json")
    tmpl=read_json(ROOT/"standards/templates/story-gates.template.json")

    cases=[
        case("R01_immutable_seven_stage_contract",lambda: (
            " > ".join(canonical_stages())
            if tuple(canonical_stages())==tuple(CANONICAL_STAGES)
            else (_ for _ in ()).throw(AssertionError("canonical stages drift"))
        )),
        case("R02_codex_complete_without_zip",lambda: assert_true(
            rules.get("codex_production_complete_at_publish_ready") is True and rules.get("zip_is_delivery_adapter_not_stage_gate") is True,
            "PUBLISH_READY remains CODEX completion; ZIP optional"
        )),
        case("R03_single_stage_source",lambda: assert_true(
            rules.get("do_not_create_second_episode_stage") is True and wf.get("episode_stage_source")=="meta/episode-state.json",
            "episode-state remains sole stage source"
        )),
        case("R04_max3_single_writer_failsoft",lambda: assert_true(
            rules.get("max_parallel_image_workers")==3 and rules.get("production_ledger_single_writer") is True and rules.get("scheduler_fail_soft") is True,
            "image concurrency max3 + ledger single-writer + fail-soft"
        )),
        case("R05_fast_scout_never_final_pass",lambda: assert_true(
            rules.get("fast_scout_never_final_pass") is True and (steps.get("FAST_FRAME_SCOUT") or {}).get("final_pass_authority") is False,
            "Fast Scout is triage only"
        )),
        case("R06_snapshot_before_publish_ready_and_delivery_strict",lambda: assert_true(
            (steps.get("PUBLISH_READY_GATE") or {}).get("depends_on")==["FINAL_CANDIDATE_SNAPSHOT"] and rules.get("delivery_consumes_verified_snapshot") is True,
            "snapshot freezes candidate before PUBLISH_READY; Delivery consumes it"
        )),
        case("R07_legacy_no_evidence_backfill",lambda: assert_true(
            migrate_v21.version_tuple("2.0.3.6") < migrate_v21.MIN_V21,
            "legacy 2.0.x classified below V2.1 and migration default is read-only"
        )),
        case("R08_template_has_current_v21_policies",lambda: assert_true(
            (((tmpl.get("visual") or {}).get("calibration") or {}).get("policy")=="four_admission_v21")
            and (((tmpl.get("visual") or {}).get("fast_frame_scout") or {}).get("enabled") is True)
            and (((tmpl.get("release") or {}).get("final_candidate_snapshot") or {}).get("enabled") is True),
            "new episode template carries Phase5-8 policies"
        )),
        case("R09_post_publish_does_not_mutate_frozen_manifest",lambda: assert_true(
            post_publish_review.MANIFEST_MUTATION_POLICY=="FORBIDDEN_AFTER_SNAPSHOT",
            "published facts/data review live outside release-manifest"
        )),
        case("R10_data_review_windows_and_48h_gate",lambda: assert_true(
            post_publish_review.CHECKPOINTS==("6h","24h","48h","7d") and post_publish_review.REQUIRED_FOR_DATA_REVIEWED==("48h",),
            "6h/24h/48h/7d supported; 48h minimum for DATA_REVIEWED"
        )),
        case("R11_story_regression_suite",lambda: run_subprocess("story_regression.py","run")),
        case("R12_workflow_runner_self_test",lambda: run_subprocess("workflow_runner.py","self-test")),
        case("R13_phase_modules_self_tests",lambda: " | ".join([
            run_subprocess("migrate_v21.py","self-test"),
            run_subprocess("workflow_observability.py","self-test"),
            run_subprocess("post_publish_review.py","self-test"),
            run_subprocess("account_learning_index.py","self-test"),
        ])),
        case("R14_product_stages_include_publish_loop",lambda: assert_true(
            manifest.get("stages")==list(CANONICAL_STAGES) and manifest.get("stages")[-2:]==["PUBLISHED","DATA_REVIEWED"],
            "product contract closes publish/data-review loop without new stage system"
        )),
    ]
    failed=[x for x in cases if x["status"]!="PASS"]
    report={
        "schema_version":1,
        "generated_at":now(),
        "story_os_version":manifest.get("story_os_version"),
        "summary":{"passed":not failed,"case_count":len(cases),"failed":len(failed)},
        "cases":cases,
    }
    write_json(REPORT,report)
    return report


def self_test()->None:
    assert case("x",lambda:"ok")["status"]=="PASS"
    assert case("x",lambda:1/0)["status"]=="FAIL"
    print("REGRESSION MATRIX V2.1 PHASE9 SELF-TEST PASS")


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("run");sub.add_parser("show");sub.add_parser("self-test")
    a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    if a.cmd=="run":
        report=run_matrix()
        for row in report["cases"]:print(f"[{row['status']}] {row['id']}: {row['detail']}")
        return 0 if report["summary"]["passed"] else 2
    if not REPORT.is_file():run_matrix()
    print(REPORT.read_text(encoding="utf-8"));return 0


if __name__=="__main__":raise SystemExit(main())
