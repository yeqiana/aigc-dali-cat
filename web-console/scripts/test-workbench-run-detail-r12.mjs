import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
const chrome=process.env.CHROME_PATH||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const base=new URL(process.env.STORYOS_LOCAL_CONSOLE_URL||'http://127.0.0.1:3104/');
assert.equal(base.hostname,'127.0.0.1');
assert.ok(fs.existsSync(chrome),'Chrome missing');
const api=await fetch(new URL('/api/v1/runtime/statuses?limit=100&offset=0',base));
assert.equal(api.status,200);
const json=await api.json();
assert.ok(json.data?.items?.length>=1&&json.data.items.every(x=>x.state_source==='local_workspace_episode_state_file'));
const out=path.resolve('../.storyos-tmp/ui-qa/r12');
fs.mkdirSync(out,{recursive:true});
const html=fs.readFileSync('index.html','utf8');
const scenarios=[{name:'workbench',menu:'故事制作',width:1366},{name:'run-detail',menu:'生产监控',width:1440}];
try {
 for(const c of scenarios){
  const script=[
   '(async()=>{try{',
   'const config='+JSON.stringify(c)+';',
   'const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));',
   'let nav;for(let i=0;i<150&&!nav;i++){nav=document.querySelector(\'nav[aria-label="主要页面"]\');if(!nav)await sleep(100)}',
   'if(!nav)throw Error("no navigation");',
   'const link=[...nav.querySelectorAll("button")].find(el=>el.textContent?.trim()===config.menu);if(!link)throw Error("no menu");link.click();',
   'if(config.name==="workbench"){',
   ' let ready=false;for(let i=0;i<200;i++){const main=document.querySelector("main");const value=main?.textContent||"";if(value.includes("制作进展")&&value.includes("制作与审核记录")){ready=true;break}if(value.includes("历史作品详细证据加载失败")){ready=true;break}await sleep(100)}',
   ' if(!ready)throw Error("workbench did not settle");',
   '}else{',
   ' let row;for(let i=0;i<200&&!row;i++){row=document.querySelector(\'#storyos-production-monitor-view table tbody tr[role="button"],#storyos-production-monitor-view table tbody tr[class*="cursor-pointer"]\');if(!row)await sleep(100)}',
   ' if(!row)throw Error("run history table row missing");row.click();',
   ' let ready=false;for(let i=0;i<240;i++){const txt=document.querySelector("main")?.textContent||"";if(txt.includes("历史工作区 Run 快照")&&txt.includes("心跳未验证")){ready=true;break}await sleep(100)}',
   ' if(!ready)throw Error("history Run detail missing truthful notice");',
   ' if((document.querySelector("main")?.textContent||"").includes("Worker-01"))throw Error("fake worker fallback");',
   '}',
   'const root=document.documentElement;const maxWidth=root.scrollWidth;if(maxWidth>innerWidth+4)throw Error("page horizontally overflows "+maxWidth+"/"+innerWidth);',
   'const main=document.querySelector("main");const unnamed=[...main.querySelectorAll("button")].filter(x=>!x.textContent?.trim()&&!x.getAttribute("aria-label")&&!x.getAttribute("title"));if(unnamed.length)throw Error("unnamed actions "+unnamed.length);',
   'document.body.dataset.r12Status="pass";',
   '}catch(e){document.body.dataset.r12Status="fail:"+e.message;}})();'
  ].join('\n');
  const name='qa-r12-'+c.name+'.html';
  fs.writeFileSync(name,html.replace('</body>','<script>'+script+'</script></body>'));
  const args=['--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--hide-scrollbars','--virtual-time-budget=29000','--window-size='+c.width+',900','--user-data-dir='+path.join(out,'profile-'+c.name)];
  const url=new URL('/'+name,base).href;
  const dom=spawnSync(chrome,[...args,'--dump-dom',url],{encoding:'utf8',timeout:62000,maxBuffer:6000000});
  const mark=dom.stdout?.match(/data-r12-status="([^"]+)"/)?.[1]||'missing';
  if(mark!=='pass'){
   fs.writeFileSync(path.join(out,'failure-'+c.name+'.txt'),(dom.stdout||'').slice(-14000)+'\n'+(dom.stderr||'').slice(-1000));
   throw Error(c.name+' '+mark);
  }
  const file=path.join(out,'storyos-'+c.name+'.png');
  const shot=spawnSync(chrome,[...args,'--screenshot='+file,url],{encoding:'utf8',timeout:62000});
  assert.ok(fs.existsSync(file)&&fs.statSync(file).size>8000,'Screenshot failed '+c.name+' '+shot.stderr?.slice(-200));
  console.log('PASS '+c.name+' deep navigation, real source, accessible actions, no overflow, '+fs.statSync(file).size+'B');
 }
 console.log('R12_BROWSER_DEEP_VIEWS_2_OF_2_PASS');
} finally {
 for(const c of scenarios)try{fs.unlinkSync('qa-r12-'+c.name+'.html')}catch{}
}
