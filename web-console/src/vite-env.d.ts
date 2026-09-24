/// <reference types="vite/client" />

// Web Console 只从环境变量读取 Platform API 基址；未设置时留空，
// 由 vite.config.ts 的 platformProxy 走同源代理。
interface ImportMetaEnv {
  readonly VITE_PLATFORM_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
