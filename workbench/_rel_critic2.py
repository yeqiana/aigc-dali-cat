
# -*- coding: utf-8 -*-
"""Re-run the release semantic host critic without -o so the critic's own JSON
write to the candidate path survives (the first run's -o clobbered it)."""
import json, pathlib, shutil, sys
sys.path.insert(0, str(pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat') / 'episodes/_system'))
import codex_critic_runner as runner

root = pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat')
ep = root / r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
codex = pathlib.Path(r'C:/Users/79873/AppData/Local/OpenAI/Codex/bin/fd4c151a749f3ab4/codex.exe')
prompt = (ep / 'meta/.release-critic-prompt.txt').read_text(encoding='utf-8')
req = json.loads((ep / 'meta/.release-critic-request-stdout.json').read_text(encoding='utf-8'))
candidate = root / req['candidate_path']
candidate.unlink(missing_ok=True)

old = ep / 'meta/release-semantic-host-critic-attempt-1.jsonl'
archive = ep / 'meta/archive'
archive.mkdir(parents=True, exist_ok=True)
if old.is_file():
    shutil.move(str(old), str(archive / 'release-semantic-host-critic-attempt-1-o-clobbered.jsonl'))
    print('archived first transcript')

stage = root / '.storyos_tmp/release-critic'
attachments = [stage / n for n in ('cover-cover.png', 'body01-01.png', 'body02-02.png',
                                   'body03-03.png', 'climax-15.png', 'payoff-20.png')]
res = runner.launch(prompt, codex=codex, root=root, timeout=2400, output_path=None,
                    attachments=attachments, reasoning_effort='high', log_path=old)
print('rc', res.returncode, 'log_bytes', old.stat().st_size)
print('candidate_exists', candidate.is_file())
if candidate.is_file():
    raw = candidate.read_bytes()
    print('candidate_bytes', len(raw), 'head', raw[:40])
    try:
        data = json.loads(raw.decode('utf-8-sig'))
        print('summary', json.dumps(data.get('summary'), ensure_ascii=False))
        print('release_checks', json.dumps(data.get('release_checks'), ensure_ascii=False))
        print('governance_checks', json.dumps(data.get('governance_checks'), ensure_ascii=False))
        print('issue_codes', json.dumps(data.get('issue_codes'), ensure_ascii=False))
        print('notes', json.dumps(data.get('notes'), ensure_ascii=False)[:600])
    except Exception as exc:
        print('PARSE_FAIL', exc)
print('HOST_CRITIC_DONE')

