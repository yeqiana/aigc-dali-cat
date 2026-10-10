import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const web=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const base=process.env.STORYOS_LOCAL_CONSOLE_URL || 'http://127.0.0.1:3100/';
const url=new URL(base);
assert.ok(url.hostname==='127.0.0.1' && url.protocol==='http:', '只允许在本机 loopback 做 E2E');
const chrome=process.env.CHROME_PATH || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
assert.ok(fs.existsSync(chrome),'此浏览器验收需要 Chrome');
const output=path.resolve(web,'../.storyos-tmp/ui-qa');
fs.mkdirSync(output,{recursive:true});

const home=await fetch(url);
assert.equal(home.status,200);
assert.ok((await home.text()).includes('id="root"'));
const status=await fetch(new URL('/api/v1/runtime/statuses?limit=1&offset=0',url));
assert.equal(status.status,200);
const data=await status.json();
assert.equal(data.code,'OK');
assert.equal(data.data?.items?.[0]?.state_source,'isolated-test','必须是隔离测试 API');
const index=fs.readFileSync(path.join(web,'index.html'),'utf8');
const qa=path.join(web,'qa-r8-local-live.html');
const js=[
'(async()=>{try{',
'const sleep=ms=>new Promise(r=>setTimeout(r,ms));',
'let menu;',
'for(let i=0;i<160&&!menu;i++){menu=document.querySelector(\'nav[aria-label="主要页面"]\');if(!menu)await sleep(100);}',
'if(!menu)throw Error("sidebar");',
'const banner=document.querySelector(\'[data-testid="local-fixture-banner"]\');',
'if(!banner||!banner.textContent.includes("隔离测试"))throw Error("missing fixture banner");',
'let shown=false;',
'for(let i=0;i<140&&!shown;i++){shown=(document.querySelector("main")?.textContent||"").includes("真实 HTTP 联调样例");if(!shown)await sleep(100);}',
'if(!shown)throw Error("home fixture not visible");',
'const monitor=[...menu.querySelectorAll("button")].find(x=>x.textContent.trim()==="生产监控");',
'if(!monitor)throw Error("monitor navigation");monitor.click();',
'let stage=false;',
'for(let i=0;i<160&&!stage;i++){const t=document.querySelector("main")?.textContent||"";stage=t.includes("平台阶段证据")&&t.includes("本机隔离测试数据");if(!stage)await sleep(100);}',
'if(!stage)throw Error("monitor source not labeled");',
'const before=performance.getEntriesByType("resource").filter(x=>/runDetail\\d\\d/.test(x.name));',
'if(before.length)throw Error("Run 详情提前加载："+before.length);',
'const detailButton=[...document.querySelectorAll("main button")].find(x=>x.textContent.trim()==="详情");',
'if(!detailButton)throw Error("historical Run detail button missing");detailButton.click();',
'let loaded=false;',
'for(let i=0;i<160&&!loaded;i++){const resources=performance.getEntriesByType("resource").filter(x=>/runDetail\\d\\d/.test(x.name));loaded=resources.length===1;if(!loaded)await sleep(100);}',
'if(!loaded)throw Error("历史 Run 详情没有按需加载一份");',
'document.body.dataset.localLive="pass";',
'}catch(e){document.body.dataset.localLive="fail:"+e.message}})();'
].join('\n');
fs.writeFileSync(qa,index.replace('</body>','<script>'+js+'</script></body>'));
try {
 const result=spawnSync(chrome,[
   '--headless=new','--disable-gpu','--no-sandbox','--disable-dev-shm-usage',
   '--virtual-time-budget=30000','--window-size=1440,900',
   '--user-data-dir='+path.join(output,'r8-local-live-browser'),
   '--dump-dom',new URL('/qa-r8-local-live.html',url).href
 ],{encoding:'utf8',timeout:60000,maxBuffer:4500000});
 const marker=result.stdout?.match(/data-local-live="([^"]+)"/)?.[1]||'missing';
 if(marker!=='pass'){
  fs.writeFileSync(path.join(output,'r8-live-failure.txt'),(result.stdout||'').slice(-22000)+'\n'+(result.stderr||'').slice(-2000));
  throw Error('浏览器本地全链路失败: '+marker);
 }
 console.log('PASS Chrome 真正打开 Vite 本机页面、读取隔离 API、识别测试模式、导航监控并核验阶段证据');
 for(const w of [1366,1440]){
  const dest=path.join(output,'storyos-r8-local-'+w+'.png');
  const r=spawnSync(chrome,[
    '--headless=new','--disable-gpu','--no-sandbox','--disable-dev-shm-usage',
    '--virtual-time-budget=9000','--window-size='+w+',900',
    '--user-data-dir='+path.join(output,'r8-shot-'+w),
    '--screenshot='+dest,base
  ],{encoding:'utf8',timeout:50000});
  assert.ok(fs.existsSync(dest)&&fs.statSync(dest).size>4000,'截图失败 '+w+' '+r.stderr);
  console.log('PASS 实机浏览器截图 '+w+'px，'+fs.statSync(dest).size+' B');
 }
}finally{try{fs.unlinkSync(qa);}catch{}}
