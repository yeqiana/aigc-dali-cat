import React, { useState } from 'react';
import {
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Copy,
  Download,
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
  const [bgColor, setBgColor] = useState('#181818');
  const [fgColor, setFgColor] = useState('#FFFFFF');
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
    showToast('已复制 Codex 主题配置至剪贴板');
  };

  return (
    <div id="codex-appearance-settings-view" className="space-y-6 text-zinc-300 font-sans select-none pb-24">
      {/* Toast 提示 */}
      {toastMessage && (
        <div className="fixed top-12 right-8 z-50 bg-white text-black px-4 py-2 rounded-xl text-xs font-semibold shadow-2xl flex items-center gap-2 animate-in fade-in">
          <Check className="w-4 h-4 text-black" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* 顶部标签切换：外观参数 与 管线参数 */}
      <div className="flex items-center justify-between border-b border-[#262626] pb-3">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setActiveSubTab('appearance')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer flex items-center gap-1.5 ${
              activeSubTab === 'appearance'
                ? 'bg-white text-black font-semibold'
                : 'text-zinc-400 hover:text-white hover:bg-[#18181b]'
            }`}
          >
            <Palette className="w-3.5 h-3.5" />
            <span>外观参数 (Appearance)</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveSubTab('pipeline')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer flex items-center gap-1.5 ${
              activeSubTab === 'pipeline'
                ? 'bg-white text-black font-semibold'
                : 'text-zinc-400 hover:text-white hover:bg-[#18181b]'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>StoryOS 管线与并发设置</span>
          </button>
        </div>

        <div className="text-[11px] font-mono text-zinc-500">
          Codex UI Settings v2.4
        </div>
      </div>

      {activeSubTab === 'appearance' ? (
        <div className="space-y-8 max-w-3xl">
          {/* ===================== 1. 主题 (Theme) ===================== */}
          <section className="space-y-4">
            <h2 className="text-sm font-semibold text-white tracking-wide">
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
                  themeMode === 'system' ? 'text-white' : 'text-zinc-400 hover:text-zinc-200'
                }`}
              >
                <div className={`w-full aspect-[16/10] rounded-xl overflow-hidden border transition-all relative flex ${
                  themeMode === 'system'
                    ? 'border-white ring-2 ring-white/20'
                    : 'border-[#2e2e2e] hover:border-[#444]'
                }`}>
                  {/* 左半浅色 */}
                  <div className="w-1/2 h-full bg-[#8c8c8c] p-2 flex flex-col justify-end relative">
                    <div className="w-full h-4/5 bg-white/95 rounded-tl-lg p-1.5 space-y-1 shadow-sm">
                      <div className="w-12 h-1 bg-zinc-300 rounded-full" />
                      <div className="w-full h-0.5 bg-zinc-200 rounded-full" />
                      <div className="w-4/5 h-0.5 bg-zinc-200 rounded-full" />
                    </div>
                  </div>
                  {/* 右半深色 */}
                  <div className="w-1/2 h-full bg-[#262626] p-2 flex flex-col justify-end relative">
                    <div className="w-full h-4/5 bg-[#141414] rounded-tr-lg p-1.5 space-y-1 shadow-sm">
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
                  themeMode === 'light' ? 'text-white' : 'text-zinc-400 hover:text-zinc-200'
                }`}
              >
                <div className={`w-full aspect-[16/10] rounded-xl overflow-hidden border transition-all p-2 flex flex-col justify-end bg-[#e4e4e7] ${
                  themeMode === 'light'
                    ? 'border-white ring-2 ring-white/20'
                    : 'border-[#2e2e2e] hover:border-[#444]'
                }`}>
                  <div className="w-full h-4/5 bg-white rounded-t-lg p-2 space-y-1.5 shadow-sm">
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
                  themeMode === 'dark' ? 'text-white' : 'text-zinc-400 hover:text-zinc-200'
                }`}
              >
                <div className={`w-full aspect-[16/10] rounded-xl overflow-hidden border transition-all p-2 flex flex-col justify-end bg-[#262626] ${
                  themeMode === 'dark'
                    ? 'border-white ring-2 ring-white/20'
                    : 'border-[#2e2e2e] hover:border-[#444]'
                }`}>
                  <div className="w-full h-4/5 bg-[#ffffff] rounded-t-lg p-2 space-y-1.5 shadow-sm">
                    <div className="w-16 h-1.5 bg-zinc-300 rounded-full" />
                    <div className="w-full h-1 bg-zinc-200 rounded-full" />
                    <div className="w-5/6 h-1 bg-zinc-200 rounded-full" />
                    <div className="w-3/4 h-1 bg-zinc-200 rounded-full" />
                  </div>
                </div>
                <span className="text-xs font-medium">深色</span>
              </button>
            </div>

            {/* Code Diff Preview (代码差异对比预览组件) */}
            <div className="rounded-xl border border-[#27272a] bg-[#0c0c0e] font-mono text-[11px] overflow-hidden">
              <div className="grid grid-cols-2 divide-x divide-[#222226]">
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
              <div className="px-2 py-1 bg-[#101013] border-t border-[#1f1f23] flex items-center justify-between text-zinc-600">
                <div className="flex items-center gap-1">
                  <ChevronLeft className="w-3 h-3 hover:text-zinc-400 cursor-pointer" />
                </div>
                <div className="flex items-center gap-1">
                  <ChevronRight className="w-3 h-3 hover:text-zinc-400 cursor-pointer" />
                </div>
              </div>
            </div>

            {/* 深色主题参数卡片 (Codex 风格圆角面板) */}
            <div className="bg-[#141416] border border-[#27272a] rounded-2xl p-4 divide-y divide-[#222226] text-xs">
              {/* 1. 深色主题选择与动作 */}
              <div className="py-3 first:pt-0 flex items-center justify-between">
                <span className="text-white font-medium">深色主题</span>
                <div className="flex items-center gap-2.5">
                  <button
                    type="button"
                    onClick={() => showToast('已打开主题导入窗口')}
                    className="text-zinc-400 hover:text-white transition-colors cursor-pointer"
                  >
                    导入
                  </button>
                  <button
                    type="button"
                    onClick={handleCopyTheme}
                    className="text-zinc-400 hover:text-white transition-colors cursor-pointer"
                  >
                    复制主题
                  </button>
                  <div className="px-1.5 py-0.5 rounded bg-[#202024] text-zinc-400 text-[10px] font-mono border border-[#2e2e33]">
                    Aa
                  </div>
                  <div className="relative">
                    <select
                      value={darkThemePreset}
                      onChange={(e) => {
                        setDarkThemePreset(e.target.value);
                        showToast(`已应用主题: ${e.target.value}`);
                      }}
                      className="appearance-none bg-[#202024] border border-[#2e2e33] hover:border-zinc-500 text-white rounded-lg px-3 py-1.5 pr-7 text-xs font-mono outline-hidden cursor-pointer"
                    >
                      <option value="Codex">Codex</option>
                      <option value="GitHub Dark">GitHub Dark</option>
                      <option value="Vesper">Vesper</option>
                      <option value="One Dark Pro">One Dark Pro</option>
                    </select>
                    <ChevronDown className="w-3 h-3 text-zinc-400 absolute right-2 top-2.5 pointer-events-none" />
                  </div>
                </div>
              </div>

              {/* 2. 强调色 */}
              <div className="py-3 flex items-center justify-between">
                <span className="text-white font-medium">强调色</span>
                <div className="relative">
                  <select
                    value={accentColor}
                    onChange={(e) => {
                      setAccentColor(e.target.value);
                      showToast(`强调色已设为: ${e.target.value}`);
                    }}
                    className="appearance-none bg-[#202024] border border-[#2e2e33] hover:border-zinc-500 text-white rounded-lg px-3 py-1.5 pr-7 text-xs outline-hidden cursor-pointer"
                  >
                    <option value="默认">默认</option>
                    <option value="纯白高亮">纯白高亮</option>
                    <option value="经典蓝">经典蓝 (#2563eb)</option>
                    <option value="翡翠绿">翡翠绿 (#10b981)</option>
                  </select>
                  <ChevronDown className="w-3 h-3 text-zinc-400 absolute right-2 top-2.5 pointer-events-none" />
                </div>
              </div>

              {/* 3. 背景颜色 */}
              <div className="py-3 flex items-center justify-between">
                <span className="text-white font-medium">背景</span>
                <button
                  type="button"
                  onClick={() => showToast('背景色已锁定: #181818')}
                  className="px-3 py-1 rounded-lg bg-[#202024] border border-[#2e2e33] hover:border-zinc-400 text-white font-mono text-xs flex items-center gap-2 cursor-pointer"
                >
                  <span className="w-2.5 h-2.5 rounded-full border border-zinc-500 bg-[#181818]" />
                  <span>{bgColor}</span>
                </button>
              </div>

              {/* 4. 前景颜色 */}
              <div className="py-3 flex items-center justify-between">
                <span className="text-white font-medium">前景</span>
                <button
                  type="button"
                  onClick={() => showToast('前景色已锁定: #FFFFFF')}
                  className="px-3 py-1 rounded-lg bg-white text-black font-mono font-bold text-xs flex items-center gap-2 cursor-pointer shadow-xs hover:bg-zinc-200"
                >
                  <span className="w-2.5 h-2.5 rounded-full border border-zinc-300 bg-white" />
                  <span>{fgColor}</span>
                </button>
              </div>

              {/* 5. UI 字体 */}
              <div className="py-3 flex items-center justify-between">
                <span className="text-white font-medium">UI 字体</span>
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <select
                      value={uiFont}
                      onChange={(e) => setUiFont(e.target.value)}
                      className="appearance-none bg-[#202024] border border-[#2e2e33] text-white rounded-lg px-3 py-1.5 pr-7 text-xs outline-hidden cursor-pointer"
                    >
                      <option value="系统默认">系统默认</option>
                      <option value="Inter">Inter</option>
                      <option value="PingFang SC">PingFang SC</option>
                      <option value="JetBrains Mono">JetBrains Mono</option>
                    </select>
                    <ChevronDown className="w-3 h-3 text-zinc-400 absolute right-2 top-2.5 pointer-events-none" />
                  </div>
                  <div className="relative">
                    <select
                      value={uiFontWeight}
                      onChange={(e) => setUiFontWeight(e.target.value)}
                      className="appearance-none bg-[#202024] border border-[#2e2e33] text-white rounded-lg px-2.5 py-1.5 pr-6 text-xs outline-hidden cursor-pointer"
                    >
                      <option value="常规">常规</option>
                      <option value="中粗">中粗</option>
                      <option value="粗体">粗体</option>
                    </select>
                    <ChevronDown className="w-3 h-3 text-zinc-400 absolute right-2 top-2.5 pointer-events-none" />
                  </div>
                </div>
              </div>

              {/* 6. 内容字体 */}
              <div className="py-3 flex items-center justify-between">
                <span className="text-white font-medium">内容字体</span>
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <select
                      value={contentFont}
                      onChange={(e) => setContentFont(e.target.value)}
                      className="appearance-none bg-[#202024] border border-[#2e2e33] text-white rounded-lg px-3 py-1.5 pr-7 text-xs outline-hidden cursor-pointer"
                    >
                      <option value="与界面字体相同">与界面字体相同</option>
                      <option value="等宽代码字体">等宽代码字体</option>
                      <option value="宋体/明朝体 (剧本模式)">宋体/明朝体 (剧本模式)</option>
                    </select>
                    <ChevronDown className="w-3 h-3 text-zinc-400 absolute right-2 top-2.5 pointer-events-none" />
                  </div>
                  <div className="relative">
                    <select
                      value={contentFontWeight}
                      onChange={(e) => setContentFontWeight(e.target.value)}
                      className="appearance-none bg-[#202024] border border-[#2e2e33] text-white rounded-lg px-2.5 py-1.5 pr-6 text-xs outline-hidden cursor-pointer"
                    >
                      <option value="常规">常规</option>
                      <option value="中粗">中粗</option>
                    </select>
                    <ChevronDown className="w-3 h-3 text-zinc-400 absolute right-2 top-2.5 pointer-events-none" />
                  </div>
                </div>
              </div>

              {/* 7. 半透明侧边栏 */}
              <div className="py-3 flex items-center justify-between">
                <span className="text-white font-medium">半透明侧边栏</span>
                <button
                  type="button"
                  onClick={() => {
                    setTranslucentSidebar(!translucentSidebar);
                    showToast(translucentSidebar ? '已关闭半透明侧边栏' : '已启用半透明侧边栏');
                  }}
                  className={`w-11 h-6 rounded-full transition-colors p-0.5 flex items-center cursor-pointer ${
                    translucentSidebar ? 'bg-[#2563eb] justify-end' : 'bg-[#27272a] justify-start'
                  }`}
                >
                  <span className="w-5 h-5 rounded-full bg-white shadow-md" />
                </button>
              </div>

              {/* 8. 对比度滑动条 */}
              <div className="py-3 last:pb-0 flex items-center justify-between gap-6">
                <span className="text-white font-medium shrink-0">对比度</span>
                <div className="flex items-center gap-3 w-64">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={contrastValue}
                    onChange={(e) => setContrastValue(Number(e.target.value))}
                    className="w-full h-1.5 bg-[#27272a] rounded-lg appearance-none cursor-pointer accent-[#2563eb]"
                  />
                  <span className="text-zinc-300 font-mono text-xs w-6 text-right shrink-0">
                    {contrastValue}
                  </span>
                </div>
              </div>
            </div>
          </section>

          {/* ===================== 2. 偏好设置 (Preferences) ===================== */}
          <section className="space-y-4">
            <h2 className="text-sm font-semibold text-white tracking-wide">
              偏好设置
            </h2>

            <div className="bg-[#141416] border border-[#27272a] rounded-2xl p-4 divide-y divide-[#222226] text-xs">
              {/* 2.1 使用指针光标 */}
              <div className="py-3 first:pt-0 flex items-center justify-between">
                <div>
                  <div className="text-white font-medium">使用指针光标</div>
                  <div className="text-[11px] text-zinc-400 mt-0.5">
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
                    pointerCursor ? 'bg-[#2563eb] justify-end' : 'bg-[#27272a] justify-start'
                  }`}
                >
                  <span className="w-5 h-5 rounded-full bg-white shadow-md" />
                </button>
              </div>

              {/* 2.2 减少动态效果 */}
              <div className="py-3 flex items-center justify-between">
                <div>
                  <div className="text-white font-medium">减少动态效果</div>
                  <div className="text-[11px] text-zinc-400 mt-0.5">
                    减少动画效果或匹配系统设置
                  </div>
                </div>
                <div className="bg-[#202024] p-0.5 rounded-lg border border-[#2e2e33] flex items-center gap-0.5">
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
                            ? 'bg-[#323238] text-white font-medium'
                            : 'text-zinc-400 hover:text-white'
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
                  <div className="text-white font-medium">UI 字号</div>
                  <div className="text-[11px] text-zinc-400 mt-0.5">
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
                    className="w-14 bg-[#202024] border border-[#2e2e33] text-white font-mono text-center rounded-lg px-2 py-1 text-xs focus:border-zinc-400 outline-hidden"
                  />
                  <span className="text-zinc-400 font-mono text-xs">px</span>
                </div>
              </div>

              {/* 2.4 差异标记 */}
              <div className="py-3 last:pb-0 flex items-center justify-between">
                <div>
                  <div className="text-white font-medium">差异标记</div>
                  <div className="text-[11px] text-zinc-400 mt-0.5">
                    使用颜色或 +/- 标记显示更改
                  </div>
                </div>
                <div className="bg-[#202024] p-0.5 rounded-lg border border-[#2e2e33] flex items-center gap-0.5">
                  <button
                    type="button"
                    onClick={() => {
                      setDiffMarker('color');
                      showToast('差异标记: 颜色');
                    }}
                    className={`px-3 py-1 rounded-md text-xs transition-colors cursor-pointer ${
                      diffMarker === 'color'
                        ? 'bg-[#323238] text-white font-medium'
                        : 'text-zinc-400 hover:text-white'
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
                        ? 'bg-[#323238] text-white font-medium'
                        : 'text-zinc-400 hover:text-white'
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
            <div className="bg-[#141416] p-4 rounded-2xl border border-[#27272a] space-y-3.5 text-xs">
              <div className="flex items-center gap-2 text-white font-bold border-b border-[#222226] pb-2">
                <Terminal className="w-4 h-4 text-white" />
                <span>生图模型与任务编排</span>
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">模型引擎 (Model)</label>
                <select
                  value={modelFamily}
                  onChange={(e) => setModelFamily(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-[#000000] border border-[#27272a] text-white font-mono text-xs focus:border-white outline-hidden cursor-pointer"
                >
                  <option value="gpt-image-2">gpt-image-2 (官方推荐高质量工业模型)</option>
                  <option value="flux-pro">flux-pro (影视光影高保真渲染)</option>
                </select>
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">渲染质量 (Quality)</label>
                <select
                  value={qualityLevel}
                  onChange={(e) => setQualityLevel(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-[#000000] border border-[#27272a] text-white font-mono text-xs focus:border-white outline-hidden cursor-pointer"
                >
                  <option value="high">high (电影级高保真)</option>
                  <option value="standard">standard (标准快速预览)</option>
                </select>
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">任务执行层</label>
                <div className="p-2.5 rounded-lg bg-[#000000] border border-[#27272a] flex items-center justify-between text-xs">
                  <span className="font-mono text-white font-bold flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5 text-white" />
                    <span>{executionLayer}</span>
                  </span>
                  <span className="text-[10px] font-mono font-bold text-black bg-white px-2 py-0.5 rounded">
                    RUNNING
                  </span>
                </div>
              </div>
            </div>

            {/* 模块 2：画幅与并发控制 */}
            <div className="bg-[#141416] p-4 rounded-2xl border border-[#27272a] space-y-3.5 text-xs">
              <div className="flex items-center gap-2 text-white font-bold border-b border-[#222226] pb-2">
                <Camera className="w-4 h-4 text-white" />
                <span>画幅与并发控制</span>
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">画幅比例 (Aspect Ratio)</label>
                <select
                  value={aspectRatio}
                  onChange={(e) => setAspectRatio(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-[#000000] border border-[#27272a] text-white font-mono text-xs focus:border-white outline-hidden cursor-pointer"
                >
                  <option value="4:5 1080×1350">4:5 1080×1350 (官方标准竖版)</option>
                  <option value="16:9 1920×1080">16:9 1920×1080 (横屏影院)</option>
                </select>
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">批次组织 (Batch Size)</label>
                <select
                  value={maxBatchSize}
                  onChange={(e) => setMaxBatchSize(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-[#000000] border border-[#27272a] text-white font-mono text-xs focus:border-white outline-hidden cursor-pointer"
                >
                  <option value="5">5 帧逻辑批次</option>
                  <option value="3">3 帧快速调试批次</option>
                  <option value="1">1 帧单帧调试</option>
                </select>
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">同时出图最大并发数</label>
                <select
                  value={maxConcurrency}
                  onChange={(e) => setMaxConcurrency(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-[#000000] border border-[#27272a] text-white font-mono text-xs focus:border-white outline-hidden cursor-pointer"
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
