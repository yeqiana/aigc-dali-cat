import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(here,'../..');
const web=path.resolve(root,'web-console');
const apiPort=Number(process.env.STORYOS_FIXTURE_PORT || 18080);
const webPort=Number(process.env.STORYOS_LOCAL_CONSOLE_PORT || 3100);
if(!Number.isInteger(apiPort)||!Number.isInteger(webPort)||apiPort<1024||webPort<1024||apiPort>65535||webPort>65535||apiPort===webPort)throw Error('Invalid local fixture ports');
const python=process.env.STORYOS_PYTHON|| (process.platform==='win32'
  ?path.join(process.env.LOCALAPPDATA||'C:\\Users\\79873\\AppData\\Local','Programs','Python','Python312','python.exe')
  :'python3');
const vite=path.resolve(web,'node_modules','vite','bin','vite.js');
const children=[];
let closing=false;
function shutdown(code=0){
 if(closing)return;
 closing=true;
 for(const child of children)try{child.kill();}catch{}
 process.exitCode=code;
}
for(const sig of ['SIGINT','SIGTERM'])process.on(sig,()=>{shutdown();setTimeout(()=>process.exit(),800).unref();});
process.on('exit',()=>{for(const child of children)try{child.kill();}catch{}});
function start(file,args,cwd,env=process.env){
 const child=spawn(file,args,{cwd,env,stdio:['ignore','pipe','pipe'],windowsHide:true});
 children.push(child);
 child.stdout.on('data',data=>process.stdout.write('[local] '+data.toString()));
 child.stderr.on('data',data=>process.stderr.write('[local] '+data.toString()));
 child.once('error',error=>{console.error('Local child could not start:',error.message);shutdown(1);});
 child.once('exit',code=>{if(!closing){console.error('Local service stopped unexpectedly:',code);shutdown(1);}});
 return child;
}
async function poll(url,check){
 const deadline=Date.now()+25000;
 while(Date.now()<deadline && !closing){
   try {
     const resp=await fetch(url,{signal:AbortSignal.timeout(1300),cache:'no-store'});
     if(resp.ok&&await check(resp))return;
   }catch{}
   await new Promise(resolve=>setTimeout(resolve,300));
 }
 throw Error('Local endpoint not ready: '+url);
}
async function main(){
 console.log('本地隔离联调模式：仅 127.0.0.1，只有内存 Fixture；不启动生产 Runtime 或数据库');
 start(python,[path.resolve(root,'scripts','storyos_isolated_api_fixture.py'),'--port',String(apiPort)],root);
 await poll('http://127.0.0.1:'+apiPort+'/healthz',async r=>(await r.json()).code==='OK');
 const viteEnv={...process.env,VITE_PLATFORM_API_URL:'http://127.0.0.1:'+apiPort,VITE_STORYOS_FIXTURE_MODE:'true'};
 start(process.execPath,[vite,'--host','127.0.0.1','--port',String(webPort),'--strictPort'],web,viteEnv);
 await poll('http://127.0.0.1:'+webPort+'/',async r=>(await r.text()).includes('id="root"'));
 await poll('http://127.0.0.1:'+webPort+'/api/v1/runtime/statuses?limit=1&offset=0',async r=>{
  const payload=await r.json();return payload.code==='OK'&&payload.data?.items?.[0]?.state_source==='isolated-test';
 });
 console.log('LOCAL_STORYOS_READY http://127.0.0.1:'+webPort+'/');
 console.log('LOCAL_FIXTURE_API http://127.0.0.1:'+apiPort+'/healthz');
 console.log('请不要将测试数据当作真实 Runtime 状态；Ctrl+C 可关闭两个子进程。');
}
main().catch(error=>{console.error(error.message);shutdown(1);});
