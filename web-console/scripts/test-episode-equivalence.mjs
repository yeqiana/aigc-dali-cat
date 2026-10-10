import assert from 'node:assert/strict';
import fs from 'node:fs';
import {spawnSync} from 'node:child_process';
function parseData(text,marker) { const pos=text.indexOf(marker);assert.ok(pos>=0,marker);return JSON.parse(text.slice(pos+marker.length).trim().replace(/;\s*$/,'').replace(/\s+as unknown as Episode\[\]\s*$/,'')); }
const originals=[];
for(let n=1;n<=3;n++){
 const result=spawnSync('git',['show','b4063a1c:web-console/src/data/storyosEpisodePart'+n+'.ts'],{encoding:'utf8'});
 assert.equal(result.status,0);
 originals.push(...parseData(result.stdout,': Episode[] ='));
}
const details=[];
for(let n=1;n<=11;n++){
 const text=fs.readFileSync('src/data/episodeDetail'+String(n).padStart(2,'0')+'.ts','utf8');
 details.push(parseData(text,': Episode ='));
}
assert.deepEqual(details, originals, '单作品详情必须完整保留 11 部历史作品所有字段与顺序');
const index=parseData(fs.readFileSync('src/data/storyosEpisodeSnapshots.ts','utf8'),': Episode[] =');
assert.equal(index.length,11);
assert.deepEqual(index.map(r=>r.id), details.map(r=>r.id));
assert.ok(index.every(r=>r.__indexOnly===true&&r.runtimeRequest.sourceBadge==='示例数据'));
assert.ok(index.every(r=>r.frameReviews.length===0&&r.storyboardBeats.length===0));
console.log('PASS 11 部完整历史作品详情与基线一致，首屏仅包含轻量目录');
