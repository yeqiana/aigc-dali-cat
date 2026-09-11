
import json,pathlib,shutil
root=pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat'); ep=root/r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
req=json.loads((ep/'meta/.release-critic-request-stdout.json').read_text(encoding='utf-8'))
print('candidate_path:',req['candidate_path'])
print('prompt_path:',req.get('request_path'))
print('--- prompt tail ---')
print(req['prompt'][-600:])
stage=root/'.storyos_tmp/release-critic'
stage.mkdir(parents=True,exist_ok=True)
want={'cover.png':'cover','01.png':'body01','02.png':'body02','03.png':'body03','15.png':'climax','20.png':'payoff'}
staged=[]
for row in req['source_files']:
    name=row['path'].split('/')[-1]
    if name in want:
        src=root/row['path']
        dst=stage/(want[name]+'-'+name)
        shutil.copy2(src,dst)
        staged.append(str(dst))
(ep/'meta/.release-critic-prompt.txt').write_text(req['prompt'],encoding='utf-8')
print('--- staged ---')
for s in staged: print(s)

