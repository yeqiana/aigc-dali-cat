#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import importlib.util
import json
import os
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

SYSTEM = Path(__file__).resolve().parent
ROOT = SYSTEM.parents[1]
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SYSTEM / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module

router = load('router201', 'runtime_router.py')
backend = load('backend201', 'codex_subscription_image.py')
story_contract = load('story_contract201', 'story_os_contract.py')

class EngineeringTests(unittest.TestCase):
    def test_version_contract(self):
        data = json.loads((ROOT / 'runtimes/runtime-contract.json').read_text(encoding='utf-8'))
        manifest = json.loads((ROOT / 'story_os_manifest.json').read_text(encoding='utf-8-sig'))
        self.assertIn('module_version', data)
        self.assertIn('platform_min_version', data)
        self.assertEqual(manifest['platform_version'], story_contract.story_os_version())
        self.assertEqual(data['common_rules']['stable_evidence_gate'], 'episodes/_system/evidence_gate.py')

    def test_legacy_runtime_override_does_not_change_production_mode(self):
        # production.mode owns effective runtime; STORY_OS_RUNTIME is diagnostics only.
        with patch.dict(os.environ, {'STORY_OS_RUNTIME': 'WEB',
                                     'STORY_OS_PRODUCTION_MODE': 'COLLABORATIVE'}):
            effective, source = router.detect()
        self.assertEqual(effective, 'WORK')
        self.assertIn('STORY_OS_PRODUCTION_MODE', source)

    def test_backend_prompt_contract(self):
        text = backend.worker_prompt('scene', [], '1024x1280')
        self.assertIn('image_generation exactly once', text)
        self.assertNotIn('./out.png', text)
        self.assertIn('thread_id', text)
        self.assertIn('stop immediately', text)

    def test_release_version_not_v18(self):
        text = (SYSTEM / 'release_package.py').read_text(encoding='utf-8')
        self.assertNotIn("'story_os_version': '1.8'", text)
        self.assertIn("from story_os_contract import story_os_version", text)
        self.assertIn("STORY_OS_VERSION = story_os_version()", text)

    def test_story_os_uses_stable_gate(self):
        text = (SYSTEM / 'story_os.py').read_text(encoding='utf-8')
        self.assertIn('evidence_gate.py', text)
        self.assertNotIn('python episodes/_system/v18_gate.py', text)

if __name__ == '__main__':
    unittest.main()
