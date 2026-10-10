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
const dir=path.resolve('../.storyos-tmp/ui-qa/r11');fs.mkdirSync(dir,{recursive:true});
const html=fs.readFileSync('index.html','utf8');
assert.ok(html.includes('<title>StoryOS</title>'));
const icon=await fetch(new URL('/favicon.svg?v=2',url));assert.equal(icon.status,200);assert.ok((await icon.text()).includes('M42 18H28'));
const cases=[{name:'library',menu:'作品与项目',title:'作品与项目',width:1440},{name:'agents',menu:'Agents',title:'Agents',width:1366},{name:'logs',menu:'审计日志',title:'运行日志审计控制台',width:1440},{name:'settings',menu:'系统设置',title:'系统设置',width:1366}];
try{
 for(const c of cases){
  const script=[
   '(async()=>{try{',
   'const c='+JSON.stringify(c)+';const sleep=ms=>new Promise(r=>setTimeout(r,ms));',
   'let nav;', 'for(let i=0;i<150&&!nav;i++){nav=document.querySelector(\'nav[aria-label="主要页面"]\');if(!nav)await sleep(100)}',
   'if(!nav)throw Error("navigation inaccessible");',
   'if(c.menu){const b=[...document.querySelectorAll("button")].find(x=>x.textContent.trim()===c.menu);if(!b)throw Error("menu missing");b.click();}',
   'let main;',
   'for(let i=0;i<190;i++){main=document.querySelector("main");if(main?.querySelector("h1")?.textContent.trim()===c.title)break;await sleep(100)}',
   'if(main?.querySelector("h1")?.textContent.trim()!==c.title)throw Error("title wrong");',
   'if(!document.querySelector(\'[data-testid="local-real-evidence-banner"]\'))throw Error("source banner hidden");',
   'const px=document.documentElement.scrollWidth;', 'if(px>innerWidth+3)throw Error("horizontal overflow: "+px+"/"+innerWidth);',
   'const unnamed=[...main.querySelectorAll("button")].filter(b=>!b.textContent?.trim()&&!b.getAttribute("aria-label")&&!b.getAttribute("title")&&!b.querySelector("[aria-label],[title]"));if(unnamed.length)throw Error("unlabelled buttons "+unnamed.length);',
   'document.body.dataset.r11Visual="pass";',
   '}catch(e){document.body.dataset.r11Visual="fail:"+e.message}})();'
  ].join('\n');
  const name='qa-r11-'+c.name+'.html';
  fs.writeFileSync(name,html.replace('</body>','<script>'+script+'</script></body>'));
  const profile=path.join(dir,'profile-'+c.name);
  const cmd=['--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--hide-scrollbars','--virtual-time-budget=28000','--window-size='+c.width+',900','--user-data-dir='+profile];
  const check=spawnSync(chrome,[...cmd,'--dump-dom',new URL('/'+name,url).href],{encoding:'utf8',timeout:55000,maxBuffer:5000000});
  const mark=check.stdout?.match(/data-r11-visual="([^"]+)"/)?.[1]||'missing';
  if(mark!=='pass'){
   fs.writeFileSync(path.join(dir,'failure-'+c.name+'.txt'),(check.stdout||'').slice(-15000)+'\n'+(check.stderr||'').slice(-1500));
   throw Error('R11 '+c.name+' UX '+mark);
  }
  const image=path.join(dir,'storyos-'+c.name+'.png');
  const shot=spawnSync(chrome,[...cmd,'--screenshot='+image,new URL('/'+name,url).href],{encoding:'utf8',timeout:55000});
  assert.ok(fs.existsSync(image)&&fs.statSync(image).size>9000,'Screenshot failed '+c.name+' '+shot.stderr?.slice(-250));
  console.log('PASS '+c.name+' title, real-data source, accessible actions, no horizontal overflow; screenshot '+fs.statSync(image).size+' B');
 }
 console.log('PASS R11 REAL DATA CHROME VISUAL 4/4');
}finally{
 for(const c of cases)try{fs.unlinkSync('qa-r11-'+c.name+'.html')}catch{}
}
