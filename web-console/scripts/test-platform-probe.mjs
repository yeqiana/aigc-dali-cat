import assert from 'node:assert/strict';
import http from 'node:http';
import {spawn} from 'node:child_process';
import {once} from 'node:events';

const server=http.createServer((req,res)=>{
  res.setHeader('Content-Type','application/json');
  if(req.url==='/healthz') return res.end(JSON.stringify({code:'OK',data:{status:'UP'}}));
  if(req.url?.startsWith('/api/v1/runtime/statuses?')) return res.end(JSON.stringify({code:'OK',data:{items:[],total:0}}));
  res.writeHead(404);res.end('{}');
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const port=server.address().port;
async function exec(url) {
  const child=spawn(process.execPath,['scripts/probe-platform-readonly.mjs'],{
    env:{...process.env,STORYOS_READONLY_API_URL:url},stdio:['ignore','pipe','pipe']
  });
  let stdout='',stderr='';
  child.stdout.on('data',b=>stdout+=b.toString());
  child.stderr.on('data',b=>stderr+=b.toString());
  const [exit]=await once(child,'close');
  return {exit,stdout,stderr};
}
try {
  const ok=await exec('http://127.0.0.1:'+port);
  assert.equal(ok.exit,0,ok.stderr);
  assert.match(ok.stdout,/READONLY_API_READY/);
  const forbidden=await exec('https://example.com');
  assert.equal(forbidden.exit,2);
  assert.match(forbidden.stderr,/只允许对本机/);
  const credentials=await exec('http://username:password@127.0.0.1:'+port);
  assert.equal(credentials.exit,2);
  const offline=await exec('http://127.0.0.1:1');
  assert.equal(offline.exit,1);
  assert.match(offline.stderr,/READONLY_API_UNAVAILABLE/);
  console.log('PASS 4/4：只读 API 可达、禁止远程、禁止凭据 URL、断线安全失败');
}finally {server.close();}
