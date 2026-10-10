import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';

const source = fs.readFileSync('src/api/httpClient.ts', 'utf8');
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText;
const exportsObject = {};
let fetchStub = async () => { throw new Error('fetch stub unavailable'); };
const fakeRequire = (name) => {
  if (name === '../config/appConfig') return { appConfig: { platformApiBaseUrl: '' } };
  throw new Error('Unexpected import ' + name);
};
const sandbox = {
  exports: exportsObject,
  require: fakeRequire,
  fetch: (...args) => fetchStub(...args),
  AbortController, setTimeout, clearTimeout,
};
vm.runInNewContext(compiled, sandbox, { filename: 'httpClient.ts' });
const { platformRequest } = sandbox.exports;
if (typeof platformRequest !== 'function') throw new Error('No platformRequest');
const response = (status, payload) => ({
  ok: status >= 200 && status < 300,
  status,
  text: async () => payload === null ? '' : JSON.stringify(payload),
});
let passed = 0;
async function check(name, run) {
  try { await run(); console.log('PASS ' + name); passed++; }
  catch(error) { console.error('FAIL ' + name + ': ' + error.message); process.exitCode = 1; }
}

await check('合法信封解包', async () => {
  fetchStub = async () => response(200, { code: 'OK', data: { entries: 3 } });
  assert.equal((await platformRequest('/api/v1/runtime/statuses')).entries, 3);
});
await check('受控能力不可用必须失败', async () => {
  fetchStub = async () => response(503, { code: 'CAPABILITY_NOT_CONFIGURED', message: '能力未接入', data: null });
  await assert.rejects(platformRequest('/api/v1/agents'), e => e.code === 'CAPABILITY_NOT_CONFIGURED' && e.httpStatus === 503);
});
await check('非 JSON 响应必须失败', async () => {
  fetchStub = async () => ({ ok: true, status: 200, text: async () => '<html>unexpected</html>' });
  await assert.rejects(platformRequest('/api/v1/runtime/status'), e => e.code === 'INVALID_RESPONSE');
});
await check('空响应不能伪造成功', async () => {
  fetchStub = async () => response(200, null);
  await assert.rejects(platformRequest('/api/v1/runtime/statuses'), e => e.code === 'INVALID_RESPONSE');
});
await check('请求前已取消应区分取消', async () => {
  fetchStub = async (_url, {signal}) => {
    assert.equal(signal.aborted, true);
    const error = new Error('cancelled'); error.name = 'AbortError'; throw error;
  };
  const controller = new AbortController(); controller.abort();
  await assert.rejects(platformRequest('/api/v1/runtime/status', { signal: controller.signal }), e => e.code === 'CANCELLED');
});
await check('超时不是主动取消', async () => {
  fetchStub = async (_url, {signal}) => new Promise((_resolve,reject) => {
    signal.addEventListener('abort', () => { const error = new Error('deadline'); error.name = 'AbortError'; reject(error); }, {once:true});
  });
  await assert.rejects(platformRequest('/api/v1/runtime/status', { timeoutMs: 15 }), e => e.code === 'TIMEOUT');
});
await check('网络断开应显式失败', async () => {
  fetchStub = async () => { throw new Error('network disconnected'); };
  await assert.rejects(platformRequest('/healthz'), e => e.code === 'NETWORK_ERROR');
});
console.log('API contract tests passed: ' + passed + '/7');
if (passed !== 7) process.exitCode = 1;
