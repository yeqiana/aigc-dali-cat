# StoryOS Web Console

StoryOS 的 React + TypeScript 前端生产控制台。默认入口是高密度 Production Monitor，并通过唯一的 Platform API 边界读取运行态、执行链路与生产证据。

## 当前数据边界

- Web Console 只通过 `VITE_PLATFORM_API_URL` / Vite 同源代理访问 StoryOS Platform API，不直接调用 Gemini 或其他模型 SDK。
- 前端不得直接推进 Episode stage；正式阶段以 StoryOS canonical state transition 为准。
- `src/data/storyosRealData.ts` 是从当前工作区 canonical evidence 生成的只读投影；生成器不复制生产像素资产到 `web-console/public`。
- WebCodex 是 Workspace Provider，不是 Episode Authority。

## 本地运行

要求 Node.js 22+，统一使用 npm。仓库只维护 `package-lock.json`，不要生成第二套 Bun/Yarn/PNPM 锁文件。

```bash
npm ci
npm run dev
```

默认开发服务监听 `0.0.0.0:3100`。

如果 Platform API 不与前端同源，可设置：

```bash
VITE_PLATFORM_API_URL=http://127.0.0.1:<platform-port>
```

未设置 `VITE_PLATFORM_API_URL` 时，Vite dev/preview 代理默认转发到 `http://127.0.0.1:8080`。

## 校验

```bash
npm run lint
npm run build
```

`npm run lint` 当前执行 TypeScript `tsc --noEmit` 校验。

## 主要入口

当前 React 版本是单页控制台，浏览器入口统一为 `/`，不再维护旧 Vue Router 的独立 URL。侧栏在同一页面内切换 Production Monitor、生产流水线、剧集/素材、Agent、数据看板、异常中心、系统设置与运行日志等工作区视图。

后端能力仍以 Platform API 的真实可用契约为准；前端不为尚未提供的 controller/API 保留伪造入口。

## Docker

构建镜像使用 `npm ci` 锁定依赖树：

```bash
docker build -f docker/Dockerfile -t story-os-web-console .
```
