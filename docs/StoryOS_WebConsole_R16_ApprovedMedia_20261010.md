# StoryOS Web Console R16｜真实批准图片只读接入与视觉验收

日期：2026-10-10　目标分支：`story-platform-v3-rever`

## 动机和边界

R15 解决了历史 `data:image/svg+xml` 假图占屏的问题，但尚未接通真实已批准图片。R16 只读取本地工作区 `episodes/<系列>/<作品>/media/approved/NN.png`（或 JPEG/WebP）以及同目录 `meta/episode-state.json`。这是**本机批准文件投影**，不是在线 Runtime、图片 Provider 回执或某次历史 Run 的专属产物证据。

不会访问：`candidates`、`identity`、`_archive`、`_tests`、任意外部目录、符号链接目标、任意文件路径。媒体接口**仅在本地只读启动器** `scripts/storyos_local_readonly_api.py` 中注册，不加入平台正式 API/生产服务。

## 四槽交付

| 范围 | 变更 |
|---|---|
| 安全 API | `GET /api/v1/local-media/catalog` 返回不包含路径的批准帧索引；`GET /api/v1/local-media/images/<32位不透明标识>` 返回真正 PNG/JPG/WebP 字节。不接受任何客户端路径输入 |
| 制作台 | `localApprovedMedia.ts` 仅读取本地模式的媒体目录，用**标题 + 业务 Episode 编号严格匹配**；制作台独立展示已批准的真实图库，初始 10 张可展开至 20 张；原批次帧状态矩阵仍独立显示 |
| 作品目录 | 工作台与作品库只对匹配身份且已批准的作品显示真实首帧，其余继续使用中性无封面标记；不影响表格分页 |
| 历史 Run | 精确匹配标题/Run 对应业务编号后可展示批准图，但标签必须声明“本地已批准素材 · 非该 Run 原始证据”；没有批准图的历史 Run 不伪造图片 |

## 安全约束

- 必须存在可解析的 `meta/episode-state.json`，且非测试/归档路径，具有严格的作品标题和业务编号。
- 图片目录只允许 `media/approved`；只读、只允许帧号 `01`–`20`、扩展名 PNG/JPG/JPEG/WebP、长度不超过 12 MiB；检查真实文件头和最终路径，不跟随符号链接。
- 下载端每次重新扫描许可目录，校验哈希不透明标识。服务仅绑定 `127.0.0.1`，限制 Host、Origin 和 Sec-Fetch-Site，同源 Vite 代理访问。禁跨域访问、OPTIONS；响应有 `nosniff` 和 `no-store`。
- 禁止直接向网页暴露绝对 Windows 路径，禁止调用生产任务，禁止绕过审核将候选图提升为 approved。
- 图片在集成隔离 Worktree 中不复制，也不提交 Git；本地预览使用 Git Common Directory 对应的**主工作区原始素材**。

## 验收

- 实际主工作区批准图：`误入桃花源` 20 张、`婚礼前夜` 20 张、`仲夏夜惊魂｜停电夜蜕壳` 20 张，共 60 张；其他作品没有符合当前目录合同的批准图。
- 隔离 Vite `127.0.0.1:3109` → 本机只读 `127.0.0.1:19118`：已返回 60 条经图片头验证的索引，实际 PNG 请求 200，字节成功解码，非授权路径 404。
- `python -m unittest tests.system.test_storyos_local_approved_media -v`：临时目录、归档/候选/符号链接/无效头/跨域/只读 HTTP 共 3 组安全测试。
- `npm run test:media`：Chrome **4/4**，作品库封面、制作台 10 张图、历史 Run 20 张图成功解码，未批准作品不得出现媒体图；包含真实桌面截图、无横向溢出。
- 同时运行 `npm run lint`、`npm run build -- --base=./`、`test:bundles`、`test:api`、`test:monitor`、`test:workflow`、`test:console`、`test:episodes`、`test:runs`、`test:readonly-probe` 与既有 R10–R13 视觉/分页/主题浏览器回归。
- 截图在被 Git 忽略的 `.storyos-tmp/ui-qa/r16/`，不进入仓库，不触及 `episodes/` 文件内容。

## 后续可优化

目前已批准素材是只读图库投影，尚未与每次 Generation Attempt、Frame Audit 具体产物逐项形成强证据关系。若需要宣称“该历史 Run 产生了这张图片”，必须先获得 Runtime 的权威产物映射和审核记录，不得仅靠标题、帧号推断。
