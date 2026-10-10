import assert from 'node:assert/strict';
import vm from 'node:vm';
import fs from 'node:fs';
import ts from 'typescript';
const compiled=ts.transpileModule(fs.readFileSync('src/api/runtimeCoverage.ts','utf8'),{
  compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}
}).outputText;
const ctx={exports:{}};vm.runInNewContext(compiled,ctx);
const fn=ctx.exports.summarizeRuntimeCoverage;
assert.equal(typeof fn,'function');
const first=fn(100,150,true);
assert.equal(first.incomplete,true);
assert.equal(first.total,150);
assert.match(first.warning,/部分阶段摘要/);
const complete=fn(4,4,false);
assert.equal(complete.incomplete,false);
assert.equal(complete.warning,null);
const partial=fn(100,100,false,['SOURCE_UNAVAILABLE']);
assert.match(partial.warning,/部分错误/);
const unknown=fn(10,null,false);
assert.equal(unknown.total,null);
assert.equal(unknown.incomplete,false);
assert.equal(fn(-1,-5,false).loaded,0);
console.log('PASS 权威阶段覆盖率 5 类边界：分页不完整、完整、部分错误、未知总数、非法数量');
