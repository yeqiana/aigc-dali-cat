import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const dist = path.resolve('dist/assets');
const files = fs.readdirSync(dist);
function chunk(name) {
  const file = files.find(value => value.startsWith(name + '-') && value.endsWith('.js'));
  assert.ok(file, '缺少构建分包: ' + name);
  return { name:file, size:fs.statSync(path.join(dist, file)).size };
}
const entry = chunk('index');
const episodes = chunk('historical-episodes');
const runs = chunk('historical-runs');
assert.ok(entry.size <= 350_000, '主入口大于 350 KB: ' + entry.size);
assert.ok(runs.size > 100_000 && episodes.size > 100_000, '未正确拆分历史 Run / Episode');
const html = fs.readFileSync(path.resolve('dist/index.html'), 'utf8');
assert.ok(!html.includes('historical-runs-'), '历史 Run 包不应被首页预加载');
console.log('PASS 主入口 ' + entry.size + 'B，预算 350000B');
console.log('PASS Episode 证据 ' + episodes.size + 'B，历史 Run ' + runs.size + 'B 独立按需加载');
console.log('PASS 首页 HTML 不预加载 Run 快照（总资源体积并未因此同比下降）');
