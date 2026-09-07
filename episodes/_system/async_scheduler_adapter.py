#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Streaming adapter for Story OS async runtime.

The adapter owns task execution events only. Scheduler remains the single
writer for ledger/state.
"""
from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, AsyncIterator

from async_task_runtime import AsyncTaskRuntime, TaskEvent


async def stream_tasks(
    tasks: list[dict[str, Any]],
    handler: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
    workers: int = 5,
) -> AsyncIterator[TaskEvent]:
    if not tasks:
        return
    runtime = AsyncTaskRuntime(workers=workers)
    events: asyncio.Queue[TaskEvent] = asyncio.Queue()

    async def consume(event: TaskEvent) -> None:
        await events.put(event)

    runner = asyncio.create_task(runtime.run(consume))
    for task in tasks:
        await runtime.submit(task, handler)

    remaining = len(tasks)
    try:
        while remaining:
            event = await events.get()
            remaining -= 1
            yield event
            events.task_done()
    finally:
        await runtime.queue.join()
        await runtime.stop()
        runner.cancel()
        await asyncio.gather(runner, return_exceptions=True)


async def run_tasks(
    tasks: list[dict[str, Any]],
    handler: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
    workers: int = 5,
) -> list[TaskEvent]:
    result = []
    async for event in stream_tasks(tasks, handler, workers):
        result.append(event)
    return result


def self_test() -> None:
    async def handler(task: dict[str, Any]) -> dict[str, Any]:
        if task["id"] == "03":
            raise RuntimeError("mock timeout")
        return {"task": task["id"]}

    async def main() -> None:
        events = [x async for x in stream_tasks([{"id": f"{i:02d}"} for i in range(1, 21)], handler, workers=5)]
        assert len(events) == 20
        assert any(x.event == "TASK_FAILED" for x in events)
        assert any(x.event == "TASK_SUCCESS" for x in events)

    asyncio.run(main())


if __name__ == "__main__":
    self_test()
    print("ASYNC SCHEDULER ADAPTER STREAM SELF-TEST PASS")
