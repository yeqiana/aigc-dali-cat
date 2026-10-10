import assert from 'node:assert/strict';

const target=process.env.STORYOS_READONLY_API_URL || 'http://127.0.0.1:8080';
const url=new URL(target);
if (!['127.0.0.1','localhost','[::1]'].includes(url.hostname) || url.protocol!=='http:') {
  console.error('只允许对本机 HTTP 端口进行只读 API 探测，不接受远程/生产 URL');
  process.exit(2);
}
if (url.username || url.password || url.pathname!=='/' || url.search || url.hash) {
  console.error('只允许无鉴权凭据的服务根地址');
  process.exit(2);
}
async function request(path) {
  const controller=new AbortController();
  const timeout=setTimeout(()=>controller.abort(),4500);
  try{
    const response=await fetch(new URL(path,url),{method:'GET',signal:controller.signal,headers:{Accept:'application/json'},cache:'no-store'});
    const body=await response.json().catch(()=>null);
    return {response,body};
  }finally{clearTimeout(timeout)}
}
try {
  const health=await request('healthz');
  assert.equal(health.response.status,200,'healthz 必须返回 HTTP 200');
  assert.equal(health.body?.code,'OK','响应必须使用已定义信封');
  const statuses=await request('api/v1/runtime/statuses?limit=1&offset=0');
  if(statuses.response.status===503){
    assert.equal(statuses.body?.code,'CAPABILITY_NOT_CONFIGURED');
    console.log('READONLY_API_UNCONFIGURED: 平台 HTTP 可达，但 Runtime 查询能力尚未配置');
  }else{
    assert.equal(statuses.response.status,200);
    assert.equal(statuses.body?.code,'OK');
    assert.ok(Array.isArray(statuses.body?.data?.items));
    assert.ok(Number.isSafeInteger(statuses.body?.data?.total));
    console.log('READONLY_API_READY: healthz / Runtime statuses 契约已通过，返回记录数',statuses.body.data.items.length,'总数',statuses.body.data.total);
  }
}catch(e){
  console.error('READONLY_API_UNAVAILABLE:',e instanceof Error ? e.message : 'unknown');
  process.exitCode=1;
}
