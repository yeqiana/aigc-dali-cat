# StoryOS Web Console

StoryOS 的前端生产控制台。默认入口是高密度 Production Monitor，并提供 Runtime、Execution、Trace、Memory、Project、Agent、Plugin 等 Platform API 查询页。

## 当前数据边界

- Production Console 当前仍使用前端示例 Episode / Monitor 数据，并在界面常驻显示 `DEMO DATA · NOT AUTHORITY`。
- 前端不得直接推进 Episode stage；正式阶段以 StoryOS canonical state transition 为准。
- Platform 查询页读取真实 Platform API；失败会显式展示错误，不回退伪造结果。
- WebCodex 是 Workspace Provider，不是 Episode Authority。

## 本地运行

要求 Node.js 22+，统一使用 npm。仓库只维护 `package-lock.json`，不要生成第二套 Bun/Yarn/PNPM 锁文件。

```bash
npm ci
npm run dev
```

默认开发服务监听 `0.0.0.0:3000`。

如果 Platform API 不与前端同源，可设置：

```bash
VITE_PLATFORM_API_URL=http://127.0.0.1:<platform-port>
```

未设置 `VITE_PLATFORM_API_URL` 时，API 请求使用当前页面同源地址。

## 校验

```bash
npm run lint
npm run build
```

`npm run lint` 当前执行 TypeScript `tsc --noEmit` 校验。

## 主要入口

- `/`：Production Console
- `/platform`：Platform Console
- `/runtime`：Runtime Visualization
- `/executions`：Execution Explorer
- `/traces`：Trace Explorer
- `/memory`：Memory Console
- `/agents`：Agent Console

Project / Plugin / Marketplace 暂未暴露：当前默认 Platform HTTP composition 没有这些可用 controller/API 契约，前端不保留假入口。

## Docker

构建镜像使用 `npm ci` 锁定依赖树：

```bash
docker build -f docker/Dockerfile -t story-os-web-console .
```
