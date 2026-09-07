#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REMOVED_HEADINGS = (
    '## Story OS V2.1｜一句话全自动入口',
    '## Runtime DAG Refactor｜更快、更能断点续跑',
    '## Runtime Performance Pack P0.7–P1.2',
    '## Character / Entry Pool｜普通年轻人先于异常',
    '## Runtime Optimization R2｜缓存 / 资源库 / ChatGPT→Codex 接力',
    '## V2.0.3.4 新篇目录约定',
)

REQUIRED_README_LINKS = (
    'AGENTS.md',
    'SKILL.md',
    'START_HERE.md',
    'standards/制作规范_正式版.md',
    'config/index.yaml',
    'episode_layout',
)


def rule_blocks(path):
    text = path.read_text(encoding='utf-8-sig')
    blocks = {}
    current = None
    body = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith('<!-- STORY_OS_') and 'BEGIN -->' in s:
            name = s[len('<!-- '):].split('_BEGIN')[0]
            current = name
            body = []
        elif s.startswith('<!-- STORY_OS_') and 'END -->' in s:
            name = s[len('<!-- '):].split('_END')[0]
            if current != name:
                raise AssertionError('unbalanced Story OS marker: ' + s)
            blocks.setdefault(name, []).append(body)
            current = None
        elif current is not None:
            body.append(line)
    return blocks


class DocsAuthorityConsistencyTests(unittest.TestCase):

    def test_readme_has_no_rule_copies(self):
        text = (ROOT / 'README.md').read_text(encoding='utf-8-sig')
        self.assertNotIn('<!-- STORY_OS_', text)
        for heading in REMOVED_HEADINGS:
            self.assertNotIn(heading, text)
        for link in REQUIRED_README_LINKS:
            self.assertIn(link, text)

    def test_shared_rule_blocks_identical_between_agents_and_skill(self):
        agents = rule_blocks(ROOT / 'AGENTS.md')
        skill = rule_blocks(ROOT / 'SKILL.md')
        shared = sorted(set(agents) & set(skill))
        self.assertTrue(shared, 'no shared rule blocks remain to protect')
        for name in shared:
            self.assertEqual(len(agents[name]), 1, name + ' duplicated in AGENTS.md')
            self.assertEqual(len(skill[name]), 1, name + ' duplicated in SKILL.md')
            self.assertEqual(agents[name][0], skill[name][0], name + ' drifted between AGENTS.md and SKILL.md')

    def test_portal_version_line_derives_from_manifest(self):
        manifest = json.loads((ROOT / 'story_os_manifest.json').read_text(encoding='utf-8-sig'))
        portal = (ROOT / 'docs/story_os_document_portal/README.txt').read_text(encoding='utf-8-sig')
        self.assertIn('story_os_manifest.json', portal)
        self.assertIn(str(manifest['platform_version']), portal)
        self.assertNotIn('V2.1 主平台 + V2.2 Visual Narrative Core R1 主链集成', portal)


if __name__ == '__main__':
    unittest.main()
