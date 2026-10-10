import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

// 离线 Chromium 测试。主动封禁 fetch 以验证无后端时各业务页面不伪造在线状态。
const dist = path.resolve('dist');
const index = fs.readFileSync(path.join(dist, 'index.html'), 'utf8');
const chrome = process.env.CHROME_PATH || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
assert.ok(fs.existsSync(chrome), '需要本机 Chrome 或环境变量 CHROME_PATH');
const out = path.resolve('../.storyos-tmp/ui-qa');
fs.mkdirSync(out, {recursive:true});
const scenarios=[
  {name:'home',nav:null,expected:'Platform API 未连接'},
  {name:'monitor',nav:'生产监控',expected:'无法连接 Platform API'},
  {name:'workflow',nav:'工作流',expected:'无法连接 Platform API'},
  {name:'agents',nav:'Agents',expected:'Agent 能力尚未接通'},
  {name:'story',nav:'故事制作',expected:'制作与审核记录'}
];
const network="window.fetch=async()=>{throw new Error('test offline: no backend access')};";
for(const scenario of scenarios){
  const payload=JSON.stringify(scenario);
  const code=[
    '(async()=>{try{',
    'const test='+payload+';',
    'const wait=ms=>new Promise(r=>setTimeout(r,ms));',
    'let nav=null;',
    'for(let i=0;i<100&&!nav;i++){',
    " nav=document.querySelector('nav[aria-label=\"主要页面\"]');",
    ' if(!nav) await wait(100);',
    '}',
    "if(!nav)throw Error('sidebar failed to mount');",
    'if(test.nav){',
    'const button=[...nav.querySelectorAll("button")].find(b=>b.textContent.trim()===test.nav);',
    "if(!button)throw Error('missing menu: '+test.nav);",
    'button.click();',
    '}',
    'let result=false;',
    'for(let i=0;i<280;i++){',
    " const main=document.querySelector('main');",
    ' result=Boolean(main?.textContent.includes(test.expected));',
    ' if(result)break;',
    ' await wait(100);',
    '}',
    "document.body.dataset.consoleQa=result?'pass':'fail:expected-content';",
    '}catch(e){document.body.dataset.consoleQa="fail:"+e.message}})();'
  ].join('\n');
  const file=path.join(dist,'qa-r5-'+scenario.name+'.html');
  fs.writeFileSync(file,index.replace('</head>','<script>'+network+'</script></head>').replace('</body>','<script>'+code+'</script></body>'));
  const run=spawnSync(chrome,[
    '--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
    '--disable-web-security','--allow-file-access-from-files','--virtual-time-budget=45000',
    '--window-size=1440,900','--user-data-dir='+path.join(out,'r5-qa-'+scenario.name),
    '--dump-dom',pathToFileURL(file).href
  ],{encoding:'utf8',timeout:70000,maxBuffer:4000000});
  const marker=(run.stdout||'').match(/data-console-qa="([^"]+)"/)?.[1]||'missing';
  if(marker!=='pass'){
    fs.writeFileSync(path.join(out,'r5-'+scenario.name+'-failure.txt'),
      (run.stdout||'').slice(-15000)+'\n'+(run.stderr||'').slice(-3000));
    throw Error(scenario.name+' browser smoke failed: '+marker);
  }
  console.log('PASS 离线页面 '+scenario.name);
}
console.log('StoryOS 浏览器离线真实 DOM 验收 5/5');
