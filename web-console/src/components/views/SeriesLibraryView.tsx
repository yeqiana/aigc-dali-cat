import React, {useMemo, useState} from 'react';
import {Button, Input, Select, Table} from 'antd';
import type {TableColumnsType} from 'antd';
import {Clapperboard, Plus} from 'lucide-react';
import type {Episode} from '../../types';

interface Props { episodes:Episode[]; activeEpisode:Episode; onSelectEpisode:(episode:Episode)=>void; onGoToWorkbench:()=>void; onNewStoryClick:()=>void; }
const STAGES:Record<string,string> = {IDEA_LOCK:'创意锁定',STORYBOARD_LOCK:'分镜锁定',VISUAL_CALIBRATE:'视觉校准',PROD_APPROVED:'生产审核',READY_TO_PUBLISH:'待发布',PUBLISHED:'已发布',POST_MORTEM:'数据复盘'};
export const SeriesLibraryView: React.FC<Props> = ({episodes,activeEpisode,onSelectEpisode,onGoToWorkbench,onNewStoryClick}) => {
  const [query,setQuery]=useState('');
  const [stage,setStage]=useState('ALL');
  const [page,setPage]=useState(1);
  const [pageSize,setPageSize]=useState(15);
  const rows=useMemo(()=>episodes.filter(ep=>(stage==='ALL'||ep.currentStage===stage)&&`${ep.title} ${ep.code} ${ep.genre}`.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase())),[episodes,stage,query]);
  const open=(ep:Episode)=>{onSelectEpisode(ep);onGoToWorkbench();};
  const columns:TableColumnsType<Episode>=[
    {title:'作品',dataIndex:'title',key:'title',ellipsis:true,render:(_,ep)=><div className="flex min-w-0 items-center gap-3"><div className="flex h-12 w-10 shrink-0 items-center justify-center overflow-hidden rounded-[4px] bg-[var(--bg-elevated)]">{ep.coverImage?<img src={ep.coverImage} alt="" loading="lazy" className="h-full w-full object-cover"/>:<Clapperboard size={16} className="text-[var(--text-tertiary)]"/>}</div><div className="min-w-0"><Button type="link" size="small" onClick={()=>open(ep)} aria-label={`打开故事 ${ep.title}`} className="!h-auto !p-0 !font-semibold !text-[var(--text-primary)]"><span className="block max-w-[40vw] truncate text-left">{ep.title}</span></Button><p className="mt-1 truncate text-[11px] text-[var(--text-tertiary)]">{ep.code} · {ep.genre||'未分类'}</p></div></div>},
    {title:'生产阶段',dataIndex:'currentStage',key:'stage',width:148,render:(value:string)=><span className="text-[12px]">{STAGES[value]||value}</span>},
    {title:'帧进度',key:'frames',width:158,render:(_,ep)=>{const percent=ep.totalFrames?Math.round(ep.completedFrames/ep.totalFrames*100):0;return <div className="text-[12px] tabular-nums"><span>{ep.completedFrames}/{ep.totalFrames} 帧</span><div className="mt-1 h-1 w-24 rounded bg-[var(--border-normal)]"><div className="h-full rounded bg-[var(--info)]" style={{width:`${Math.min(100,Math.max(0,percent))}%`}}/></div></div>;}},
    {title:'更新时间',dataIndex:'updatedAt',key:'updatedAt',width:170,ellipsis:true,render:(value:string)=><span className="text-[12px] text-[var(--text-secondary)]">{value||'未知'}</span>},
    {title:'操作',key:'action',width:80,render:(_,ep)=><Button type="link" onClick={()=>open(ep)} size="small">打开</Button>},
  ];
  return <section id="series-library-view" className="w-full min-w-0 space-y-3 pb-6 text-[var(--text-primary)]">
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border-subtle)] pb-3">
      <div><h1 className="os-page-heading">作品与项目</h1><p className="mt-1 text-[12px] text-[var(--text-secondary)]">{episodes.length} 部作品 · 工作区快照</p></div>
      <Button type="primary" icon={<Plus size={15}/>} onClick={onNewStoryClick}>新建故事</Button>
    </header>
    <div className="flex flex-wrap items-center gap-2">
      <Input.Search aria-label="搜索故事标题、编号或类型" value={query} onChange={e=>{setQuery(e.target.value);setPage(1);}} placeholder="搜索作品 / 编号 / 类型" allowClear className="min-w-[220px] max-w-[440px] flex-1"/>
      <Select aria-label="筛选生产阶段" value={stage} onChange={v=>{setStage(v);setPage(1);}} className="w-[170px]" options={[{value:'ALL',label:'全部阶段'},...Object.entries(STAGES).map(([value,label])=>({value,label}))]}/>
      <span className="ml-auto text-[12px] text-[var(--text-tertiary)]">匹配 {rows.length} 条</span>
    </div>
    <Table<Episode> rowKey="id" size="small" columns={columns} dataSource={rows} scroll={{x:770}} rowClassName={ep=>ep.id===activeEpisode.id?'storyos-ant-selected':''}
      pagination={{current:Math.min(page,Math.max(1,Math.ceil(rows.length/pageSize))),pageSize,total:rows.length,showSizeChanger:true,pageSizeOptions:['10','15','30','50'],showTotal:(total,range)=>`${range[0]}–${range[1]} / ${total} 条`,onChange:(next,size)=>{setPage(next);setPageSize(size);}}}
      locale={{emptyText:'暂无符合条件的作品，请修改筛选条件'}}/>
    <p className="text-[11px] text-[var(--text-tertiary)]">阶段与帧数来源为当前工作区记录；生产执行、审核及发布结果应以正式 Runtime 证据为准。</p>
  </section>;
};