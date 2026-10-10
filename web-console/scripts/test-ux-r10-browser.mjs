import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
const chrome=process.env.CHROME_PATH||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const base=process.env.STORYOS_LOCAL_CONSOLE_URL||'http://127.0.0.1:3102/';
assert.ok(fs.existsSync(chrome));
const url=new URL(base);
assert.equal(url.protocol,'http:');assert.equal(url.hostname,'127.0.0.1');
const data=await (await fetch(new URL('/api/v1/runtime/statuses?limit=100&offset=0',url))).json();
assert.ok(data.code==='OK'&&data.data.total>0);
assert.ok(data.data.items.every(x=>x.state_source==='local_workspace_episode_state_file'));
const dir=path.resolve('../.storyos-tmp/ui-qa/r10');fs.mkdirSync(dir,{recursive:true});
const html=fs.readFileSync('index.html','utf8');
const cases=[
 {name:'overview',menu:null,title:'工作台',width:1440},
 {name:'monitor',menu:'生产监控',title:'生产监控',width:1440},
 {name:'workflow',menu:'工作流',title:'生产流程',width:1440},
 {name:'overview-1366',menu:null,title:'工作台',width:1366}
];
try{
 for(const c of cases){
  const script=[
   '(async()=>{try{',
   'const c='+JSON.stringify(c)+';const sleep=ms=>new Promise(r=>setTimeout(r,ms));',
   'let nav;', 'for(let i=0;i<150&&!nav;i++){nav=document.querySelector(\'nav[aria-label="主要页面"]\');if(!nav)await sleep(100)}',
   'if(!nav)throw Error("navigation inaccessible");',
   'if(c.menu){const b=[...nav.querySelectorAll("button")].find(x=>x.textContent.trim()===c.menu);if(!b)throw Error("menu missing");b.click();}',
   'let main;',
   'for(let i=0;i<190;i++){main=document.querySelector("main");if(main?.querySelector("h1")?.textContent.trim()===c.title)break;await sleep(100)}',
   'if(main?.querySelector("h1")?.textContent.trim()!==c.title)throw Error("title wrong");',
   'if(!document.querySelector(\'[data-testid="local-real-evidence-banner"]\'))throw Error("source banner hidden");',
   'let ready=false;',
   'for(let i=0;i<150;i++){const txt=main.textContent||"";if(c.menu==="生产监控"&&txt.includes("本机真实作品状态文件")){ready=true;break;}if(c.menu==="工作流"&&txt.includes("各作品所处阶段")&&txt.includes("标准七阶段")){ready=true;break;}if(!c.menu&&txt.includes("生产阶段记录")&&txt.includes("来自本机 episodes")){ready=true;break;}await sleep(100)}',
   'if(!ready)throw Error("page data not rendered");',
   'if(!main.querySelector("table,.os-data-row,[aria-label=\\\"项目概况\\\"]"))throw Error("primary data surface missing");',
   'const px=document.documentElement.scrollWidth;', 'if(px>innerWidth+3)throw Error("horizontal overflow: "+px+"/"+innerWidth);',
   'const unnamed=[...main.querySelectorAll("button")].filter(b=>!b.textContent?.trim()&&!b.getAttribute("aria-label")&&!b.getAttribute("title")&&!b.querySelector("[aria-label],[title]"));if(unnamed.length)throw Error("unlabelled buttons "+unnamed.length);',
   'document.body.dataset.r10Visual="pass";',
   '}catch(e){document.body.dataset.r10Visual="fail:"+e.message}})();'
  ].join('\n');
  const name='qa-r10-'+c.name+'.html';
  fs.writeFileSync(name,html.replace('</body>','<script>'+script+'</script></body>'));
  const profile=path.join(dir,'profile-'+c.name);
  const cmd=['--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--hide-scrollbars','--virtual-time-budget=28000','--window-size='+c.width+',900','--user-data-dir='+profile];
  const check=spawnSync(chrome,[...cmd,'--dump-dom',new URL('/'+name,url).href],{encoding:'utf8',timeout:55000,maxBuffer:5000000});
  const mark=check.stdout?.match(/data-r10-visual="([^"]+)"/)?.[1]||'missing';
  if(mark!=='pass'){
   fs.writeFileSync(path.join(dir,'failure-'+c.name+'.txt'),(check.stdout||'').slice(-15000)+'\n'+(check.stderr||'').slice(-1500));
   throw Error('R10 '+c.name+' UX '+mark);
  }
  const image=path.join(dir,'storyos-'+c.name+'.png');
  const shot=spawnSync(chrome,[...cmd,'--screenshot='+image,new URL('/'+name,url).href],{encoding:'utf8',timeout:55000});
  assert.ok(fs.existsSync(image)&&fs.statSync(image).size>9000,'Screenshot failed '+c.name+' '+shot.stderr?.slice(-250));
  console.log('PASS '+c.name+' title, real-data source, accessible actions, no horizontal overflow; screenshot '+fs.statSync(image).size+' B');
 }
 console.log('PASS R10 REAL DATA CHROME VISUAL 4/4');
}finally{
 for(const c of cases)try{fs.unlinkSync('qa-r10-'+c.name+'.html')}catch{}
}
