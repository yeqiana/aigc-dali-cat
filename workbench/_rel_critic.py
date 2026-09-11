
# -*- coding: utf-8 -*-
"""Host (product-runtime stand-in) launch of the release semantic critic.

Mirrors the visual-lock baseline host run: the WORK-runtime request prepared by
release_preflight is executed in a fresh isolated Codex session with ASCII-only
staged image attachments, logging the full JSONL transcript into meta/.
"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat') / 'episodes/_system'))
import codex_critic_runner as runner

root = pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat')
ep = root / r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
codex = pathlib.Path(r'C:/Users/79873/AppData/Local/OpenAI/Codex/bin/fd4c151a749f3ab4/codex.exe')
assert codex.is_file(), codex

prompt = (ep / 'meta/.release-critic-prompt.txt').read_text(encoding='utf-8')
req = json.loads((ep / 'meta/.release-critic-request-stdout.json').read_text(encoding='utf-8'))
candidate = root / req['candidate_path']
candidate.unlink(missing_ok=True)
stage = root / '.storyos_tmp/release-critic'
attachments = [stage / n for n in ('cover-cover.png', 'body01-01.png', 'body02-02.png',
                                   'body03-03.png', 'climax-15.png', 'payoff-20.png')]
log = ep / 'meta/release-semantic-host-critic-attempt-1.jsonl'

res = runner.launch(
    prompt,
    codex=codex,
    root=root,
    timeout=2400,
    output_path=candidate,
    attachments=attachments,
    reasoning_effort='high',
    log_path=log,
)
print('rc', res.returncode, 'log', log, 'log_bytes', log.stat().st_size)
print('candidate_exists', candidate.is_file())
if candidate.is_file():
    data = json.loads(candidate.read_text(encoding='utf-8'))
    print('summary', json.dumps(data.get('summary'), ensure_ascii=False))
    print('release_checks', json.dumps(data.get('release_checks'), ensure_ascii=False))
    print('governance_checks', json.dumps(data.get('governance_checks'), ensure_ascii=False))
    print('issue_codes', json.dumps(data.get('issue_codes'), ensure_ascii=False))
print('HOST_CRITIC_DONE')

