import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { spawn } from 'node:child_process';
import { once } from 'node:events';

const cwd = process.cwd();
const dist = path.resolve(cwd, 'dist');
const fallbackPython = process.platform === 'win32'
  ? path.join(process.env.LOCALAPPDATA || '', 'Programs/Python/Python312/python.exe') : 'python3';
const python = process.env.STORYOS_PYTHON || fallbackPython;
const chrome = process.env.CHROME_PATH || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
assert.ok(fs.existsSync(chrome), 'Chrome binary unavailable');
assert.ok(fs.existsSync(path.join(dist,'index.html')), 'Run vite build --base=./ first');
const fixture = spawn(python, ['../scripts/storyos_isolated_api_fixture.py'], {cwd, stdio:['ignore','pipe','pipe']});
let stopped=false;
const apiPort = await new Promise((resolve,reject)=>{
  let content=''; const timeout=setTimeout(()=>reject(new Error('隔离 Python API 未启动')),12000);
  fixture.stdout.on('data',buf=>{content+=buf.toString();const m=content.match(/READY (\d+)/);if(m){clearTimeout(timeout);resolve(Number(m[1]));}});
  fixture.once('error',err=>{clearTimeout(timeout);reject(err);});
  fixture.once('exit',code=>{clearTimeout(timeout);reject(Error('API fixture exit '+code));});
});
function readFile(req,res){
  const filename=path.resolve(dist,'.'+(new URL(req.url,'http://localhost').pathname||'/index.html'));
  if(!filename.startsWith(dist+path.sep)||!fs.existsSync(filename)){res.writeHead(404);res.end();return;}
  const extension=path.extname(filename);
  res.writeHead(200, {'Content-Type': extension==='.js'?'text/javascript':extension==='.html'?'text/html':'text/css'});
  fs.createReadStream(filename).pipe(res);
}
const server=http.createServer(async(req,res)=>{
  if(req.url.startsWith('/api/')||req.url==='/healthz'){
    try{
      const upstream=await fetch('http://127.0.0.1:'+apiPort+req.url);
      res.writeHead(upstream.status,{'Content-Type':'application/json'});
      res.end(Buffer.from(await upstream.arrayBuffer()));
    }catch(e){res.writeHead(502);res.end('fixture upstream offline');}
    return;
  }
  readFile(req,res);
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const port=server.address().port;
const root=fs.readFileSync(path.join(dist,'index.html'),'utf8');
const runnerScript=String.raw`(async()=>{
 const wait=ms=>new Promise(r=>setTimeout(r,ms));
 const type='__TYPE__';
 try {
   if(type==='workflow'){
     let button;
     for(let i=0;i<70&&!button;i++){
       button=[...document.querySelectorAll('nav button')].find(b=>b.textContent.trim()==='工作流');
       if(!button)await wait(100);
     }
     if(!button)throw Error('navigation');
     button.click();
   }
   let ok=false;
   for(let i=0;i<180&&!ok;i++){
     const text=document.querySelector('main')?.textContent||'';
     ok=text.includes('真实 HTTP 联调样例') && text.includes('分镜锁定');
     if(!ok)await wait(100);
   }
   document.body.dataset.apiE2e=ok?'pass':'fail:data';
 }catch(e){document.body.dataset.apiE2e='fail:'+e.message}
})();`;
const profiles=path.resolve('../.storyos-tmp/ui-qa');
fs.mkdirSync(profiles,{recursive:true});
async function browserCase(which){
  const name='qa-r6-'+which+'.html',page=path.join(dist,name);
  fs.writeFileSync(page,root.replace('</body>','<script>'+runnerScript.replace('__TYPE__',which)+'</script></body>'));
  const child=spawn(chrome,[
    '--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
    '--virtual-time-budget=26000','--window-size=1440,900',
    '--user-data-dir='+path.join(profiles,'r6-api-'+which),
    '--dump-dom','http://127.0.0.1:'+port+'/'+name
  ],{stdio:['ignore','pipe','pipe']});
  let output='',error='';
  child.stdout.on('data',buf=>{output+=buf.toString();});
  child.stderr.on('data',buf=>{error+=buf.toString().slice(0,500);});
  const [code]=await once(child,'close');
  const marker=output.match(/data-api-e2e="([^"]+)"/)?.[1]||'missing';
  assert.equal(marker,'pass',which+' failed: '+marker+' exit='+code+' '+error.slice(-250));
  console.log('PASS 浏览器真实 HTTP 联调 '+which);
}
try{
  const health=await fetch('http://127.0.0.1:'+port+'/healthz');
  assert.equal(health.status,200);
  await browserCase('home');
  await browserCase('workflow');
  console.log('真实 HTTP 路由+代理+浏览器 E2E 2/2（仅隔离 fixture，非生产）');
}finally{
  stopped=true;
  server.close();
  fixture.kill();
}
