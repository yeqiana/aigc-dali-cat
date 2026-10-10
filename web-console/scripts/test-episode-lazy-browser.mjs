import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawn,spawnSync} from 'node:child_process';

const dist=path.resolve('dist'),base=fs.readFileSync(path.join(dist,'index.html'),'utf8');
const chrome=process.env.CHROME_PATH||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
assert.ok(fs.existsSync(chrome),'Chrome required');
const temp=path.resolve('../.storyos-tmp/ui-qa');fs.mkdirSync(temp,{recursive:true});
const server=spawn(process.execPath,['scripts/test-static-server.mjs',dist],{stdio:['ignore','pipe','pipe']});
const port=await new Promise((resolve,reject)=>{
 let b='';const timer=setTimeout(()=>reject(Error('HTTP server startup timeout')),12000);
 server.stdout.on('data',c=>{b+=c.toString();const m=b.match(/READY (\d+)/);if(m){clearTimeout(timer);resolve(Number(m[1]));}});
 server.once('error',reject);
});
const script=[
'(async()=>{try{',
'const sleep=ms=>new Promise(r=>setTimeout(r,ms));',
'let nav;',
'for(let i=0;i<120&&!nav;i++){nav=document.querySelector(\'nav[aria-label="主要页面"]\');if(!nav)await sleep(100);}',
'if(!nav)throw Error("navigation");',
'const initiallyLoaded=performance.getEntriesByType("resource").filter(x=>/episodeDetail\\d\\d-/.test(x.name));',
'if(initiallyLoaded.length)throw Error("eager-loaded "+initiallyLoaded.length+" detail modules");',
'const go=[...nav.querySelectorAll("button")].find(x=>x.textContent.trim()==="故事制作");',
'if(!go)throw Error("workbench nav");',
'go.click();',
'let hydrated=false;',
'for(let i=0;i<180;i++){',
' const main=document.querySelector("main");',
' if(main?.querySelector("#story-next-action-title")&&!(main.textContent||"").includes("正在按需加载")){hydrated=true;break;}',
' await sleep(100);',
'}',
'if(!hydrated)throw Error("detail_not_loaded");',
'const modules=performance.getEntriesByType("resource").filter(x=>/episodeDetail\\d\\d-/.test(x.name));',
'if(modules.length!==1)throw Error("not_one_detail: "+modules.length);',
'document.body.dataset.lazyE2e="pass";document.body.dataset.lazyFiles=String(modules.length);',
'}catch(e){document.body.dataset.lazyE2e="fail:"+e.message}})();'
].join('\n');
const entry='qa-r7-lazy-workbench.html';
fs.writeFileSync(path.join(dist,entry),base.replace('</head>','<script>window.fetch=async()=>{throw Error("offline test")};</script></head>').replace('</body>','<script>'+script+'</script></body>'));
try{
 const result=spawnSync(chrome,[
 '--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--virtual-time-budget=30000',
 '--window-size=1440,900','--user-data-dir='+path.join(temp,'r7-lazy-episode'),'--dump-dom',
 'http://127.0.0.1:'+port+'/'+entry
 ],{encoding:'utf8',timeout:50000,maxBuffer:5000000});
 const marker=result.stdout?.match(/data-lazy-e2e="([^"]+)"/)?.[1]||'none';
 if(marker!=='pass'){
  fs.writeFileSync(path.join(temp,'r7-lazy-debug.txt'),(result.stdout||'').slice(-20000)+'\n'+(result.stderr||'').slice(-2200));
  throw Error('Episode single-module browser load failed: '+marker);
 }
 console.log('PASS 首页未预加载详细 Episode，进入故事制作才加载 1/11 作品模块');
}finally{server.kill();}
