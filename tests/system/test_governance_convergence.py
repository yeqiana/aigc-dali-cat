"""Governance acceptance through both scheduler entrypoints, no image service."""
import argparse
import asyncio
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'episodes/_system'))
import image_scheduler
import batch_scheduler
import scheduler_core
import raw_candidate_budget as budget
import prompt_package
import production_batch_review as batch_review
import frame_semantic_review as semantic
import incremental_frame_review as incr
import product_review_adapter as product_review
import batch_prompt_compiler
import openai_batch_prompt_compiler
import golden_episode_regression as golden
import codex_subscription_image as single_backend
import batch_image_worker as batch_delivery
from test_repair_concurrency_lane import make_episode


class EntryBehavior(unittest.TestCase):
    def exercise(self, lane, failures=()):
        td, ep = make_episode([{'frame': i} for i in range(1, 7)])
        self.addCleanup(td.cleanup)
        q = scheduler_core.load_queue(ep)
        q['adaptive_parallel'] = 1  # historical value must not throttle restart
        for row in q['items']:
            row.update(scope='batch' if lane is batch_scheduler else 'repair')
        scheduler_core.save_queue(ep, q)
        active = peak = 0
        starts, ends, scouts = {}, {}, []
        ordering = []
        lock = threading.Lock()
        slow_release = threading.Event()

        def worker(_ep, row, *_args):
            nonlocal active, peak
            f = row['frame']
            with lock:
                active += 1; peak = max(peak, active); starts[f] = time.monotonic()
                ordering.append(('start', f))
            try:
                if f == 1:
                    if failures:
                        time.sleep(.05)
                    elif not slow_release.wait(3):
                        raise AssertionError('no first-completed refill')
                elif f == 4:
                    slow_release.set()
                else:
                    time.sleep(.02 * f)
                if f in failures:
                    raise RuntimeError('network failure')
                out = ep / f'{f}.png'; out.write_bytes(b'mock')
                return {'returncode': 0, 'output': str(out), 'payload': {}}
            finally:
                with lock:
                    active -= 1; ends[f] = time.monotonic()
                    ordering.append(('end', f))

        async def async_worker(*args):
            return await asyncio.to_thread(worker, *args)

        def scout(*args, **kwargs):
            scouts.append(len(ends))
            return {'decision': 'UNCERTAIN'}

        with ExitStack() as stack:
            for name, replacement in (
                ('ledger_begin', lambda *a: (True, '')),
                ('ledger_success', lambda *a: (True, '')),
                ('ledger_tech_fail', lambda *a: None),
            ):
                stack.enter_context(patch.object(lane, name, replacement))
            stack.enter_context(patch.object(lane.resource_library, 'ensure_fresh', lambda *a: None))
            stack.enter_context(patch.object(lane.runtime_router, 'detect', lambda: ('CODEX', 'test')))
            stack.enter_context(patch.object(lane.runtime_router, 'image_execution_runtime', lambda: ('CODEX', 'test')))
            if lane is image_scheduler:
                stack.enter_context(patch.object(lane, 'async_backend_worker', async_worker))
                rc = lane.run_scheduler_async(ep, 3, 30, None)
            else:
                stack.enter_context(patch.object(lane, 'verified_image_lane', lambda *a: True))
                stack.enter_context(patch.object(lane, 'ensure_image_capability', lambda *a, **k: True))
                stack.enter_context(patch.object(lane.image_provider_runtime, 'select_batch_provider', lambda *a: {'provider': 'codex_subscription'}))
                stack.enter_context(patch.object(lane.image_worker_pool, 'execute', worker))
                stack.enter_context(patch.object(lane.batch_capability_probe, 'record', lambda *a, **k: None))
                stack.enter_context(patch.object(lane.frame_scout, 'required', lambda *a: True))
                stack.enter_context(patch.object(lane.frame_scout, 'evaluate_candidate', scout))
                stack.enter_context(patch.object(lane.batch_repair_arbiter, 'assess', lambda *a, **k: {'action': 'NONE'}))
                rc = lane.run(ep, 3, 30, None)
                # Six inputs traverse two legal logical batches (5 + 1).
                first = len(ends)
                self.assertEqual(first, 5)
                self.assertTrue(all(x == 5 for x in scouts))
                lane.run(ep, 3, 30, None)
        q = scheduler_core.load_queue(ep)
        self.assertEqual(peak, 3)
        self.assertEqual(len(starts), 6)
        self.assertTrue(all(x['attempts'] == 1 for x in q['items']))
        if not failures:
            self.assertEqual(rc, 0)
            self.assertLess(ordering.index(('start', 4)), ordering.index(('end', 1)))
        else:
            caps = [w['next_parallel'] for w in q['waves']]
            self.assertIn(2, caps); self.assertIn(1, caps)
        return q

    def test_image_entry_refills_six(self):
        self.exercise(image_scheduler)

    def test_batch_entry_refills_and_preserves_barrier(self):
        self.exercise(batch_scheduler)

    def test_both_entries_degrade_without_repeating_success(self):
        for lane in (image_scheduler, batch_scheduler):
            with self.subTest(lane=lane.__name__):
                self.exercise(lane, failures=(1, 2))


