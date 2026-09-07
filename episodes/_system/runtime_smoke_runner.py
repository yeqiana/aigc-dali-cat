#!/usr/bin/env python3
"""Execute isolated recovery regressions and report observed results only."""
import io
from pathlib import Path
import time
import unittest
from runtime_atomic_store import atomic_write_json

ROOT = Path(__file__).resolve().parents[2]
REPORT = Path("runtime-smoke-report.json")


def run_smoke(output=REPORT):
    suite=unittest.defaultTestLoader.discover(str(ROOT / "tests/system"),pattern="test_runtime_recovery.py")
    stream=io.StringIO()
    started=time.monotonic()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    report={"schema_version":2,"classification":"NON_AUTHORITY_TEST_ONLY",
            "scope":"real coordinator and scheduler; mocked image backend; isolated temporary episodes",
            "tests_run":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),
            "skipped":len(result.skipped),"elapsed_seconds":round(time.monotonic()-started,3),
            "result":"PASS" if result.testsRun>0 and result.wasSuccessful() and not result.skipped else "FAIL",
            "output":stream.getvalue(),"real_image_generation_verified":False}
    atomic_write_json(Path(output),report)
    return report


def self_test():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        report=run_smoke(Path(td)/"report.json")
        assert report["result"]=="PASS", report["output"]


if __name__=="__main__": self_test()
