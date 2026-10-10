import React, { Suspense } from 'react';

// 大体量作品证据与完整工作区代码按需独立加载，避免阻塞最小入口解析。
const StoryOSApp = React.lazy(() => import('./StoryOSApp'));

export default function App() {
  return (
    <Suspense fallback={<div role="status" className="min-h-screen flex items-center justify-center bg-[var(--bg-app)] text-[13px] text-[var(--text-secondary)]">正在载入 StoryOS 工作区…</div>}>
      <StoryOSApp />
    </Suspense>
  );
}
