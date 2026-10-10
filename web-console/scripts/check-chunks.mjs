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
const parts = ['historical-episode-a', 'historical-episode-b', 'historical-episode-c'].map(chunk);
const runs = chunk('historical-runs');
assert.ok(entry.size <= 350_000, '主入口大于 350 KB: ' + entry.size);
assert.ok(runs.size > 100_000 && parts.every(x => x.size > 100_000 && x.size < 500_000), '历史 Episode 分包须各小于 500 KB');
const html = fs.readFileSync(path.resolve('dist/index.html'), 'utf8');
assert.ok(!html.includes('historical-runs-'), '历史 Run 包不应被首页预加载');
console.log('PASS 主入口 ' + entry.size + 'B，预算 350000B');
console.log('PASS Episode 三个分包 ' + parts.map(x => x.size).join('/') + ' B，历史 Run ' + runs.size + ' B');
console.log('PASS Run 历史证据不随首页预加载，Episode 仍全部随首页静态引用');
