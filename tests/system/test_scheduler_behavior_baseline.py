"""Deterministic execution baseline for B1; no provider or production writes."""
import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'episodes/_system'))
import async_scheduler_adapter


class SchedulerBehaviorBaseline(unittest.IsolatedAsyncioTestCase):
    async def test_first_completion_refills_within_submitted_batch(self):
        release_slow = asyncio.Event()
        third_started = asyncio.Event()
        active = 0
        peak = 0
        calls = []

        async def handler(row):
            nonlocal active, peak
            calls.append(row['id'])
            active += 1
            peak = max(peak, active)
            try:
                if row['id'] == 'slow':
                    await release_slow.wait()
                elif row['id'] == 'third':
                    third_started.set()
                return {'output': row['id']}
            finally:
                active -= 1

        async def consume():
            return [event async for event in async_scheduler_adapter.stream_tasks(
                [{'id': x} for x in ('slow', 'fast', 'third')], handler, workers=2)]

        task = asyncio.create_task(consume())
        try:
            await asyncio.wait_for(third_started.wait(), 3)
            self.assertFalse(task.done())
            self.assertLessEqual(peak, 2)
        finally:
            release_slow.set()
            events = await asyncio.wait_for(task, 3)
        self.assertEqual(len(events), 3)
        self.assertEqual(len(set(calls)), 3)
        self.assertEqual(events[-1].task_id, 'slow')

    async def test_failed_task_does_not_prevent_remaining_tasks(self):
        calls = []

        async def handler(row):
            calls.append(row['id'])
            if row['id'] == 'bad':
                raise RuntimeError('injected transport error')
            return {'output': row['id']}

        async def consume():
            return [event async for event in async_scheduler_adapter.stream_tasks(
                [{'id': x} for x in ('bad', 'good', 'next')], handler, workers=1)]

        events = await asyncio.wait_for(consume(), 3)
        self.assertEqual(calls, ['bad', 'good', 'next'])
        self.assertEqual([x.event for x in events],
                         ['TASK_FAILED', 'TASK_SUCCESS', 'TASK_SUCCESS'])


if __name__ == '__main__':
    unittest.main()
