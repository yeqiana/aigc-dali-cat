#!/usr/bin/env python3
"""Story OS async task runtime.

A small execution layer shared by image production schedulers.
Workers execute external/model work, while callers receive events that can be
committed by a single ledger writer. This module intentionally does not own
Story stage state.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable


@dataclass
class TaskEvent:
    event: str
    task_id: str
    payload: dict[str, Any]


class AsyncTaskRuntime:
    def __init__(self, workers: int = 5):
        if workers < 1:
            raise ValueError("workers must be >= 1")
        self.workers = workers
        self.queue: asyncio.Queue[tuple[dict[str, Any], Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]]] = asyncio.Queue()
        self.events: asyncio.Queue[TaskEvent] = asyncio.Queue()
        self._running = False

    async def submit(self, task: dict[str, Any], handler: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]):
        await self.queue.put((task, handler))

    async def _worker(self, index: int):
        while self._running:
            try:
                task, handler = await asyncio.wait_for(self.queue.get(), timeout=0.2)
            except asyncio.TimeoutError:
                continue
            task_id = str(task.get("id") or index)
            started = time.time()
            try:
                result = await handler(task)
                await self.events.put(TaskEvent("TASK_SUCCESS", task_id, {
                    "result": result,
                    "elapsed_seconds": round(time.time() - started, 3),
                }))
            except Exception as exc:
                await self.events.put(TaskEvent("TASK_FAILED", task_id, {
                    "error": str(exc),
                    "elapsed_seconds": round(time.time() - started, 3),
                }))
            finally:
                self.queue.task_done()

    async def run(self, event_handler: Callable[[TaskEvent], Awaitable[None]] | None = None):
        self._running = True
        workers = [asyncio.create_task(self._worker(i + 1)) for i in range(self.workers)]
        try:
            while self._running or not self.events.empty():
                try:
                    event = await asyncio.wait_for(self.events.get(), timeout=0.2)
                except asyncio.TimeoutError:
                    continue
                if event_handler:
                    await event_handler(event)
                self.events.task_done()
        finally:
            self._running = False
            for worker in workers:
                worker.cancel()

    async def stop(self):
        self._running = False
        await self.queue.join()
        await self.events.join()


async def self_test() -> None:
    runtime = AsyncTaskRuntime(workers=5)
    completed = []

    async def handler(task):
        if task["id"] == "03":
            raise RuntimeError("mock timeout")
        return {"ok": True}

    async def consume(event):
        completed.append(event)

    runner = asyncio.create_task(runtime.run(consume))
    for i in range(1, 21):
        await runtime.submit({"id": f"{i:02d}"}, handler)
    await runtime.queue.join()
    await asyncio.sleep(0.1)
    await runtime.stop()
    runner.cancel()
    assert len(completed) == 20


if __name__ == "__main__":
    asyncio.run(self_test())
    print("ASYNC TASK RUNTIME SELF-TEST PASS")
