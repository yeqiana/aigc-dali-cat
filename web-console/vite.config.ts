import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig } from 'vite';

// Web Console 只通过这一组代理访问 Platform API（默认 http://127.0.0.1:8080）。
// 与 web-console/.env.example 的 VITE_PLATFORM_API_URL 同源，二者不形成第二入口。
const platformApiTarget = process.env.VITE_PLATFORM_API_URL || 'http://127.0.0.1:8080';

const platformProxy = {
  '/api': {
    target: platformApiTarget,
    changeOrigin: true,
  },
  '/healthz': {
    target: platformApiTarget,
    changeOrigin: true,
  },
};

export default defineConfig(() => {
  return {
    plugins: [react(), tailwindcss()],
    build: {
      rollupOptions: {
        output: {
          manualChunks(id: string) {
            // 历史 Run 大包只随监控模块加载；Episode 证据与 Registry 分别独立。
            const normalized = id.replace(/\\/g, '/');
            if (normalized.includes('/src/data/storyosRunSnapshots.ts')) return 'historical-runs';
            if (normalized.includes('/src/data/storyosEpisodePart1.ts')) return 'historical-episode-a';
            if (normalized.includes('/src/data/storyosEpisodePart2.ts')) return 'historical-episode-b';
            if (normalized.includes('/src/data/storyosEpisodePart3.ts')) return 'historical-episode-c';
          },
        },
      },
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    server: {
      // Optional local-agent optimization: disable HMR/file watching when
      // DISABLE_HMR=true to reduce file-system churn during automated edits.
      hmr: process.env.DISABLE_HMR !== 'true',
      watch: process.env.DISABLE_HMR === 'true' ? null : {},
      proxy: platformProxy,
    },
    preview: { proxy: platformProxy },
  };
});
