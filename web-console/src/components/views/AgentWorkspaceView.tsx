import React, {useEffect,useState} from 'react';
import {Button,Table} from 'antd';
import type {TableColumnsType} from 'antd';
import {AlertCircle,RefreshCw,ShieldCheck} from 'lucide-react';
import {platformApi} from '../../api/platformApi';
import {MemorySearchPanel} from './MemorySearchPanel';
type AgentSummary={id:string;name:string;description:string;status:string;tools:string[]};
const asText=(v:unknown):string=>typeof v==='string'?v:'';
const asAgent=(value:unknown):AgentSummary|null=>{
 if(!value||typeof value!=='object')return null;
 const x=value as Record<string,unknown>;const id=asText(x.agent_id)||asText(x.id);
 const name=asText(x.name)||id;if(!name)return null;
 return {id:id||name,name,description:asText(x.description),status:asText(x.status),tools:Array.isArray(x.tools)?x.tools.filter((v):v is string=>typeof v==='string'):[]};
};
export const AgentWorkspaceView:React.FC=()=>{
 const [agents,setAgents]=useState<AgentSummary[]>([]);
 const [state,setState]=useState<'loading'|'available'|'error'>('loading');
 const [message,setMessage]=useState('');
 const [reload,setReload]=useState(0);
 useEffect(()=>{let alive=true;setState('loading');platformApi.agents().then(response=>{if(!alive)return;setAgents((response.items??[]).map(asAgent).filter((a):a is AgentSummary=>a!==null));setMessage('');setState('available');}).catch(()=>{if(!alive)return;setAgents([]);setMessage('Agent Registry 列表 API 尚不可用，不能据此推断在线 Agent 或启停状态。');setState('error');});return()=>{alive=false};},[reload]);
 const columns:TableColumnsType<AgentSummary>=[
  {title:'Agent',dataIndex:'name',key:'name',render:(v:string,x)=><div className="min-w-0"><div className="truncate text-[13px] font-semibold">{v}</div><div className="mt-1 truncate font-mono text-[11px] text-[var(--text-tertiary)]">{x.id}</div></div>},
  {title:'描述',dataIndex:'description',key:'description',ellipsis:true,render:(v:string)=><span className="text-[12px] text-[var(--text-secondary)]">{v||'暂无描述'}</span>},
  {title:'已披露工具',dataIndex:'tools',key:'tools',width:235,ellipsis:true,render:(v:string[])=><span className="text-[12px] text-[var(--text-secondary)]">{v.length?v.join('、'):'未披露'}</span>},
  {title:'状态',dataIndex:'status',key:'status',width:120,render:(v:string)=><span className="text-[12px]">{v||'未提供'}</span>}
 ];
 return <div className="w-full min-w-0 space-y-4 pb-6 text-[var(--text-primary)]">
  <header className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border-subtle)] pb-3"><div><h1 className="os-page-heading">Agents</h1><p className="mt-1 text-[12px] text-[var(--text-secondary)]">只读 Agent Registry · Skills / MCP 与 Memory 的能力不代表当前已连通</p></div><Button icon={<RefreshCw size={15}/>} disabled={state==='loading'} onClick={()=>setReload(v=>v+1)}>刷新</Button></header>
  {state==='error'&&<div role="alert" className="flex items-start gap-2 border-l-2 border-[var(--warning)] py-2 pl-3 text-[12px] text-[var(--text-secondary)]"><AlertCircle size={17} className="shrink-0 text-[var(--warning)]"/><span>{message}</span></div>}
  <section className="min-w-0 space-y-2"><div className="flex items-center justify-between gap-3"><h2 className="text-[14px] font-semibold">已注册 Agent</h2><span className="text-[12px] text-[var(--text-tertiary)]">{state==='available'? `${agents.length} 条已返回`:'接口状态待确认'}</span></div>
  <Table<AgentSummary> rowKey="id" size="small" columns={columns} dataSource={agents} loading={state==='loading'} scroll={{x:790}} pagination={{pageSize:15,showSizeChanger:true,pageSizeOptions:['15','30','50'],showTotal:n=>`共 ${n} 条`}} locale={{emptyText:state==='error'?'无法获取 Agent 数据':'暂无已注册 Agent'}}/>
  </section>
  <MemorySearchPanel/>
  <footer className="flex items-start gap-2 border-t border-[var(--border-subtle)] pt-3 text-[11px] text-[var(--text-tertiary)]"><ShieldCheck size={15} className="shrink-0"/>本页只读。创建、启动、停止 Agent 需要独立授权的后端 API。</footer>
 </div>;
};
