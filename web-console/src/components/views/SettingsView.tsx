import React, { useState } from 'react';
import {
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Palette,
  Sliders,
  Terminal,
  Camera,
  Cpu
} from 'lucide-react';

export const SettingsView: React.FC = () => {
  // 顶层标签：外观参数 vs 管线与引擎
  const [activeSubTab, setActiveSubTab] = useState<'appearance' | 'pipeline'>('appearance');

  // 1. 主题选择: 'system' | 'light' | 'dark'
  const [themeMode, setThemeMode] = useState<'system' | 'light' | 'dark'>('dark');

  // 2. 主题详细配置
  const [darkThemePreset, setDarkThemePreset] = useState('Codex');
  const [accentColor, setAccentColor] = useState('默认');
  const bgColor = '#0B0D10';
  const fgColor = '#F1F3F5';
  const [uiFont, setUiFont] = useState('系统默认');
  const [uiFontWeight, setUiFontWeight] = useState('常规');
  const [contentFont, setContentFont] = useState('与界面字体相同');
  const [contentFontWeight, setContentFontWeight] = useState('常规');
  const [translucentSidebar, setTranslucentSidebar] = useState(true);
  const [contrastValue, setContrastValue] = useState(60);

  // 3. 偏好设置
  const [pointerCursor, setPointerCursor] = useState(true);
  const [reducedMotion, setReducedMotion] = useState<'system' | 'on' | 'off'>('system');
  const [uiFontSize, setUiFontSize] = useState('14');
  const [diffMarker, setDiffMarker] = useState<'color' | 'sign'>('color');

  // 4. 管线设置项
  const [modelFamily, setModelFamily] = useState('gpt-image-2');
  const [qualityLevel, setQualityLevel] = useState('high');
  const [maxBatchSize, setMaxBatchSize] = useState('5');
  const [maxConcurrency, setMaxConcurrency] = useState('3');
  const [aspectRatio, setAspectRatio] = useState('4:5 1080×1350');
  const [executionLayer] = useState('StoryOS Engine');

  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 2000);
  };

  const handleCopyTheme = () => {
    const config = {
      theme: themeMode,
      preset: darkThemePreset,
      accent: accentColor,
      background: bgColor,
      foreground: fgColor,
      contrast: contrastValue,
      translucentSidebar,
      uiFont,
      contentFont,
    };
    navigator.clipboard.writeText(JSON.stringify(config, null, 2));
    showToast('已复制 StoryOS 主题配置至剪贴板');
  };

  return (
    <div id="codex-appearance-settings-view" className="space-y-6 text-[var(--text-secondary)] font-sans select-none pb-24">
      {/* Toast 提示 */}
      {toastMessage && (
        <div className="storyos-elevated fixed top-12 right-8 z-50 px-4 py-2 text-xs font-semibold flex items-center gap-2 animate-in fade-in">
          <Check className="w-4 h-4 text-[var(--success)]" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* 顶部标签切换：外观参数 与 管线参数 */}
      <div className="flex items-center justify-between border-b border-[var(--border-normal)] pb-3">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setActiveSubTab('appearance')}
            className={`h-9 px-3 rounded-[var(--radius-md)] text-xs font-medium transition-colors cursor-pointer flex items-center gap-1.5 border ${
              activeSubTab === 'appearance'
                ? 'bg-[var(--primary-soft)] text-[var(--primary-hover)] border-[var(--border-normal)] font-semibold'
                : 'bg-[var(--bg-surface)] text-[var(--text-secondary)] border-transparent hover:text-[var(--text-primary)] hover:bg-[var(--bg-subtle)]'
            }`}
          >
            <Palette className="w-3.5 h-3.5" />
            <span>外观参数 (Appearance)</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveSubTab('pipeline')}
            className={`h-9 px-3 rounded-[var(--radius-md)] text-xs font-medium transition-colors cursor-pointer flex items-center gap-1.5 border ${
              activeSubTab === 'pipeline'
                ? 'bg-[var(--primary-soft)] text-[var(--primary-hover)] border-[var(--border-normal)] font-semibold'
                : 'bg-[var(--bg-surface)] text-[var(--text-secondary)] border-transparent hover:text-[var(--text-primary)] hover:bg-[var(--bg-subtle)]'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>StoryOS 管线与并发设置</span>
          </button>
        </div>

        <div className="text-[11px] font-mono text-[var(--text-tertiary)]">
          StoryOS UI Settings
        </div>
      </div>

      {activeSubTab === 'appearance' ? (
        <div className="space-y-8 max-w-3xl">
          {/* ===================== 1. 主题 (Theme) ===================== */}
          <section className="space-y-4">
            <h2 className="text-sm font-semibold text-[var(--text-primary)] tracking-wide">
              主题
            </h2>

            {/* 三大主题模式卡片 (系统 / 浅色 / 深色) */}
            <div className="grid grid-cols-3 gap-4">
              {/* 1.1 系统模式 */}
              <button
                type="button"
                onClick={() => {
                  setThemeMode('system');
                  showToast('已切换为「系统」模式');
                }}
                className={`group flex flex-col items-center gap-2 text-left cursor-pointer focus:outline-hidden ${
                  themeMode === 'system' ? 'text-[var(--text-primary)]' : 'text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]'
                }`}
              >
                <div className={`w-full aspect-[16/10] rounded-[var(--radius-md)] overflow-hidden border transition-colors relative flex ${
                  themeMode === 'system'
                    ? 'border-[var(--primary)]'
                    : 'border-[var(--border-normal)] hover:border-[var(--border-strong)]'
                }`}>
                  {/* 左半浅色 */}
                  <div className="w-1/2 h-full bg-[#8c8c8c] p-2 flex flex-col justify-end relative">
                    <div className="w-full h-4/5 bg-white/95 rounded-tl-[var(--radius-sm)] p-1.5 space-y-1">
                      <div className="w-12 h-1 bg-zinc-300 rounded-full" />
                      <div className="w-full h-0.5 bg-zinc-200 rounded-full" />
                      <div className="w-4/5 h-0.5 bg-zinc-200 rounded-full" />
                    </div>
                  </div>
                  {/* 右半深色 */}
                  <div className="w-1/2 h-full bg-[#262626] p-2 flex flex-col justify-end relative">
                    <div className="w-full h-4/5 bg-[#141414] rounded-tr-[var(--radius-sm)] p-1.5 space-y-1">
                      <div className="w-12 h-1 bg-zinc-600 rounded-full" />
                      <div className="w-full h-0.5 bg-zinc-700 rounded-full" />
                      <div className="w-4/5 h-0.5 bg-zinc-700 rounded-full" />
                    </div>
                  </div>
                </div>
                <span className="text-xs font-medium">系统</span>
              </button>

              {/* 1.2 浅色模式 */}
              <button
                type="button"
                onClick={() => {
                  setThemeMode('light');
                  showToast('已切换为「浅色」主题模式');
                }}
                className={`group flex flex-col items-center gap-2 text-left cursor-pointer focus:outline-hidden ${
                  themeMode === 'light' ? 'text-[var(--text-primary)]' : 'text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]'
                }`}
              >
                <div className={`w-full aspect-[16/10] rounded-[var(--radius-md)] overflow-hidden border transition-colors p-2 flex flex-col justify-end bg-[#e4e4e7] ${
                  themeMode === 'light'
                    ? 'border-[var(--primary)]'
                    : 'border-[var(--border-normal)] hover:border-[var(--border-strong)]'
                }`}>
                  <div className="w-full h-4/5 bg-white rounded-t-[var(--radius-sm)] p-2 space-y-1.5">
                    <div className="w-16 h-1.5 bg-zinc-300 rounded-full" />
                    <div className="w-full h-1 bg-zinc-200 rounded-full" />
                    <div className="w-5/6 h-1 bg-zinc-200 rounded-full" />
                    <div className="w-3/4 h-1 bg-zinc-200 rounded-full" />
                  </div>
                </div>
                <span className="text-xs font-medium">浅色</span>
              </button>

              {/* 1.3 深色模式 (当前默认选中态) */}
              <button
                type="button"
                onClick={() => {
                  setThemeMode('dark');
                  showToast('已切换为「深色」主题模式');
                }}
                className={`group flex flex-col items-center gap-2 text-left cursor-pointer focus:outline-hidden ${
                  themeMode === 'dark' ? 'text-[var(--text-primary)]' : 'text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]'
                }`}
              >
                <div className={`w-full aspect-[16/10] rounded-[var(--radius-md)] overflow-hidden border transition-colors p-2 flex flex-col justify-end bg-[#262626] ${
                  themeMode === 'dark'
                    ? 'border-[var(--primary)]'
                    : 'border-[var(--border-normal)] hover:border-[var(--border-strong)]'
                }`}>
                  <div className="w-full h-4/5 bg-[#13161b] rounded-t-[var(--radius-sm)] p-2 space-y-1.5">
                    <div className="w-16 h-1.5 bg-[#737d8a] rounded-full" />
                    <div className="w-full h-1 bg-[#2d333d] rounded-full" />
                    <div className="w-5/6 h-1 bg-[#2d333d] rounded-full" />
                    <div className="w-3/4 h-1 bg-[#2d333d] rounded-full" />
                  </div>
                </div>
                <span className="text-xs font-medium">深色</span>
              </button>
            </div>

            {/* Code Diff Preview (代码差异对比预览组件) */}
            <div className="rounded-[var(--radius-md)] border border-[var(--border-normal)] bg-[var(--bg-app)] font-mono text-[11px] overflow-hidden">
              <div className="grid grid-cols-2 divide-x divide-[var(--border-subtle)]">
                {/* 左列：红底差异 */}
                <div className="p-2 space-y-0.5 text-zinc-300 select-text">
                  <div className="flex items-center gap-2 text-zinc-500">
                    <span className="w-4 text-right">1</span>
                    <span><span className="text-[#a78bfa]">const</span> <span className="text-blue-400">themePreview</span>: <span className="text-emerald-400">ThemeConfig</span> = {'{'}</span>
                  </div>
                  <div className="flex items-center gap-2 bg-[#ef4444]/15 border-l-2 border-[#ef4444] px-1 py-0.2 text-red-200">
                    <span className="w-4 text-right text-red-400">2</span>
                    <span>  <span className="text-amber-300">surface</span>: <span className="text-emerald-300">"sidebar"</span>,</span>
                  </div>
                  <div className="flex items-center gap-2 bg-[#ef4444]/15 border-l-2 border-[#ef4444] px-1 py-0.2 text-red-200">
                    <span className="w-4 text-right text-red-400">3</span>
                    <span>  <span className="text-amber-300">accent</span>: <span className="text-emerald-300">"#2563eb"</span>,</span>
                  </div>
                  <div className="flex items-center gap-2 bg-[#ef4444]/15 border-l-2 border-[#ef4444] px-1 py-0.2 text-red-200">
                    <span className="w-4 text-right text-red-400">4</span>
                    <span>  <span className="text-amber-300">contrast</span>: <span className="text-sky-400">42</span>,</span>
                  </div>
                  <div className="flex items-center gap-2 text-zinc-500">
                    <span className="w-4 text-right">5</span>
                    <span>{'};'}</span>
                  </div>
                </div>

                {/* 右列：绿底差异 */}
                <div className="p-2 space-y-0.5 text-zinc-300 select-text">
                  <div className="flex items-center gap-2 text-zinc-500">
                    <span className="w-4 text-right">1</span>
                    <span><span className="text-[#a78bfa]">const</span> <span className="text-blue-400">themePreview</span>: <span className="text-emerald-400">ThemeConfig</span> = {'{'}</span>
                  </div>
                  <div className="flex items-center gap-2 bg-[#10b981]/15 border-l-2 border-[#10b981] px-1 py-0.2 text-emerald-200">
                    <span className="w-4 text-right text-emerald-400">2</span>
                    <span>  <span className="text-amber-300">surface</span>: <span className="text-emerald-300">"sidebar-elevated"</span>,</span>
                  </div>
                  <div className="flex items-center gap-2 bg-[#10b981]/15 border-l-2 border-[#10b981] px-1 py-0.2 text-emerald-200">
                    <span className="w-4 text-right text-emerald-400">3</span>
                    <span>  <span className="text-amber-300">accent</span>: <span className="text-emerald-300">"#0ea5e9"</span>,</span>
                  </div>
                  <div className="flex items-center gap-2 bg-[#10b981]/15 border-l-2 border-[#10b981] px-1 py-0.2 text-emerald-200">
                    <span className="w-4 text-right text-emerald-400">4</span>
                    <span>  <span className="text-amber-300">contrast</span>: <span className="text-sky-400">{contrastValue}</span>,</span>
                  </div>
                  <div className="flex items-center gap-2 text-zinc-500">
                    <span className="w-4 text-right">5</span>
                    <span>{'};'}</span>
                  </div>
                </div>
              </div>

              {/* 底部微型滚动箭头指示 */}
              <div className="px-2 py-1 bg-[var(--bg-workspace)] border-t border-[var(--border-subtle)] flex items-center justify-between text-[var(--text-disabled)]">
                <div className="flex items-center gap-1" aria-hidden="true">
                  <ChevronLeft className="w-3 h-3 text-[var(--text-disabled)]" />
                </div>
                <div className="flex items-center gap-1" aria-hidden="true">
                  <ChevronRight className="w-3 h-3 text-[var(--text-disabled)]" />
                </div>
              </div>
            </div>

            {/* 深色主题参数：使用 StoryOS Design Token，不创建竞争色板。 */}
            <div className="bg-[var(--bg-surface)] border border-[var(--border-normal)] rounded-[var(--radius-lg)] p-4 divide-y divide-[var(--border-subtle)] text-xs">
              {/* 1. 深色主题选择与动作 */}
              <div className="py-3 first:pt-0 flex items-center justify-between">
                <span className="text-[var(--text-primary)] font-medium">深色主题</span>
                <div className="flex items-center gap-2.5">
                  <button
                    type="button"
                    disabled
                    title="主题导入尚未接入文件解析能力"
                    className="text-[var(--text-disabled)] cursor-not-allowed"
                  >
                    导入
                  </button>
                  <button
                    type="button"
                    onClick={handleCopyTheme}
                    className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
                  >
                    复制主题
                  </button>
                  <div className="px-1.5 py-0.5 rounded-[var(--radius-xs)] bg-[var(--bg-workspace)] text-[var(--text-secondary)] text-[10px] font-mono border border-[var(--border-normal)]">
                    Aa
                  </div>
                  <div className="relative">
                    <select
                      value={darkThemePreset}
                      onChange={(e) => {
                        setDarkThemePreset(e.target.value);
                        showToast(`已应用主题: ${e.target.value}`);
                      }}
                      className="appearance-none storyos-control h-8 px-3 pr-7 text-xs font-mono outline-hidden cursor-pointer"
                    >
                      <option value="Codex">Codex</option>
                      <option value="GitHub Dark">GitHub Dark</option>
                      <option value="Vesper">Vesper</option>
                      <option value="One Dark Pro">One Dark Pro</option>
                    </select>
                    <ChevronDown className="w-3 h-3 text-[var(--text-tertiary)] absolute right-2 top-2.5 pointer-events-none" />
                  </div>
                </div>
              </div>

              {/* 2. 强调色 */}
              <div className="py-3 flex items-center justify-between">
                <span className="text-[var(--text-primary)] font-medium">强调色</span>
                <div className="relative">
                  <select
                    value={accentColor}
                    onChange={(e) => {
                      setAccentColor(e.target.value);
                      showToast(`强调色已设为: ${e.target.value}`);
                    }}
                    className="appearance-none storyos-control h-8 px-3 pr-7 text-xs outline-hidden cursor-pointer"
                  >
                    <option value="默认">默认</option>
                    <option value="纯白高亮">纯白高亮</option>
                    <option value="经典蓝">经典蓝 (#2563eb)</option>
                    <option value="翡翠绿">翡翠绿 (#10b981)</option>
                  </select>
                  <ChevronDown className="w-3 h-3 text-[var(--text-tertiary)] absolute right-2 top-2.5 pointer-events-none" />
                </div>
              </div>

              {/* 3. 背景颜色 */}
              <div className="py-3 flex items-center justify-between">
                <span className="text-[var(--text-primary)] font-medium">背景</span>
                <div
                  className="storyos-control h-8 px-3 font-mono text-xs flex items-center gap-2"
                  aria-label="背景色锁定为 #0B0D10"
                >
                  <span className="w-2.5 h-2.5 rounded-full border border-[var(--border-strong)] bg-[var(--bg-app)]" />
                  <span>{bgColor}</span>
                </div>
              </div>

              {/* 4. 前景颜色 */}
              <div className="py-3 flex items-center justify-between">
                <span className="text-[var(--text-primary)] font-medium">前景</span>
                <div
                  className="storyos-control h-8 px-3 font-mono font-semibold text-xs flex items-center gap-2"
                  aria-label="前景色锁定为 #F1F3F5"
                >
                  <span className="w-2.5 h-2.5 rounded-full border border-[var(--border-strong)] bg-[var(--text-primary)]" />
                  <span>{fgColor}</span>
                </div>
              </div>

              {/* 5. UI 字体 */}
              <div className="py-3 flex items-center justify-between">
                <span className="text-[var(--text-primary)] font-medium">UI 字体</span>
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <select
                      value={uiFont}
                      onChange={(e) => setUiFont(e.target.value)}
                      className="appearance-none storyos-control h-8 px-3 pr-7 text-xs outline-hidden cursor-pointer"
                    >
                      <option value="系统默认">系统默认</option>
                      <option value="Inter">Inter</option>
                      <option value="PingFang SC">PingFang SC</option>
                      <option value="JetBrains Mono">JetBrains Mono</option>
                    </select>
                    <ChevronDown className="w-3 h-3 text-[var(--text-tertiary)] absolute right-2 top-2.5 pointer-events-none" />
                  </div>
                  <div className="relative">
                    <select
                      value={uiFontWeight}
                      onChange={(e) => setUiFontWeight(e.target.value)}
                      className="appearance-none storyos-control h-8 px-2.5 pr-6 text-xs outline-hidden cursor-pointer"
                    >
                      <option value="常规">常规</option>
                      <option value="中粗">中粗</option>
                      <option value="粗体">粗体</option>
                    </select>
                    <ChevronDown className="w-3 h-3 text-[var(--text-tertiary)] absolute right-2 top-2.5 pointer-events-none" />
                  </div>
                </div>
              </div>

              {/* 6. 内容字体 */}
              <div className="py-3 flex items-center justify-between">
                <span className="text-[var(--text-primary)] font-medium">内容字体</span>
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <select
                      value={contentFont}
                      onChange={(e) => setContentFont(e.target.value)}
                      className="appearance-none storyos-control h-8 px-3 pr-7 text-xs outline-hidden cursor-pointer"
                    >
                      <option value="与界面字体相同">与界面字体相同</option>
                      <option value="等宽代码字体">等宽代码字体</option>
                      <option value="宋体/明朝体 (剧本模式)">宋体/明朝体 (剧本模式)</option>
                    </select>
                    <ChevronDown className="w-3 h-3 text-[var(--text-tertiary)] absolute right-2 top-2.5 pointer-events-none" />
                  </div>
                  <div className="relative">
                    <select
                      value={contentFontWeight}
                      onChange={(e) => setContentFontWeight(e.target.value)}
                      className="appearance-none storyos-control h-8 px-2.5 pr-6 text-xs outline-hidden cursor-pointer"
                    >
                      <option value="常规">常规</option>
                      <option value="中粗">中粗</option>
                    </select>
                    <ChevronDown className="w-3 h-3 text-[var(--text-tertiary)] absolute right-2 top-2.5 pointer-events-none" />
                  </div>
                </div>
              </div>

              {/* 7. 半透明侧边栏 */}
              <div className="py-3 flex items-center justify-between">
                <span className="text-[var(--text-primary)] font-medium">半透明侧边栏</span>
                <button
                  type="button"
                  onClick={() => {
                    setTranslucentSidebar(!translucentSidebar);
                    showToast(translucentSidebar ? '已关闭半透明侧边栏' : '已启用半透明侧边栏');
                  }}
                  className={`w-11 h-6 rounded-full transition-colors p-0.5 flex items-center cursor-pointer ${
                    translucentSidebar ? 'bg-[var(--primary)] justify-end' : 'bg-[var(--border-strong)] justify-start'
                  }`}
                >
                  <span className="w-5 h-5 rounded-full bg-[var(--text-primary)]" />
                </button>
              </div>

              {/* 8. 对比度滑动条 */}
              <div className="py-3 last:pb-0 flex items-center justify-between gap-6">
                <span className="text-[var(--text-primary)] font-medium shrink-0">对比度</span>
                <div className="flex items-center gap-3 w-64">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={contrastValue}
                    onChange={(e) => setContrastValue(Number(e.target.value))}
                    className="w-full h-1.5 bg-[var(--border-normal)] rounded-[var(--radius-sm)] appearance-none cursor-pointer accent-[var(--primary)]"
                  />
                  <span className="text-[var(--text-secondary)] font-mono text-xs w-6 text-right shrink-0">
                    {contrastValue}
                  </span>
                </div>
              </div>
            </div>
          </section>

          {/* ===================== 2. 偏好设置 (Preferences) ===================== */}
          <section className="space-y-4">
            <h2 className="text-sm font-semibold text-[var(--text-primary)] tracking-wide">
              偏好设置
            </h2>

            <div className="storyos-surface p-4 divide-y divide-[var(--border-subtle)] text-xs">
              {/* 2.1 使用指针光标 */}
              <div className="py-3 first:pt-0 flex items-center justify-between">
                <div>
                  <div className="text-[var(--text-primary)] font-medium">使用指针光标</div>
                  <div className="text-[11px] text-[var(--text-tertiary)] mt-0.5">
                    悬停交互元素时切换为指针光标
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setPointerCursor(!pointerCursor);
                    showToast(pointerCursor ? '已关闭指针光标' : '已开启指针光标');
                  }}
                  className={`w-11 h-6 rounded-full transition-colors p-0.5 flex items-center cursor-pointer ${
                    pointerCursor ? 'bg-[var(--primary)] justify-end' : 'bg-[var(--border-strong)] justify-start'
                  }`}
                >
                  <span className="w-5 h-5 rounded-full bg-[var(--text-primary)]" />
                </button>
              </div>

              {/* 2.2 减少动态效果 */}
              <div className="py-3 flex items-center justify-between">
                <div>
                  <div className="text-[var(--text-primary)] font-medium">减少动态效果</div>
                  <div className="text-[11px] text-[var(--text-tertiary)] mt-0.5">
                    减少动画效果或匹配系统设置
                  </div>
                </div>
                <div className="bg-[var(--bg-muted)] p-0.5 rounded-[var(--radius-md)] border border-[var(--border-normal)] flex items-center gap-0.5">
                  {(['system', 'on', 'off'] as const).map((mode) => {
                    const labels = { system: '系统', on: '开启', off: '关闭' };
                    const isActive = reducedMotion === mode;
                    return (
                      <button
                        key={mode}
                        type="button"
                        onClick={() => {
                          setReducedMotion(mode);
                          showToast(`减少动态效果: ${labels[mode]}`);
                        }}
                        className={`px-3 py-1 rounded-md text-xs transition-colors cursor-pointer ${
                          isActive
                            ? 'bg-[var(--bg-selected)] text-[var(--text-primary)] font-medium'
                            : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)]'
                        }`}
                      >
                        {labels[mode]}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 2.3 UI 字号 */}
              <div className="py-3 flex items-center justify-between">
                <div>
                  <div className="text-[var(--text-primary)] font-medium">UI 字号</div>
                  <div className="text-[11px] text-[var(--text-tertiary)] mt-0.5">
                    调整 ChatGPT / StoryOS 界面使用的基准字号
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  <input
                    type="number"
                    min="11"
                    max="20"
                    value={uiFontSize}
                    onChange={(e) => setUiFontSize(e.target.value)}
                    className="storyos-control w-14 font-mono text-center px-2 text-xs outline-none focus:border-[var(--focus)]"
                  />
                  <span className="text-[var(--text-tertiary)] font-mono text-xs">px</span>
                </div>
              </div>

              {/* 2.4 差异标记 */}
              <div className="py-3 last:pb-0 flex items-center justify-between">
                <div>
                  <div className="text-[var(--text-primary)] font-medium">差异标记</div>
                  <div className="text-[11px] text-[var(--text-tertiary)] mt-0.5">
                    使用颜色或 +/- 标记显示更改
                  </div>
                </div>
                <div className="bg-[var(--bg-muted)] p-0.5 rounded-[var(--radius-md)] border border-[var(--border-normal)] flex items-center gap-0.5">
                  <button
                    type="button"
                    onClick={() => {
                      setDiffMarker('color');
                      showToast('差异标记: 颜色');
                    }}
                    className={`px-3 py-1 rounded-md text-xs transition-colors cursor-pointer ${
                      diffMarker === 'color'
                        ? 'bg-[var(--bg-selected)] text-[var(--text-primary)] font-medium'
                        : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)]'
                    }`}
                  >
                    颜色
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setDiffMarker('sign');
                      showToast('差异标记: +/-');
                    }}
                    className={`px-3 py-1 rounded-md text-xs transition-colors cursor-pointer ${
                      diffMarker === 'sign'
                        ? 'bg-[var(--bg-selected)] text-[var(--text-primary)] font-medium'
                        : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)]'
                    }`}
                  >
                    +/-
                  </button>
                </div>
              </div>
            </div>
          </section>
        </div>
      ) : (
        /* ===================== 管线与生产引擎设置 ===================== */
        <div className="space-y-4 max-w-3xl">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 模块 1：模型与执行层 */}
            <div className="storyos-surface p-4 space-y-3.5 text-xs">
              <div className="flex items-center gap-2 text-[var(--text-primary)] font-semibold border-b border-[var(--border-subtle)] pb-2">
                <Terminal className="w-4 h-4 text-[var(--primary)]" />
                <span>生图模型与任务编排</span>
              </div>

              <div>
                <label className="block text-[var(--text-secondary)] font-medium mb-1">模型引擎 (Model)</label>
                <select
                  value={modelFamily}
                  onChange={(e) => setModelFamily(e.target.value)}
                  className="storyos-control w-full px-2.5 font-mono text-xs outline-none focus:border-[var(--focus)] cursor-pointer"
                >
                  <option value="gpt-image-2">gpt-image-2 (官方推荐高质量工业模型)</option>
                  <option value="flux-pro">flux-pro (影视光影高保真渲染)</option>
                </select>
              </div>

              <div>
                <label className="block text-[var(--text-secondary)] font-medium mb-1">渲染质量 (Quality)</label>
                <select
                  value={qualityLevel}
                  onChange={(e) => setQualityLevel(e.target.value)}
                  className="storyos-control w-full px-2.5 font-mono text-xs outline-none focus:border-[var(--focus)] cursor-pointer"
                >
                  <option value="high">high (电影级高保真)</option>
                  <option value="standard">standard (标准快速预览)</option>
                </select>
              </div>

              <div>
                <label className="block text-[var(--text-secondary)] font-medium mb-1">任务执行层</label>
                <div className="p-2.5 rounded-[var(--radius-md)] bg-[var(--bg-subtle)] border border-[var(--border-normal)] flex items-center justify-between text-xs">
                  <span className="font-mono text-[var(--text-primary)] font-semibold flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5 text-[var(--primary)]" />
                    <span>{executionLayer}</span>
                  </span>
                  <span className="storyos-status storyos-status--running font-mono">
                    RUNNING
                  </span>
                </div>
              </div>
            </div>

            {/* 模块 2：画幅与并发控制 */}
            <div className="storyos-surface p-4 space-y-3.5 text-xs">
              <div className="flex items-center gap-2 text-[var(--text-primary)] font-semibold border-b border-[var(--border-subtle)] pb-2">
                <Camera className="w-4 h-4 text-[var(--primary)]" />
                <span>画幅与并发控制</span>
              </div>

              <div>
                <label className="block text-[var(--text-secondary)] font-medium mb-1">画幅比例 (Aspect Ratio)</label>
                <select
                  value={aspectRatio}
                  onChange={(e) => setAspectRatio(e.target.value)}
                  className="storyos-control w-full px-2.5 font-mono text-xs outline-none focus:border-[var(--focus)] cursor-pointer"
                >
                  <option value="4:5 1080×1350">4:5 1080×1350 (官方标准竖版)</option>
                  <option value="16:9 1920×1080">16:9 1920×1080 (横屏影院)</option>
                </select>
              </div>

              <div>
                <label className="block text-[var(--text-secondary)] font-medium mb-1">批次组织 (Batch Size)</label>
                <select
                  value={maxBatchSize}
                  onChange={(e) => setMaxBatchSize(e.target.value)}
                  className="storyos-control w-full px-2.5 font-mono text-xs outline-none focus:border-[var(--focus)] cursor-pointer"
                >
                  <option value="5">5 帧逻辑批次</option>
                  <option value="3">3 帧快速调试批次</option>
                  <option value="1">1 帧单帧调试</option>
                </select>
              </div>

              <div>
                <label className="block text-[var(--text-secondary)] font-medium mb-1">同时出图最大并发数</label>
                <select
                  value={maxConcurrency}
                  onChange={(e) => setMaxConcurrency(e.target.value)}
                  className="storyos-control w-full px-2.5 font-mono text-xs outline-none focus:border-[var(--focus)] cursor-pointer"
                >
                  <option value="3">3 张并发 (吞吐保护推荐)</option>
                  <option value="2">2 张并发</option>
                  <option value="1">1 张串行出图</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
