// 仅供浏览器回归：从 dist/ 只读服务构建产物，不提供任何 API 代理或写入。
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';

const root = path.resolve(process.argv[2] || 'dist');
const mime = { '.html':'text/html; charset=utf-8', '.js':'text/javascript; charset=utf-8',
  '.css':'text/css; charset=utf-8', '.json':'application/json; charset=utf-8',
  '.svg':'image/svg+xml', '.png':'image/png' };
const server = http.createServer((request, response) => {
  try {
    const pathname = decodeURIComponent(new URL(request.url || '/', 'http://localhost').pathname);
    const file = path.resolve(root, '.' + (pathname === '/' ? '/index.html' : pathname));
    if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
      response.writeHead(404); response.end('Not found'); return;
    }
    response.writeHead(200, {'Content-Type':mime[path.extname(file)]||'application/octet-stream',
      'Cache-Control':'no-store'});
    fs.createReadStream(file).pipe(response);
  } catch { response.writeHead(400); response.end('Invalid file'); }
});
server.listen(0, '127.0.0.1', () => {
  process.stdout.write('READY '+server.address().port+'\n');
});
process.on('SIGTERM', () => server.close());
