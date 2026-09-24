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
