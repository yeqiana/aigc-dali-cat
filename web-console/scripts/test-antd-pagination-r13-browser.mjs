import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
const chrome=process.env.CHROME_PATH||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const base=process.env.STORYOS_LOCAL_CONSOLE_URL||'http://127.0.0.1:3105/';
const url=new URL(base);
assert.equal(url.hostname,'127.0.0.1');
const api=await fetch(new URL('/api/v1/runtime/statuses?limit=100&offset=0',url));
assert.equal(api.status,200);
const json=await api.json();
assert.ok(json.data?.items?.length>10,'分页验收需至少 11 条本机真实作品记录');
const html=fs.readFileSync('index.html','utf8');
const dir=path.resolve('../.storyos-tmp/ui-qa/r13');fs.mkdirSync(dir,{recursive:true});
const cases=[
  {name:'home',menu:null,root:'#storyos-home-overview',width:1366},
  {name:'library',menu:'作品与项目',root:'#series-library-view',width:1440},
  {name:'workflow',menu:'工作流',root:'#storyos-workflow-workspace',width:1440},
  {name:'monitor',menu:'生产监控',root:'#storyos-production-monitor-view',width:1366},
];
try {
 for(const c of cases){
  const script=[
    '(async()=>{try{',
    'const c='+JSON.stringify(c)+';const sleep=ms=>new Promise(r=>setTimeout(r,ms));',
    'let nav;for(let i=0;i<140&&!nav;i++){nav=document.querySelector(\'nav[aria-label="主要页面"]\');if(!nav)await sleep(100)}',
    'if(!nav)throw Error("nav missing");',
    'if(c.menu){const b=[...nav.querySelectorAll("button")].find(x=>x.textContent?.trim()===c.menu);if(!b)throw Error("menu "+c.menu);b.click()}',
    'let region,pager;for(let i=0;i<240&&!pager;i++){region=document.querySelector(c.root);pager=region?.querySelector(".ant-pagination");if(!pager)await sleep(100)}',
    'if(!pager)throw Error("pager absent "+c.root);',
    'const next=pager.querySelector(".ant-pagination-next button");if(!next)throw Error("next button missing");',
    'if(next.disabled)throw Error("next disabled with more than 10 records");next.click();',
    'let active;for(let i=0;i<120;i++){active=pager.querySelector(".ant-pagination-item-active")?.textContent?.trim();if(active==="2")break;await sleep(100)}',
    'if(active!=="2")throw Error("page did not change");',
    'if(document.documentElement.scrollWidth>innerWidth+4)throw Error("horizontal overflow");',
    'document.body.dataset.r13Paging="pass";',
    '}catch(e){document.body.dataset.r13Paging="fail:"+e.message}})();'
  ].join('\n');
  const file='qa-r13-'+c.name+'.html';
  fs.writeFileSync(file,html.replace('</body>','<script>'+script+'</script></body>'));
  const cmd=['--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--virtual-time-budget=30000','--window-size='+c.width+',900','--user-data-dir='+path.join(dir,'profile-'+c.name)];
  const r=spawnSync(chrome,[...cmd,'--dump-dom',new URL('/'+file,url).href],{encoding:'utf8',timeout:70000,maxBuffer:5500000});
  const mark=r.stdout?.match(/data-r13-paging="([^"]+)"/)?.[1]||'missing';
  if(mark!=='pass'){
    fs.writeFileSync(path.join(dir,'failure-'+c.name+'.txt'),(r.stdout||'').slice(-18000)+'\n'+(r.stderr||'').slice(-1500));
    throw Error(c.name+' paging failed: '+mark);
  }
  console.log('PASS '+c.name+': Ant Design next page selected, source loaded, no viewport overflow');
 }
 console.log('R13 ANT DESIGN REAL DATA PAGINATION 4/4 PASS');
}finally{
 for(const c of cases)try{fs.unlinkSync('qa-r13-'+c.name+'.html')}catch{}
}
