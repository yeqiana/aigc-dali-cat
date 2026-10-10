import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
const dist=path.resolve('dist');
const port=Number(process.argv[2]);
if(!Number.isInteger(port)||port<1024)throw Error('Invalid QA port');
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp'};
http.createServer((req,res)=>{
 const url=new URL(req.url||'/',`http://127.0.0.1:${port}`);
 const rel=decodeURIComponent(url.pathname).replace(/^\/+/, '')||'index.html';
 const target=path.resolve(dist,rel);
 if(!target.startsWith(dist+path.sep)){res.writeHead(403).end();return;}
 fs.readFile(target,(err,data)=>{if(err){res.writeHead(404).end();return;}res.writeHead(200,{'Content-Type':types[path.extname(target)]||'application/octet-stream','Cache-Control':'no-store'}).end(data);});
}).listen(port,'127.0.0.1');
