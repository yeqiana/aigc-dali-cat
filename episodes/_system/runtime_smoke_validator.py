#!/usr/bin/env python3
"""Reject legacy constant PASS reports as runtime acceptance evidence."""
import json
from pathlib import Path


def validate(report):
    checks={
        "schema":report.get("schema_version")==2,
        "non_authority":report.get("classification")=="NON_AUTHORITY_TEST_ONLY",
        "executed":isinstance(report.get("tests_run"),int) and report["tests_run"]>0,
        "failures":report.get("failures")==0,
        "errors":report.get("errors")==0,
        "skipped":report.get("skipped")==0,
        "test_output":bool(report.get("output")),
        "no_real_image_claim":report.get("real_image_generation_verified") is False,
        "result":report.get("result")=="PASS",
    }
    return {"checks":checks,"result":"PASS" if all(checks.values()) else "FAIL"}


if __name__=="__main__":
    import sys
    result=validate(json.loads(Path(sys.argv[1] if len(sys.argv)>1 else "runtime-smoke-report.json").read_text(encoding="utf-8-sig")))
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result["result"]=="PASS" else 1)
