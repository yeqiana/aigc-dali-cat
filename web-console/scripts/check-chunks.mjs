import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const dist=path.resolve('dist/assets');
const files=fs.readdirSync(dist);
const entry=files.find(name=>/^index-[\w-]+\.js$/.test(name));
const evidence=files.find(name=>/^workspace-evidence-[\w-]+\.js$/.test(name));
assert.ok(entry,'未找到独立最小入口');
assert.ok(evidence,'未找到单独的工作区证据包');
const entryBytes=fs.statSync(path.join(dist,entry)).size;
const evidenceBytes=fs.statSync(path.join(dist,evidence)).size;
assert.ok(entryBytes<=300_000,'入口资源超过第四轮约定的 300KB 预算：'+entryBytes);
assert.ok(evidenceBytes>entryBytes,'证据数据应独立于轻量应用入口');
console.log('PASS 入口资源 '+entryBytes+' B（阈值 300000 B）');
console.log('PASS 证据独立资源 '+evidenceBytes+' B；该文件仍需后续数据裁剪/分页，不能把分包理解成总体积下降');