class BudgetResolution(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ep = Path(self.tmp.name)

    def override(self, value):
        budget.story_json.write_json(self.ep / budget.OVERRIDE_REL, value)

    def test_unauthorized_and_boolean_overrides_do_not_raise(self):
        for value in ({'max_total_content_candidates': 44},
                      {'max_total_content_candidates': 44, 'authorized_by': True},
                      {'max_total_content_candidates': 44, 'authorization': {'approved': True}},
                      {'max_total_content_candidates': True, 'authorized_by': 'user decision'}):
            self.override(value)
            self.assertEqual(budget.episode_limit(self.ep), 35)

    def test_legacy_authorization_and_fixed_precedence_survive_restart(self):
        self.override({'max_total_content_candidates': 44, 'authorized_by': 'recorded user decision'})
        self.assertEqual(budget.episode_limit(self.ep), 44)
        self.assertEqual(budget.resolve_limit(self.ep)['source'], budget.OVERRIDE_REL.as_posix())
        cfg = self.ep / 'config.json'
        budget.story_json.write_json(cfg, {'episode_candidate_budget': {'max_total_content_candidates': 30}})
        with patch.object(budget, 'CFG', cfg):
            self.assertEqual(budget.episode_limit(self.ep), 30)

    def test_concurrent_claim_commit_release_accounting(self):
        cfg = self.ep / 'config.json'
        budget.story_json.write_json(cfg, {'episode_candidate_budget': {'max_total_content_candidates': 3}})
        results = []
        with patch.object(budget, 'CFG', cfg):
            threads = [threading.Thread(target=lambda i=i: results.append(budget.claim(self.ep, i+1, 'original', token=str(i)))) for i in range(10)]
            for t in threads: t.start()
            for t in threads: t.join()
            allowed = [row['token'] for ok, row in results if ok]
            self.assertEqual(len(allowed), 3)
            budget.commit(self.ep, allowed[0]); budget.commit(self.ep, allowed[0])
            budget.release(self.ep, allowed[1])
            summary = budget.summary(self.ep, pending=4)
            self.assertEqual((summary['committed'], summary['inflight_reserved'], summary['available']), (1, 1, 1))


class EvidenceRecovery(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT, prefix='evidence-test-')
        self.addCleanup(self.tmp.cleanup)
        self.ep = Path(self.tmp.name)

    def test_old_prompt_new_contract_rejected_without_rebinding_package(self):
        prompt = self.ep / 'prompt.txt'; prompt.write_text('old scene', encoding='utf-8')
        with patch.object(prompt_package.frame_contract, 'compile_frame', return_value={'contract_sha256': 'old'}), patch.object(prompt_package.image_model_policy, 'for_episode', return_value={}):
            prompt_package.compile_frame(self.ep, 1, prompt)
        path = self.ep / prompt_package.REL / '01.json'
        before = path.read_bytes()
        with patch.object(prompt_package.frame_contract, 'compile_frame', return_value={'contract_sha256': 'new'}), patch.object(prompt_package.image_model_policy, 'for_episode', return_value={}):
            with self.assertRaisesRegex(ValueError, 'PROMPT_SOURCE_DRIFT'):
                prompt_package.compile_frame(self.ep, 1, prompt)
        self.assertEqual(path.read_bytes(), before)

    def test_review_units_reuse_and_each_sha_invalidates(self):
        out = self.ep / 'candidate.png'; out.write_bytes(b'candidate')
        row = {'frame': 1, 'output_path': out.relative_to(ROOT).as_posix(), 'batch_id': 'B1'}
        scheduler_core.write_json(self.ep / batch_review.QUEUE_REL, {'items': [row]})
        with patch.object(batch_review.frame_contract, 'compile_frame', return_value={'contract_sha256': 'contract'}):
            unit = {'frame': '01', **batch_review.unit_binding(self.ep, row), 'checks': {'whole_image': 'pass'}, 'decision': 'PASS_PREVIEW', 'unresolved': []}
            batch_review.record_unit(self.ep, 'B1', unit)
            self.assertEqual(batch_review.reusable_units(self.ep, 'B1', [row]), [unit])
            out.write_bytes(b'changed')
            self.assertEqual(batch_review.reusable_units(self.ep, 'B1', [row]), [])
            out.write_bytes(b'candidate')
            with self.assertRaisesRegex(ValueError, 'UNCERTAIN'):
                batch_review.record_unit(self.ep, 'B1', {**unit, 'unresolved': ['hand unclear']})
        with patch.object(batch_review.frame_contract, 'compile_frame', return_value={'contract_sha256': 'changed'}):
            self.assertEqual(batch_review.reusable_units(self.ep, 'B1', [row]), [])
            with self.assertRaisesRegex(ValueError, 'SHA drift'):
                batch_review.record_unit(self.ep, 'B1', unit)
        self.assertFalse((self.ep / 'meta/production-ledger.json').exists())

    def test_finalized_batch_review_units_are_reused_and_sha_drift_invalidates(self):
        out = self.ep / 'final.png'; out.write_bytes(b'final-bytes')
        row = {'frame': 1, 'output_path': out.relative_to(ROOT).as_posix(), 'batch_id': 'FIN1'}
        scheduler_core.write_json(self.ep / batch_review.QUEUE_REL, {'items': [row]})
        with patch.object(batch_review.frame_contract, 'compile_frame', return_value={'contract_sha256': 'contract'}):
            unit = {'frame': '01', **batch_review.unit_binding(self.ep, row), 'checks': {'whole_image': 'pass'}, 'decision': 'PASS_PREVIEW', 'unresolved': []}
            final = {'schema_version': 1, 'batch_id': 'FIN1', 'review_scope': 'EARLY_BATCH_ACTUAL_PIXELS', 'final_pass_authority': False, 'frames': [unit]}
            batch_review.write_json(batch_review.final_path(self.ep, 'FIN1'), final)
            self.assertEqual(batch_review.reusable_units(self.ep, 'FIN1', [row]), [unit])
            out.write_bytes(b'changed-final-bytes')
            self.assertEqual(batch_review.reusable_units(self.ep, 'FIN1', [row]), [])
            out.write_bytes(b'final-bytes')
        with patch.object(batch_review.frame_contract, 'compile_frame', return_value={'contract_sha256': 'contract'}):
            bound = batch_review.unit_binding(self.ep, row)
        stale = dict(unit)
        stale['candidate_sha256'] = 'changed'
        batch_review.write_json(batch_review.final_path(self.ep, 'FIN1'), {'batch_id': 'FIN1', 'frames': [stale]})
        with patch.object(batch_review.frame_contract, 'compile_frame', return_value={'contract_sha256': 'contract'}):
            self.assertEqual(batch_review.reusable_units(self.ep, 'FIN1', [row]), [])
        # The old unit must not be returned for a different current SHA.
        self.assertNotEqual(stale['candidate_sha256'], bound['candidate_sha256'])

    def test_finalized_unresolved_history_cannot_pass_preview(self):
        out = self.ep / 'candidate.png'; out.write_bytes(b'candidate')
        row = {'frame': 1, 'output_path': out.relative_to(ROOT).as_posix(), 'batch_id': 'UNFIN1'}
        scheduler_core.write_json(self.ep / batch_review.QUEUE_REL, {'items': [row]})
        with patch.object(batch_review.frame_contract, 'compile_frame', return_value={'contract_sha256': 'contract'}):
            unit = {'frame': '01', **batch_review.unit_binding(self.ep, row), 'checks': {'whole_image': 'pass'}, 'decision': 'PASS_PREVIEW', 'unresolved': ['hand unclear']}
            batch_review.write_json(batch_review.final_path(self.ep, 'UNFIN1'), {'batch_id': 'UNFIN1', 'frames': [unit]})
            self.assertEqual(batch_review.reusable_units(self.ep, 'UNFIN1', [row]), [])
            with self.assertRaisesRegex(ValueError, 'UNCERTAIN'):
                batch_review.record_unit(self.ep, 'UNFIN1', unit)

    def test_finalized_and_candidate_review_history_merge_by_frame(self):
        first = self.ep / 'first.png'; first.write_bytes(b'first-bytes')
        second = self.ep / 'second.png'; second.write_bytes(b'second-bytes')
        rows = [
            {'frame': 1, 'output_path': first.relative_to(ROOT).as_posix(), 'batch_id': 'MERGE1'},
            {'frame': 2, 'output_path': second.relative_to(ROOT).as_posix(), 'batch_id': 'MERGE1'},
        ]
        scheduler_core.write_json(self.ep / batch_review.QUEUE_REL, {'items': rows})
        with patch.object(batch_review.frame_contract, 'compile_frame', return_value={'contract_sha256': 'contract'}):
            formal = {'frame': '01', **batch_review.unit_binding(self.ep, rows[0]), 'checks': {'whole_image': 'pass'}, 'decision': 'PASS_PREVIEW', 'unresolved': []}
            batch_review.write_json(batch_review.final_path(self.ep, 'MERGE1'), {'batch_id': 'MERGE1', 'frames': [formal]})
            candidate_unit = {'frame': '02', **batch_review.unit_binding(self.ep, rows[1]), 'checks': {'whole_image': 'pass'}, 'decision': 'PASS_PREVIEW', 'unresolved': []}
            batch_review.write_json(batch_review.candidate_path(self.ep, 'MERGE1'), {'batch_id': 'MERGE1', 'frames': [candidate_unit]})
            merged = batch_review.reusable_units(self.ep, 'MERGE1', rows)
            self.assertEqual({str(u.get('frame')).zfill(2) for u in merged}, {'01', '02'})

    def test_source_binding_change_invalidates_frame_review(self):
        out = self.ep / 'source.png'; out.write_bytes(b'source-pixels')
        frame = {'frame': '01', 'path_rel': out.relative_to(ROOT).as_posix(), 'sha256': 'a' * 64, 'path': out}
        binding = {'story': {'path': 'story.md', 'sha256': 'b' * 64}, 'storyboard': {'path': 'board.md', 'sha256': 'c' * 64}, 'extraction_mode': 'text_frame', 'frame_sha256': 'd' * 64}
        payload = {
            'schema_version': semantic.SCHEMA_VERSION,
            'story_os_version': '2.0.3.6',
            'frame': '01',
            'asset_path': frame['path_rel'],
            'asset_sha256': frame['sha256'],
            'critic_provenance': {'runtime': 'CODEX_ISOLATED', 'isolated_session': True, 'review_scope': 'FULL_FRAME_SET', 'attempt': 1},
            'checks': {key: True for key in semantic.checks_for_version('2.0.3.6')},
            'issue_codes': [],
            'decision': 'pass',
            'source_binding': binding,
        }
        with patch.object(semantic, 'review_required', return_value=True), patch.object(semantic, 'episode_contract_version', return_value='2.0.3.6'), patch.object(semantic.phase4_contract, 'required', return_value=True), patch.object(semantic.phase4_contract, 'source_binding', return_value=binding), patch.object(semantic.phase3_env, 'required', return_value=False), patch.object(semantic.phase4_contract, 'verify_approved_asset_binding', return_value=[]):
            self.assertEqual(semantic.validate_bound_review(payload, frame=frame, contexts={}, version='2.0.3.6', metadata_only=True, ep=self.ep), [])
            changed_binding = {'story': dict(binding['story']), 'storyboard': dict(binding['storyboard']), 'extraction_mode': binding['extraction_mode'], 'frame_sha256': binding['frame_sha256']}
            changed_binding['storyboard']['sha256'] = 'e' * 64
            semantic.phase4_contract.source_binding.return_value = changed_binding
            errors = semantic.validate_bound_review(payload, frame=frame, contexts={}, version='2.0.3.6', metadata_only=True, ep=self.ep)
            self.assertTrue(any('source_binding' in x for x in errors))

    def test_incremental_noop_patch_full_and_unreadable_contract(self):
        frames = []
        binding = {'storyboard': {'sha256': 'b' * 64}}
        for n in range(1, 9):
            out = self.ep / f'{n:02d}.png'; out.write_bytes(f'pixels {n}'.encode())
            frame = {'frame': f'{n:02d}', 'path_rel': out.relative_to(ROOT).as_posix(),
                     'sha256': semantic.sha256_file(out), 'path': out}
            frames.append(frame)
            scheduler_core.write_json(self.ep / semantic.REVIEW_DIR / f'{n:02d}.json', {
                'schema_version': semantic.SCHEMA_VERSION, 'story_os_version': '2.0.3.6',
                'frame': frame['frame'], 'asset_path': frame['path_rel'], 'asset_sha256': frame['sha256'],
                'critic_provenance': {'runtime': 'CODEX_ISOLATED', 'isolated_session': True,
                                     'review_scope': 'FULL_FRAME_SET', 'attempt': 1},
                'source_binding': binding, 'frame_contract_sha256': 'contract',
                'checks': {key: True for key in semantic.checks_for_version('2.0.3.6')},
                'issue_codes': [], 'decision': 'pass',
            })
        with ExitStack() as stack:
            for module, name, value in (
                (incr, 'review_required', True), (semantic, 'frame_records', frames),
                (semantic, 'context_hashes', {}), (semantic, 'episode_contract_version', '2.0.3.6'),
                (semantic, 'directing_v3_required', False),
                (incr, 'caption_state', {'mode': 'none', 'frame_sha256': {f['frame']: '' for f in frames}}),
            ):
                stack.enter_context(patch.object(module, name, return_value=value))
            source = stack.enter_context(patch.object(semantic, 'source_binding', return_value=binding))
            contract = stack.enter_context(patch.object(semantic, 'phase3_context_hashes', return_value={'frame_contract_sha256': 'contract'}))
            self.assertEqual(incr.build_plan(self.ep)['action'], 'NOOP')
            review_path = self.ep / semantic.REVIEW_DIR / '01.json'
            original = batch_review.read_json(review_path)
            batch_review.write_json(review_path, {**original, 'asset_sha256': 'dirty'})
            plan = incr.build_plan(self.ep)
            self.assertEqual((plan['action'], plan['dirty_frames'], plan['context_frames']), ('PATCH', ['01'], ['01', '02']))
            batch_review.write_json(review_path, original)
            source.side_effect = lambda ep, frame: {'storyboard': {'sha256': 'new'}} if frame == '01' else binding
            plan = incr.build_plan(self.ep)
            self.assertEqual(plan['action'], 'FULL')
            self.assertEqual(plan['dirty_ratio'], 0.125)  # Below threshold; source drift must escalate by itself.
            self.assertIn('story_source_binding_changed', plan['reasons']['01'])
            source.side_effect = None
            contract.side_effect = FileNotFoundError('locked Frame Contract missing')
            with self.assertRaisesRegex(FileNotFoundError, 'Contract missing'):
                incr.build_plan(self.ep)

    def batch_fixture(self, batch_id='RESUME'):
        out = self.ep / f'{batch_id}.png'; out.write_bytes(b'candidate')
        row = {'id': batch_id, 'frame': 1, 'status': 'generated',
               'output_path': out.relative_to(ROOT).as_posix(), 'batch_id': batch_id}
        batch_review.write_json(self.ep / batch_review.QUEUE_REL, {'items': [row]})
        return row

    def test_batch_prepare_resume_finalize_preserves_request_and_authority(self):
        for runtime in ('WORK', 'WEB'):
            with self.subTest(runtime=runtime), patch.object(batch_review.runtime_router, 'detect', return_value=(runtime, 'test')), patch.object(
                    batch_review.frame_contract, 'compile_frame', return_value={'contract_sha256': 'contract', 'prompt_contract': 'locked scene'}):
                row = self.batch_fixture(runtime)
                first = batch_review.prepare(self.ep, runtime)
                request_path = ROOT / first['request_path']
                frozen = request_path.read_bytes()
                unit = {'frame': '01', **batch_review.unit_binding(self.ep, row), 'checks': {'whole_image': 'pass', 'key_regions': 'pass'},
                        'decision': 'PASS_PREVIEW', 'unresolved': [], 'issue_codes': []}
                batch_review.record_unit(self.ep, runtime, unit)
                resumed = batch_review.prepare(self.ep, runtime)
                self.assertEqual(resumed['request_id'], first['request_id'])
                self.assertEqual(request_path.read_bytes(), frozen)
                self.assertEqual(resumed['reusable_units'], [unit])
                self.assertEqual(resumed['pending_frames'], [])
                candidate = batch_review.candidate_path(self.ep, runtime)
                data = batch_review.read_json(candidate)
                batch_review.write_json(candidate, {**data, 'final_pass_authority': True,
                    'critic_provenance': {'runtime': 'forged'}, 'review_scope': 'FULL_FRAME_SET'})
                with patch.object(batch_review, '_ledger_review') as ledger:
                    final = batch_review.finalize(self.ep, runtime, runtime=runtime)
                    ledger.assert_not_called()
                self.assertIs(final['final_pass_authority'], False)
                self.assertEqual(final['review_scope'], 'EARLY_BATCH_ACTUAL_PIXELS')
                self.assertEqual(final['critic_provenance']['runtime'], runtime + '_ISOLATED')
                self.assertEqual(batch_review.reusable_units(self.ep, runtime, [row]), [unit])
                queue = self.ep / batch_review.QUEUE_REL
                before = queue.read_bytes()
                self.assertEqual(batch_review.prepare(self.ep, runtime)['status'], 'FINALIZED')
                self.assertEqual(queue.read_bytes(), before)

    def test_batch_finalization_rejects_missing_fields_duplicates_and_invalid_checks(self):
        row = self.batch_fixture()
        with patch.object(batch_review.runtime_router, 'detect', return_value=('WORK', 'test')), patch.object(
                batch_review.frame_contract, 'compile_frame', return_value={'contract_sha256': 'contract', 'prompt_contract': 'locked scene'}):
            batch_review.prepare(self.ep, 'RESUME')
            unit = {'frame': '01', **batch_review.unit_binding(self.ep, row), 'checks': {'whole_image': 'pass'},
                    'decision': 'PASS_PREVIEW', 'unresolved': [], 'issue_codes': []}
            invalid = [[{k: v for k, v in unit.items() if k != field}] for field in ('candidate_sha256', 'frame_contract_sha256', 'checks', 'unresolved')]
            invalid += [[unit, unit], [unit, None], [{**unit, 'checks': {'whole_image': 'fail'}}],
                        [{**unit, 'issue_codes': ['DEFECT']}], [{**unit, 'unresolved': ['unclear hand']}],
                        [{**unit, 'issue_codes': 'bad type'}]]
            queue = self.ep / batch_review.QUEUE_REL
            before = queue.read_bytes()
            with patch.object(batch_review, '_ledger_review') as ledger, patch.object(product_review, 'mark_complete') as complete:
                for frames in invalid:
                    batch_review.write_json(batch_review.candidate_path(self.ep, 'RESUME'), {'batch_id': 'RESUME', 'frames': frames})
                    with self.subTest(frames=frames), self.assertRaises(ValueError):
                        batch_review.finalize(self.ep, 'RESUME')
                    self.assertEqual(queue.read_bytes(), before)
                    self.assertFalse(batch_review.final_path(self.ep, 'RESUME').exists())
                ledger.assert_not_called(); complete.assert_not_called()

    def test_batch_pending_uncertain_or_invalid_cannot_reuse_older_pass(self):
        row = self.batch_fixture()
        with patch.object(batch_review.frame_contract, 'compile_frame', return_value={'contract_sha256': 'contract'}):
            unit = {'frame': '01', **batch_review.unit_binding(self.ep, row), 'checks': {'whole_image': 'pass'},
                    'decision': 'PASS_PREVIEW', 'unresolved': [], 'issue_codes': []}
            batch_review.write_json(batch_review.final_path(self.ep, 'RESUME'), {'batch_id': 'RESUME', 'frames': [unit]})
            uncertain = {**unit, 'decision': 'UNCERTAIN', 'unresolved': ['hand unclear']}
            batch_review.write_json(batch_review.candidate_path(self.ep, 'RESUME'), {'batch_id': 'RESUME', 'frames': [uncertain]})
            self.assertEqual(batch_review.reusable_units(self.ep, 'RESUME', [row]), [uncertain])
            for pending in ([{**unit, 'checks': {}}], [unit, unit], [None], [{**unit, 'candidate_sha256': 'stale'}]):
                batch_review.write_json(batch_review.candidate_path(self.ep, 'RESUME'), {'batch_id': 'RESUME', 'frames': pending})
                self.assertEqual(batch_review.reusable_units(self.ep, 'RESUME', [row]), [])

    def test_batch_contract_drift_cannot_rebind_current_candidate(self):
        row = self.batch_fixture()
        with patch.object(batch_review.runtime_router, 'detect', return_value=('WORK', 'test')), patch.object(
                batch_review.frame_contract, 'compile_frame', return_value={'contract_sha256': 'old', 'prompt_contract': 'old scene'}) as compiler:
            first = batch_review.prepare(self.ep, 'RESUME')
            frozen = (ROOT / first['request_path']).read_bytes()
            compiler.return_value = {'contract_sha256': 'new', 'prompt_contract': 'new scene'}
            unit = {'frame': '01', **batch_review.unit_binding(self.ep, row), 'checks': {'whole_image': 'pass'},
                    'decision': 'PASS_PREVIEW', 'unresolved': [], 'issue_codes': []}
            batch_review.write_json(batch_review.candidate_path(self.ep, 'RESUME'), {'batch_id': 'RESUME', 'frames': [unit]})
            with self.assertRaisesRegex(product_review.ProductReviewError, 'bindings'):
                batch_review.finalize(self.ep, 'RESUME')
            with self.assertRaisesRegex(product_review.ProductReviewError, 'different frozen inputs'):
                batch_review.prepare(self.ep, 'RESUME')
            self.assertEqual((ROOT / first['request_path']).read_bytes(), frozen)
            self.assertFalse(batch_review.final_path(self.ep, 'RESUME').exists())

    def test_formal_review_reuses_only_verified_summary(self):
        scheduler_core.write_json(self.ep / semantic.SUMMARY_REL, {})
        with patch.object(semantic, 'review_required', return_value=True), patch.object(semantic, 'verify_episode', return_value=[]), patch.object(semantic, 'frame_records') as frames:
            self.assertEqual(semantic.run_critic(self.ep, attempt=1, codex_raw=None), 0)
            frames.assert_not_called()
        with patch.object(semantic, 'review_required', return_value=True), patch.object(semantic, 'verify_episode', return_value=['drift']), patch.object(semantic, 'frame_records', side_effect=ValueError('new review required')):
            with self.assertRaisesRegex(ValueError, 'new review required'):
                semantic.run_critic(self.ep, attempt=1, codex_raw=None)

    def test_semantic_finalize_rejects_contract_drift_before_any_pass_is_written(self):
        out = self.ep / 'review.png'; out.write_bytes(b'pixels')
        story = self.ep / 'story.md'; story.write_text('story', encoding='utf-8')
        board = self.ep / 'storyboard.md'; board.write_text('board', encoding='utf-8')
        contract = self.ep / 'contract.json'; contract.write_text('first contract', encoding='utf-8')
        batch_review.write_json(self.ep / 'meta/story-gates.json', {})
        frames = [{'frame': '01', 'path_rel': out.relative_to(ROOT).as_posix(), 'path': out, 'sha256': semantic.sha256_file(out)}]
        with ExitStack() as stack:
            for name, value in (
                ('frame_records', frames), ('episode_files', (story, board)), ('episode_contract_version', '2.0.3.6'),
                ('stable_visual_contract', {}), ('source_binding', {}), ('phase4_binding_errors', []),
                ('perceptual_rows', []), ('directing_v3_required', False),
            ):
                stack.enter_context(patch.object(semantic, name, return_value=value))
            stack.enter_context(patch.object(semantic.runtime_router, 'detect', return_value=('WORK', 'test')))
            stack.enter_context(patch.object(semantic, 'phase3_context_hashes', side_effect=lambda *a: {'frame_contract_sha256': semantic.sha256_file(contract)}))
            # Prepare through the real entrypoint and the real immutable request adapter.
            with patch('builtins.print'):
                self.assertEqual(semantic.run_critic(self.ep, attempt=1, codex_raw=None), product_review.HOST_ACTION_REQUIRED_RC)
            candidate = self.ep / semantic.CANDIDATE_REL
            batch_review.write_json(candidate, {'frames': [], 'issue_codes': [], 'summary': {'passed': True}})
            before = candidate.read_bytes()
            with patch('builtins.print'):
                self.assertEqual(semantic.run_critic(self.ep, attempt=1, codex_raw=None), product_review.HOST_ACTION_REQUIRED_RC)
            self.assertEqual(candidate.read_bytes(), before)  # Resume must preserve work already written.
            contract.write_text('changed during review', encoding='utf-8')
            with self.assertRaisesRegex(product_review.ProductReviewError, 'bindings'):
                semantic.finalize_product_review(self.ep, attempt=1, runtime='WORK')
            self.assertEqual(candidate.read_bytes(), before)
            self.assertFalse((self.ep / semantic.SUMMARY_REL).exists())
            self.assertFalse((self.ep / semantic.REVIEW_DIR).exists())

    def test_semantic_self_test_entrypoint(self):
        with patch('builtins.print'):
            semantic.self_test()

    def test_both_batch_compilers_send_exact_package_and_block_cached_source_drift(self):
        visual = {'text': 'visual', 'profile_id': 'M00', 'profile_path': 'M00.json',
                  'profile_sha256': 'v', 'capture_profile': 'test'}
        for compiler in (batch_prompt_compiler, openai_batch_prompt_compiler):
            with self.subTest(compiler=compiler.__name__):
                path = self.ep / f'{compiler.__name__}.txt'; path.write_text('\ufeffcurrent scene', encoding='utf-8')
                batch = {'planned_count': 1, 'frames': [{'queue_item_id': 'Q1', 'frame': '01', 'output_index': 1}]}
                items = {'Q1': {'prompt_file': path.relative_to(ROOT).as_posix()}}
                kwargs = dict(model='gpt-image-2', quality='high', size='1088x1360', reference_names=[])
                with patch.object(compiler, 'compile_prompt_contract', return_value=visual), patch.object(
                        prompt_package.image_model_policy, 'for_episode', return_value={}), patch.object(
                        prompt_package.frame_contract, 'compile_frame', return_value={'contract_sha256': 'old', 'prompt_contract': 'locked contract'}) as resolved:
                    result = compiler.compile_batch(self.ep, batch, items, **kwargs)
                    resolved.assert_called_once()
                    self.assertIn('<scene>\ncurrent scene\n</scene>', result['text'])
                    self.assertIn('<frame_contract>\nlocked contract\n</frame_contract>', result['text'])
                    self.assertNotIn('\ufeff', result['text'])
                    package = self.ep / prompt_package.REL / '01.json'
                    before = package.read_bytes()
                    resolved.return_value = {'contract_sha256': 'new', 'prompt_contract': 'new contract'}
                    with self.assertRaisesRegex(ValueError, 'PROMPT_SOURCE_DRIFT'):
                        compiler.compile_batch(self.ep, batch, items, **kwargs)
                    self.assertEqual(package.read_bytes(), before)

    def test_native_prompt_limit_fails_without_truncating_contract(self):
        path = self.ep / 'long.txt'; path.write_text('scene', encoding='utf-8')
        batch = {'planned_count': 1, 'frames': [{'queue_item_id': 'Q1', 'frame': '01', 'output_index': 1}]}
        visual = {'text': '', 'profile_id': 'M00', 'profile_path': '', 'profile_sha256': '', 'capture_profile': ''}
        with patch.object(openai_batch_prompt_compiler, 'compile_prompt_contract', return_value=visual), patch.object(
                prompt_package.image_model_policy, 'for_episode', return_value={}), patch.object(
                prompt_package.frame_contract, 'compile_frame', return_value={'contract_sha256': 'long', 'prompt_contract': 'x' * 32001}):
            with self.assertRaisesRegex(ValueError, 'OPENAI_BATCH_PROMPT_TOO_LONG'):
                openai_batch_prompt_compiler.compile_batch(self.ep, batch, {'Q1': {'prompt_file': path.relative_to(ROOT).as_posix()}},
                    model='gpt-image-2', quality='high', size='1088x1360', reference_names=[])

    def test_empty_or_missing_metric_golden_is_not_pass(self):
        with patch.object(golden, 'REPORT', self.ep / 'report.json'), patch.object(golden, 'registry', return_value={'episodes': []}):
            self.assertFalse(golden.run_all()['passed'])
        sample = {'path': self.ep.relative_to(ROOT).as_posix(), 'baseline': {}}
        with patch.object(golden, 'REPORT', self.ep / 'report.json'), patch.object(golden, 'registry', return_value={'episodes': [sample]}), patch.object(golden, 'metrics', return_value={}):
            result = golden.run_all()
            self.assertFalse(result['passed'])
            self.assertEqual(len(result['results'][0]['errors']), 7)


class SourceProofEntries(unittest.TestCase):
    """S4 residual entries: admission freeze at dispatch and provider entry guards."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT, prefix='source-proof-')
        self.addCleanup(self.tmp.cleanup)
        self.ep = Path(self.tmp.name)
        (self.ep / 'meta').mkdir(parents=True, exist_ok=True)
        self.prompt = self.ep / 'prompt.txt'

    def snapshot(self, scene_text, contract_sha):
        return {'package_sha256': 'pkg',
                'scene_prompt_sha256': hashlib.sha256(scene_text.encode('utf-8')).hexdigest(),
                'frame_contract_sha256': contract_sha}

    def version_evidence(self):
        (self.ep / 'meta/episode-state.json').write_text(
            json.dumps({'tool_version': '2.1.0'}), encoding='utf-8')

    def begin(self, item, scene_text, contract_sha):
        # The scheduler recompiles at dispatch; the mocked package is the
        # dispatch-time truth compared with the admission snapshot.
        self.prompt.write_text(scene_text, encoding='utf-8')
        package = self.snapshot(scene_text, contract_sha)
        with patch.object(prompt_package, 'compile_frame', return_value=package), \
                patch('ledger_call.begin', return_value=(True, '')):
            return scheduler_core.ledger_begin(self.ep, item, notes='source-proof-test')

    def queue_item(self, scene_text, contract_sha, *, frozen=True):
        rel = self.prompt.relative_to(ROOT).as_posix()
        item = {'id': 'q1', 'frame': 1, 'kind': 'original', 'scope': 'batch',
                'prompt_file': rel, 'references': [], 'capture_id': 'c1',
                'model': 'gpt-image-2', 'quality': 'high',
                'frame_contract': {'contract_sha256': contract_sha}}
        if frozen:
            item['prompt_package'] = self.snapshot(scene_text, contract_sha)
        return item

    def test_dispatch_rejects_scene_change_since_admission_including_first_package_and_both_changed(self):
        self.version_evidence()  # V2.1+ rows carry the admission freeze check.
        first = self.queue_item('scene v0', 'C0')
        ok, msg = self.begin(first, 'scene v0', 'C0')
        self.assertTrue(ok)  # First package matches the admission snapshot exactly.
        ok, msg = self.begin(first, 'scene v1', 'C0')  # Scene edited after admission.
        self.assertFalse(ok)
        self.assertIn('scene prompt changed after admission', msg)
        self.assertIn('PROMPT_SOURCE_DRIFT', msg)
        # Scene AND contract changed: the queue-contract guard fires before the
        # scene freeze and still fails closed before any backend dispatch.
        ok, msg = self.begin(first, 'scene v2', 'C1')
        self.assertFalse(ok)
        self.assertIn('queue contract changed', msg)
        self.assertIn('PROMPT_SOURCE_DRIFT', msg)
        # Contract-only drift stays rejected through the queue-contract check.
        ok, msg = self.begin(first, 'scene v0', 'C9')
        self.assertFalse(ok)
        self.assertIn('queue contract changed', msg)
        # Legacy rows without an admission snapshot keep contract-only binding.
        legacy = self.queue_item('scene legacy', 'C0', frozen=False)
        ok, msg = self.begin(legacy, 'scene legacy edited', 'C0')
        self.assertTrue(ok)

    def test_single_image_backend_sends_frozen_package_scene_and_blocks_drift_before_invoke(self):
        self.prompt.write_text('file scene text', encoding='utf-8')
        self.version_evidence()  # Real V2.1 gate: drift raises before invoke.
        visual = {'text': 'visual', 'profile_id': 'M00', 'profile_path': 'm',
                  'profile_sha256': 'v', 'capture_profile': 'cp'}
        pkg = {'scene_prompt': 'PACKAGE SCENE ONLY', 'scene_prompt_sha256': 's',
               'frame_contract_sha256': 'c', 'frame_prompt_contract': 'LOCKED CONTRACT TEXT',
               'package_sha256': 'p'}
        policy = {'model': 'gpt-image-2', 'quality': 'high', 'strict_model': False}
        calls = []

        def fake_invoke(prompt_path, refs, raw_output, log, size, timeout, codex,
                        visual_contract, frame_contract_text, image_model, image_quality,
                        strict_model, *, scene_text=None):
            calls.append({'scene': scene_text, 'contract': frame_contract_text,
                          'model': image_model, 'quality': image_quality})
            return 1.2

        ns = argparse.Namespace(episode_dir=self.ep, frame='01', prompt_file=self.prompt,
                                output=self.ep / 'out.png', log=self.ep / 'worker.jsonl',
                                reference=[], timeout=60, codex=None, image_model=None,
                                image_quality=None, overwrite=False,
                                _image_model_policy=policy)
        with patch.object(single_backend, 'read_canvas', return_value=(1088, 1360, '4:5')), \
                patch.object(single_backend, 'compile_prompt_contract', return_value=visual), \
                patch.object(prompt_package, 'compile_frame', return_value=pkg), \
                patch.object(single_backend, 'invoke_codex', side_effect=fake_invoke), \
                patch.object(single_backend.provider_capability, 'inspect', return_value={}), \
                patch.object(single_backend.provider_capability, 'write_receipt',
                             return_value={'path': 'meta/provider-receipts/x.json'}), \
                patch.object(single_backend.provider_capability, 'finalize_receipt',
                             lambda *a, **k: {'path': 'x.json', 'receipt': {}}), \
                patch.object(single_backend, 'normalize', return_value={'ok': True}):
            result = single_backend.generate_for_frame(ns)
        self.assertEqual(calls[0]['scene'], pkg['scene_prompt'])
        self.assertEqual(calls[0]['contract'], pkg['frame_prompt_contract'])
        self.assertEqual((calls[0]['model'], calls[0]['quality']), ('gpt-image-2', 'high'))
        self.assertEqual(result['frame_contract']['contract_sha256'], 'c')
        # The file was never read for the sent scene; the package is the source.
        self.assertNotEqual(pkg['scene_prompt'], 'file scene text')
        with patch.object(prompt_package, 'compile_frame',
                          side_effect=ValueError('PROMPT_SOURCE_DRIFT: unchanged scene prompt belongs to an older Frame Contract')), \
                patch.object(single_backend, 'invoke_codex', side_effect=fake_invoke):
            with self.assertRaisesRegex(ValueError, 'PROMPT_SOURCE_DRIFT'):
                single_backend.generate_for_frame(ns)
        self.assertEqual(len(calls), 1)  # Drift blocks before any backend invocation.

    def test_batch_delivery_entry_fails_closed_on_prompt_source_drift_before_provider_send(self):
        contract = {'planned_count': 1, 'batch_id': 'B1',
                    'frames': [{'queue_item_id': 'Q1', 'frame': 1, 'output_index': 1}]}
        items = [{'id': 'Q1', 'frame': 1, 'model': 'gpt-image-2', 'quality': 'high',
                  'attempts': 1, 'references': []}]
        route = {'provider': 'openai_images_api', 'execution_mode': 'native_n',
                 'native_multi_image': True, 'single_http_request': True}
        with patch.object(batch_delivery, 'read_canvas', return_value=(1088, 1360, '4:5')), \
                patch.object(batch_delivery.image_provider_router, 'select_for_batch', return_value=route), \
                patch.object(batch_delivery.openai_batch_prompt_compiler, 'compile_batch',
                             side_effect=ValueError('PROMPT_SOURCE_DRIFT: unchanged scene prompt belongs to an older Frame Contract')), \
                patch.object(batch_delivery.raw_candidate_budget, 'claim') as claim, \
                patch.object(batch_delivery.runtime_trace, 'start_span') as start_span, \
                patch.object(batch_delivery, '_invoke_openai_native_n') as invoke:
            # Compile happens before the provider/trace section, so drift
            # escapes the module boundary and fails closed without a send.
            with self.assertRaisesRegex(ValueError, 'PROMPT_SOURCE_DRIFT'):
                batch_delivery.execute_batch(self.ep, contract, items, 60, None)
        invoke.assert_not_called()
        claim.assert_not_called()
        start_span.assert_not_called()

    def test_incremental_review_entry_routes_cod_and_patch_full_and_work_escalation(self):
        plan = {'action': 'PATCH', 'dirty_frames': ['01'], 'context_frames': ['01', '02'],
                'reasons': {'01': ['asset_sha_changed']}, 'dirty_ratio': 0.125,
                'caption_mode': 'none'}
        with patch.object(incr, 'build_plan', return_value=plan), \
                patch.object(incr, 'verify_episode', return_value=[]):
            with patch.object(incr.runtime_router, 'detect', return_value=('CODEX', 'test')), \
                    patch.object(incr, '_run_patch', return_value=0) as run_patch, \
                    patch.object(semantic, 'run_critic', return_value=0) as run_critic:
                self.assertEqual(incr.run_review(self.ep, attempt=1, codex_raw='codex.exe'), 0)
                run_patch.assert_called_once()
                run_critic.assert_not_called()
            state = batch_review.read_json(self.ep / incr.STATE_REL)
            self.assertEqual(state['action'], 'PATCH')
            with patch.object(incr.runtime_router, 'detect', return_value=('WORK', 'test')), \
                    patch.object(incr, '_run_patch', return_value=0) as run_patch, \
                    patch.object(semantic, 'run_critic', return_value=0) as run_critic, \
                    patch.object(incr, '_decorate_full') as decorate:
                # WORK with no explicit codex must escalate PATCH to the full product review.
                self.assertEqual(incr.run_review(self.ep, attempt=1, codex_raw=None), 0)
                run_critic.assert_called_once()
                run_patch.assert_not_called()
                decorate.assert_called_once()
        full = dict(plan, action='FULL')
        with patch.object(incr, 'build_plan', return_value=full), \
                patch.object(incr, 'verify_episode', return_value=[]), \
                patch.object(incr.runtime_router, 'detect', return_value=('CODEX', 'test')), \
                patch.object(semantic, 'run_critic', return_value=0) as run_critic, \
                patch.object(incr, '_decorate_full') as decorate:
            self.assertEqual(incr.run_review(self.ep, attempt=1, codex_raw='codex.exe'), 0)
            run_critic.assert_called_once()
            decorate.assert_called_once()
        noop = {'action': 'NOOP', 'dirty_frames': [], 'context_frames': [],
                'reasons': {}, 'caption_mode': 'none'}
        with patch.object(incr, 'build_plan', return_value=noop), \
                patch.object(incr, 'verify_episode', return_value=[]) as verify, \
                patch.object(incr.runtime_router, 'detect', return_value=('CODEX', 'test')), \
                patch.object(semantic, 'run_critic', return_value=0) as run_critic:
            self.assertEqual(incr.run_review(self.ep, attempt=1, codex_raw=None), 0)
            verify.assert_called_once()
            run_critic.assert_not_called()


if __name__ == '__main__':
    unittest.main()
