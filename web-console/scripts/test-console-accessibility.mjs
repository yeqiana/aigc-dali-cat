import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { spawn, spawnSync } from 'node:child_process';

const dist=path.resolve('dist'),html=fs.readFileSync(path.join(dist,'index.html'),'utf8');
const chrome=process.env.CHROME_PATH||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
assert.ok(fs.existsSync(chrome),'Chrome binary missing');
const screenshots=path.resolve('../.storyos-tmp/ui-qa');
fs.mkdirSync(screenshots,{recursive:true});
const server=spawn(process.execPath,['scripts/test-static-server.mjs',dist],{stdio:['ignore','pipe','pipe']});
const port=await new Promise((resolve,reject)=>{
  let value='';
  const timer=setTimeout(()=>reject(Error('HTTP smoke server not ready')),10000);
  server.stdout.on('data',data=>{
    value+=data.toString();
    const m=value.match(/READY (\d+)/);
    if(m){clearTimeout(timer);resolve(Number(m[1]));}
  });
  server.on('error',reject);
});
const scenarios=[{name:'overview',menu:null,title:'工作台'},{name:'monitor',menu:'生产监控',title:'生产监控'},{name:'workflow',menu:'工作流',title:'生产流程'}];
try {
  for(const scenario of scenarios) {
    const scenarioCode=JSON.stringify(scenario);
    const inline=[
      '(async()=>{try{',
      'const config='+scenarioCode+';',
      'const wait=ms=>new Promise(r=>setTimeout(r,ms));',
      'let nav=null;',
      "for(let i=0;i<100&&!nav;i++){nav=document.querySelector('nav[aria-label=\"主要页面\"]');if(!nav)await wait(100);}",
      "if(!nav)throw Error('sidebar missing accessible nav');",
      'if(config.menu){',
      "const button=[...nav.querySelectorAll('button')].find(b=>b.textContent.trim()===config.menu);",
      "if(!button)throw Error('navigation item missing');button.click();",
      '}',
      'let main=null;',
      "for(let i=0;i<160;i++){main=document.querySelector('main');if(main?.querySelector('h1')?.textContent.trim()===config.title)break;await wait(100);}",
      "if(main?.querySelector('h1')?.textContent.trim()!==config.title)throw Error('destination route title not loaded');",
      "if(!nav.querySelector('button'))throw Error('sidebar no focusable controls');",
      "const unnamed=[...main.querySelectorAll('button')].filter(b=>!b.textContent?.trim()&&!b.getAttribute('aria-label')&&!b.getAttribute('title')&&!b.querySelector('[aria-label],[title]'));",
      "if(unnamed.length)throw Error('unlabelled button count='+unnamed.length);",
      "const width=document.documentElement.scrollWidth;const viewport=window.innerWidth;",
      "if(width>viewport+3)throw Error('horizontal overflow '+width+'/'+viewport);",
      "document.body.dataset.a11yCheck='pass';",
      "}catch(e){document.body.dataset.a11yCheck='fail:'+e.message}})();"
    ].join('\n');
    const file=path.join(dist,'qa-r6-access-'+scenario.name+'.html');
    fs.writeFileSync(file,html.replace('</head>',"<script>window.fetch=async()=>{throw Error('offline fixture')};</script></head>")
      .replace('</body>','<script>'+inline+'</script></body>'));
    const result=spawnSync(chrome,[
      '--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
      '--hide-scrollbars','--virtual-time-budget=32000',
      '--window-size=1366,900',
      '--user-data-dir='+path.join(screenshots,'r6-a11y-'+scenario.name),
      '--dump-dom','http://127.0.0.1:'+port+'/qa-r6-access-'+scenario.name+'.html'
    ],{encoding:'utf8',timeout:55000,maxBuffer:5000000});
    const marker=result.stdout?.match(/data-a11y-check="([^"]+)"/)?.[1]||'missing';
    if(marker!=='pass'){
      fs.writeFileSync(path.join(screenshots,'r6-a11y-'+scenario.name+'.txt'),(result.stdout||'').slice(-17000)+'\n'+(result.stderr||'').slice(-2000));
      throw Error(scenario.name+' a11y failed: '+marker);
    }
    console.log('PASS '+scenario.name+'：主标题、侧栏导航、按钮名称、1366px 无水平溢出');
  }
  console.log('StoryOS browser basic accessibility smoke 3/3');
}finally{server.kill();}
