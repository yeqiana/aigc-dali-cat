"""Synthetic performance baseline for bounded MySQL JSON projections.

This script is read-only: it does not connect to MySQL, Redis, or the
Runtime Workspace. It measures projection CPU cost and output size only.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
import tracemalloc
from typing import Callable

from platform.repository.mysql.payload_policy import (
    approval_projection,
    document_reference,
    metric_snapshot_projection,
    payload_bytes,
    prompt_package_projection,
    release_projection,
    runtime_review_projection,
)


def _cases() -> list[tuple[str, Callable[[dict, dict], dict], dict]]:
    return [
        (
            "prompt_package",
            prompt_package_projection,
            {"frame": "01", "scene_prompt": "x" * 4096, "source_prompt": "中文🙂" * 512},
        ),
        (
            "runtime_review",
            runtime_review_projection,
            {"request_id": "req", "prompt": "x" * 4096, "source_files": [f"f-{i}.json" for i in range(20)]},
        ),
        (
            "metric_snapshot",
            metric_snapshot_projection,
            {"final_status": "PASS", "execution_sessions": [{"raw": "x" * 4096}], "summary": {"count": 20}},
        ),
        (
            "approval",
            approval_projection,
            {"approvals": {f"a-{i}": {"approved": i % 2 == 0} for i in range(20)}},
        ),
        (
            "release",
            release_projection,
            {"files": [f"release/{i:03d}.png" for i in range(50)], "direct_release_lock": True},
        ),
    ]


def _run(count: int, name: str, projector: Callable[[dict, dict], dict], base: dict) -> dict:
    timings_ns: list[int] = []
    output_bytes = 0
    reference = document_reference(base, f"meta/runtime/perf/{name}.json")
    tracemalloc.start()
    started = time.perf_counter_ns()
    for index in range(count):
        payload = dict(base)
        payload["iteration"] = index
        began = time.perf_counter_ns()
        projection = projector(payload, reference)
        timings_ns.append(time.perf_counter_ns() - began)
        output_bytes += payload_bytes(projection)
    elapsed_ns = time.perf_counter_ns() - started
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    p95_ns = statistics.quantiles(timings_ns, n=20, method="inclusive")[18] if count > 1 else timings_ns[0]
    return {
        "count": count,
        "projector": name,
        "elapsed_ms": round(elapsed_ns / 1_000_000, 3),
        "ops_per_sec": round(count * 1_000_000_000 / elapsed_ns, 2),
        "p95_us": round(p95_ns / 1_000, 3),
        "avg_output_bytes": round(output_bytes / count, 2),
        "peak_tracemalloc_bytes": peak_bytes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counts", nargs="+", type=int, default=[2000, 10000, 100000])
    args = parser.parse_args()
    results = []
    for count in args.counts:
        if count <= 0:
            parser.error("counts must be positive")
        for name, projector, payload in _cases():
            results.append(_run(count, name, projector, payload))
    print(json.dumps({"read_only": True, "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
