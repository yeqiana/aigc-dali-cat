#!/usr/bin/env python3
"""Story OS V2.7 async runtime failure injection harness.

Validates failure isolation, retry recovery and effective status semantics
without touching real episode production assets.
"""
from __future__ import annotations

import asyncio
import random

from async_task_runtime import AsyncTaskRuntime


async def run_mock():
    runtime = AsyncTaskRuntime(workers=5)
    events = []
    attempts = {}
    random.seed(27)

    async def handler(task):
        frame = task["id"]
        attempts[frame] = attempts.get(frame, 0) + 1
        # deterministic failure injection: first attempt of selected frames fails
        if attempts[frame] == 1 and frame in {"03", "08", "14", "19", "20", "02"}:
            raise RuntimeError("mock timeout")
        return {"frame": frame, "status": "SUCCESS"}

    async def consume(event):
        events.append(event)

    runner = asyncio.create_task(runtime.run(consume))

    for i in range(1, 21):
        await runtime.submit({"id": f"{i:02d}"}, handler)

    await runtime.queue.join()
    await asyncio.sleep(0.1)

    failed = [e for e in events if e.event == "TASK_FAILED"]
    assert len(events) == 20
    assert len(failed) == 6

    # retry failed frames
    for event in failed:
        await runtime.submit({"id": event.task_id}, handler)

    await runtime.queue.join()
    await asyncio.sleep(0.1)
    await runtime.stop()
    runner.cancel()

    success = [e for e in events if e.event == "TASK_SUCCESS"]
    assert len(success) == 20
    assert all(attempts[f"{i:02d}"] >= 1 for i in range(1, 21))


if __name__ == "__main__":
    asyncio.run(run_mock())
    print("V2.7 ASYNC FAILURE INJECTION HARNESS PASS")
