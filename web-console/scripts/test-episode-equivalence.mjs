import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
const old=spawnSync('git',['show','26d18691:web-console/src/data/storyosEpisodeSnapshots.ts'],{encoding:'utf8'});
assert.equal(old.status,0);
function decode(text){const marker=': Episode[] =';const i=text.indexOf(marker);assert.ok(i>=0);return JSON.parse(text.slice(i+marker.length).trim().replace(/;\s*$/,''));}
const original=decode(old.stdout);
const rows=[1,2,3].flatMap(n=>decode(fs.readFileSync('src/data/storyosEpisodePart'+n+'.ts','utf8')));
assert.equal(rows.length,original.length);
assert.deepEqual(rows,original,'必须完整保留历史证据字段和原顺序');
assert.equal(new Set(rows.map(x=>x.id)).size,rows.length);
console.log('PASS 历史 Episode 11/11 数据完整且顺序一致');
