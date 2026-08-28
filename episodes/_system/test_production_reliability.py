#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SYSTEM_DIR = Path(__file__).resolve().parent


def load_module(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, SYSTEM_DIR / file)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


text_audit = load_module('text_audit_v17', 'text_audit.py')


class TextAuditTests(unittest.TestCase):
    def test_detects_empty_long_and_forbidden(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'subtitles.yaml'
            p.write_text(
                'voice_card:\n'
                '  person: "我"\n'
                '  role: "游客"\n'
                '  education_and_knowledge_boundary: "普通人"\n'
                '  recording_reason: "随手拍"\n'
                '  knows_now: "只知道迷路"\n'
                '  does_not_know: "不知道原因"\n'
                '  forbidden_technical_terms: "量子纠缠"\n'
                '  stress_language: "短句"\n'
                '  fear_language_change: "停顿"\n'
                'frames:\n'
                '  1: ""\n'
                '  2: "量子纠缠说明这里不对"\n'
                '  3: "' + ('很' * 49) + '"\n'
                'silent_frames: []\n',
                encoding='utf-8'
            )
            data = text_audit.parse_simple_subtitles_yaml(p)
            report = text_audit.audit(data, p)
            codes = {x['code'] for x in report['hard_errors']}
            self.assertIn('EMPTY_CAPTION_NOT_SILENT', codes)
            self.assertIn('FORBIDDEN_TECH_TERM', codes)
            self.assertIn('CAPTION_TOO_LONG', codes)

    def test_three_frame_ai_rhythm_warning(self):
        data = {
            'frames': {1: '我发现门开了', 2: '我发现灯灭了', 3: '我发现人不见了'},
            'voice_card': {}, 'silent_frames': [], 'raw_text': ''
        }
        report = text_audit.audit(data, Path('x.txt'))
        codes = {x['code'] for x in report['warnings']}
        self.assertIn('REPEATED_PREFIX_3', codes)


class ReliabilityCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ep = Path(self.tmp.name) / 'episode'
        (self.ep / 'meta').mkdir(parents=True)
        (self.ep / 'docs').mkdir()
        (self.ep / 'production/approved').mkdir(parents=True)
        (self.ep / 'docs/captions.txt').write_text('第一句\n第二句\n第三句\n', encoding='utf-8')
        (self.ep / 'production/approved/01.png').write_bytes(b'locked-image')
        (self.ep / 'meta/release-manifest.json').write_text('{}\n', encoding='utf-8')
        ledger = {
            'frames': {
                '01': {
                    'status': 'GENERATING',
                    'attempts': [
                        {
                            'attempt_id': 'a1',
                            'result': 'pending',
                            'request': {'frame': '01', 'kind': 'original', 'prompt_sha256': 'x', 'model': 'm', 'references': []},
                        }
                    ]
                }
            }
        }
        req = ledger['frames']['01']['attempts'][0]['request']
        import hashlib
        encoded = json.dumps(req, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
        ledger['frames']['01']['attempts'][0]['request_fingerprint'] = hashlib.sha256(encoded).hexdigest()
        (self.ep / 'meta/production-ledger.json').write_text(json.dumps(ledger), encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, script: str, *args: str):
        return subprocess.run([sys.executable, str(SYSTEM_DIR / script), *map(str, args)], capture_output=True, text=True)

    def test_transport_preflight_and_failure(self):
        r = self.run_script('transport_guard.py', 'preflight', self.ep, '01')
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        r = self.run_script('transport_guard.py', 'failure', self.ep, '01', '--category', 'timeout', '--message', 'timeout')
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        state = json.loads((self.ep / 'meta/transport-state.json').read_text(encoding='utf-8'))
        self.assertEqual(state['frames']['01']['consecutive_technical_failures'], 1)

    def test_text_revision_protects_assets_and_reverts(self):
        r = self.run_script('text_revision.py', 'start', self.ep, '--file', 'docs/captions.txt')
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        (self.ep / 'docs/captions.txt').write_text('改过的第一句\n短句\n停一下\n', encoding='utf-8')
        r = self.run_script('text_revision.py', 'submit', self.ep)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        r = self.run_script('text_revision.py', 'approve', self.ep, '--user-approved')
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)

    def test_text_revision_detects_protected_change(self):
        r = self.run_script('text_revision.py', 'start', self.ep, '--file', 'docs/captions.txt')
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        (self.ep / 'docs/captions.txt').write_text('改了\n', encoding='utf-8')
        (self.ep / 'production/approved/01.png').write_bytes(b'changed')
        r = self.run_script('text_revision.py', 'submit', self.ep)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('protected assets changed', r.stderr + r.stdout)


if __name__ == '__main__':
    unittest.main()
