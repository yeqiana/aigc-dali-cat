import vue2 from '@vitejs/plugin-vue2';
import path from 'path';
import {defineConfig} from 'vite';

export default defineConfig(() => {
  const platformProxy = {
    '/api': {
      target: process.env.VITE_PLATFORM_API_URL || 'http://127.0.0.1:8080',
      changeOrigin: true,
    },
    '/healthz': {
      target: process.env.VITE_PLATFORM_API_URL || 'http://127.0.0.1:8080',
      changeOrigin: true,
    },
  };
  return {
    plugins: [vue2()],
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
    preview: {proxy: platformProxy},
  };
});
