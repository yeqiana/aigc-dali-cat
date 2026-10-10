import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const dist = path.resolve('dist');
const index = fs.readFileSync(path.join(dist, 'index.html'), 'utf8');
const chrome = process.env.CHROME_PATH || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const reports = path.resolve('../.storyos-tmp/ui-qa');
assert.ok(fs.existsSync(chrome), '此测试需要本机 Chrome 或 CHROME_PATH');
fs.mkdirSync(reports, { recursive: true });
const first = {episode_id:'workflow-first',title:'分页作品甲',episode_ref:'EP-A',production_stage:'IDEA_LOCKED',state_source:'API'};
const second = {episode_id:'workflow-second',title:'分页作品乙',episode_ref:'EP-B',production_stage:'STORYBOARD_LOCKED',state_source:'API'};
const nav = "let menu=null;for(let i=0;i<80&&!menu;i++){menu=[...document.querySelectorAll('nav button')].find(b=>b.textContent.trim()==='工作流');if(!menu)await new Promise(r=>setTimeout(r,150))}if(!menu)throw Error('navigation');menu.click();";
const api = [
  'window.__nextPages=0;',
  'window.fetch=async input=>{',
  "const url=String(input);if(!url.includes('/runtime/statuses'))throw Error('non-read request');",
  "const offset=Number(new URL(url,'http://localhost').searchParams.get('offset')||0);",
  'if(offset===1)window.__nextPages++;',
  'const rows=offset===0?['+JSON.stringify(first)+']:offset===1?['+JSON.stringify(second)+']:[];',
  'await new Promise(r=>setTimeout(r,70));',
  'return new Response(JSON.stringify({code:"OK",data:{items:rows,total:2,count:rows.length,limit:100,offset,has_more:offset===0,errors:[]}}),{status:200,headers:{"Content-Type":"application/json"}});',
  '};'
].join('\n');
const testPagination = [
  '(async()=>{try{',
  'await new Promise(r=>setTimeout(r,700));',nav,
  'await new Promise(r=>setTimeout(r,900));',
  "const load=[...document.querySelectorAll('main button')].find(b=>b.textContent.trim()==='加载更多');",
  "if(!load)throw Error('load more');load.click();load.click();",
  'await new Promise(r=>setTimeout(r,1200));',
  "const text=document.querySelector('main')?.textContent||'';",
  "document.body.dataset.qa=(text.includes('分页作品甲')&&text.includes('分页作品乙')&&text.includes('已载入 2 / 2 条')&&window.__nextPages===1)?'pass':'fail:pagination';",
  "}catch(e){document.body.dataset.qa='fail:'+e.message}})();"
].join('\n');
const offlineApi = "window.fetch=async()=>{throw Error('offline fixture')};";
const testOffline = [
  '(async()=>{try{',
  'await new Promise(r=>setTimeout(r,700));',nav,
  'await new Promise(r=>setTimeout(r,1200));',
  "document.body.dataset.qa=(document.querySelector('main')?.textContent||'').includes('无法连接 Platform API')?'pass':'fail:offline';",
  "}catch(e){document.body.dataset.qa='fail:'+e.message}})();"
].join('\n');

function run(name, mock, body) {
  const html = index.replace('</head>', '<script>'+mock+'</script></head>')
    .replace('</body>', '<script>'+body+'</script></body>');
  const entry = path.join(dist, 'qa-r4-'+name+'.html');
  fs.writeFileSync(entry, html);
  const result = spawnSync(chrome, [
    '--headless=new','--no-sandbox','--disable-gpu','--disable-web-security',
    '--disable-dev-shm-usage','--allow-file-access-from-files','--virtual-time-budget=20000',
    '--window-size=1440,900','--user-data-dir='+path.join(reports, 'r4-'+name),
    '--dump-dom',pathToFileURL(entry).href
  ],{encoding:'utf8',timeout:40000,maxBuffer:4000000});
  const marker = (result.stdout||'').match(/data-qa="([^"]+)"/)?.[1] || 'missing';
  if(marker!=='pass'){
    fs.writeFileSync(path.join(reports,name+'-debug.txt'),(result.stdout||'').slice(-16000)+'\n'+(result.stderr||'').slice(-3000));
    throw Error(name+' failed: '+marker);
  }
  console.log('PASS '+name);
}
run('workflow-pages', api, testPagination);
run('workflow-offline', offlineApi, testOffline);
console.log('Workflow browser acceptance 2/2');
