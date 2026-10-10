import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';

const source = fs.readFileSync('src/api/exclusiveReadGate.ts', 'utf8');
const js = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }
}).outputText;
const runtime = { exports: {} };
vm.runInNewContext(js, runtime);
const { ExclusiveReadGate } = runtime.exports;
assert.equal(typeof ExclusiveReadGate, 'function');

const gate = new ExclusiveReadGate();
const a = gate.begin();
assert.equal(a, 1);
assert.equal(gate.begin(), null, '同时只能存在一个查询');
assert.equal(gate.isCurrent(a), true);
assert.equal(gate.finish(a), true);
assert.equal(gate.isCurrent(a), false);
assert.equal(gate.finish(a), false, '释放必须幂等');
const b = gate.begin();
assert.equal(b, 2);
gate.invalidate(); // 卸载或 StrictMode cleanup。
assert.equal(gate.isCurrent(b), false);
assert.equal(gate.finish(b), false, '旧请求不得释放新锁');
const c = gate.begin();
assert.equal(c, 4);
assert.equal(gate.finish(b), false);
assert.equal(gate.isCurrent(c), true);
assert.equal(gate.finish(c), true);
console.log('PASS 监控独占读代际锁：重叠保护 / 回调过期 / 卸载 / 新请求 / 幂等释放（5 类）');
