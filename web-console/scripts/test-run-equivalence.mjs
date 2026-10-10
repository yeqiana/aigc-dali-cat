import assert from 'node:assert/strict';
import fs from 'node:fs';
import {spawnSync} from 'node:child_process';
const original=spawnSync('git',['show','55164f21:web-console/src/data/storyosRunSnapshots.ts'],{encoding:'utf8'});
assert.equal(original.status,0);
function parse(text,marker){const p=text.indexOf(marker);assert.ok(p>=0);return JSON.parse(text.slice(p+marker.length).trim().replace(/;\s*$/,'').replace(/\s+as unknown as StoryRunItem\[\]\s*$/,''));}
const before=parse(original.stdout,': StoryRunItem[] =');
const detail=Array.from({length:11},(_,i)=>parse(fs.readFileSync('src/data/runDetail'+String(i+1).padStart(2,'0')+'.ts','utf8'),': StoryRunItem ='));
assert.deepEqual(detail,before);
const index=parse(fs.readFileSync('src/data/storyosRunSnapshots.ts','utf8'),': StoryRunItem[] =');
assert.equal(index.length,11);
assert.ok(index.every(x=>x.__indexOnly===true&&x.frames.length===0&&x.pipelineStages.length===0));
console.log('PASS 11/11 历史 Run 完整详情与冻结基线逐字段一致，首屏仅列表索引');
