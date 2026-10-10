import React from 'react';
import {Alert, Segmented, Tabs} from 'antd';
import {Palette, SlidersHorizontal} from 'lucide-react';
import type {ThemeMode} from '../../types';

interface SettingsViewProps{
 currentTheme?:ThemeMode;
 onThemeChange?:(theme:ThemeMode)=>void;
}
export const SettingsView:React.FC<SettingsViewProps>=({currentTheme='dark',onThemeChange})=>{
 return <section id="codex-appearance-settings-view" className="w-full min-w-0 space-y-5 pb-6 text-[var(--text-primary)]">
  <header className="border-b border-[var(--border-subtle)] pb-4">
   <h1 className="os-page-heading">系统设置</h1>
   <p className="mt-1.5 text-[13px] text-[var(--text-secondary)]">仅展示能验证的工作区偏好与配置状态</p>
  </header>
  <Tabs size="small" defaultActiveKey="appearance" items={[
   {key:'appearance',label:<span className="inline-flex items-center gap-1.5"><Palette size={14}/>外观设置</span>,
    children:<div className="max-w-[1000px] space-y-5">
     <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--border-subtle)] py-3">
      <div><h2 className="os-section-heading">界面主题</h2><p className="mt-1 text-[13px] text-[var(--text-secondary)]">即时切换，沿用现有浏览器本地偏好</p></div>
      <Segmented aria-label="界面主题" value={currentTheme} onChange={value=>onThemeChange?.(value as ThemeMode)}
       options={[{value:'dark',label:'深色'},{value:'light',label:'浅色'},{value:'light-gradient',label:'浅色渐变'}]}/>
     </div>
     <p className="text-[12px] leading-5 text-[var(--text-secondary)]">StoryOS 使用统一主题变量，表格、分页及菜单随主题自动适配。</p>
     <Alert type="info" showIcon message="其他外观参数尚未接入可验证的持久化设置接口，因此不提供会误导为已生效的模拟开关。" />
    </div>},
   {key:'pipeline',label:<span className="inline-flex items-center gap-1.5"><SlidersHorizontal size={14}/>生产管线</span>,
    children:<div className="space-y-4">
     <h2 className="text-[13px] font-semibold">Runtime 配置权限</h2>
     <Alert type="warning" showIcon message="当前 Console 没有已授权的生产配置读写接口。" description="模型、画幅、批次、并发等配置应由受控 StoryOS Runtime 提供权威数据；此处不会展示虚假的 RUNNING 状态，也不会用本地表单冒充设置成功。"/>
     <div className="border-y border-[var(--border-subtle)] py-3 text-[12px] text-[var(--text-secondary)]">
      <div className="flex justify-between gap-3"><span>生图模型 / 质量 / 画幅</span><span>等待权威配置接口</span></div>
      <div className="mt-3 flex justify-between gap-3"><span>批次与并发限制</span><span>等待权威配置接口</span></div>
     </div>
    </div>}
  ]}/>
 </section>;
};
