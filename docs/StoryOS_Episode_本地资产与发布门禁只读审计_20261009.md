# StoryOS 本地 Episode 资产权威与发布门禁审计（2026-10-09）

> **状态：READ_ONLY_SNAPSHOT / NOT_A_PRODUCTION_RECEIPT。** 本文只读分析另一本地主工作树 `story-platform-v3-rever` 的文件，不对其剧集、MySQL、正式 `publish`、模型工具或运营记录作任何写入。本报告不是 Review Authority，也不是正式合格/可发布证明。文件可能随生产进展变化，使用前须重新核验。

## 已核查事实

| 项目 | 《未交的答卷》00-04 | 《五十亩山地之后》00-05 |
|---|---|---|
| 本地尚未进入 Git 的资产文件 | 60 | 74 |
| 图片生产 Prompt（命名为 `01.txt` 等） | 20 条（01–20） | 25 条（01–25） |
| `production/publish` 下编号 PNG | 20 | 0 |
| `meta/release-manifest.json` 预期正文帧 | 20 | 25 |
| `release.publish_dir` | `null` | `null` |
| `release.cover_path` | `null` | `null` |
| `quality.production_gate` | `pending` | `pending` |
| `quality.publish_decision` | `hold` | `hold` |

**关键结论：** 即使某 Episode 的 `publish` 路径已经放有全部编号图片，也不代表发布链路已通过；上表两个 Episode 均不得据此标记 `PUBLISH_READY`，也不能自动提交为权威审核结果。《五十亩山地之后》的生产预检正在另一条专门 worktree 分支推进，不应重复派发图片或覆盖其运行状态。

## 防陈旧输入快照（SHA-256 前 16 位，仅供重新比对）

| 文件 | 00-04 | 00-05 |
|---|---|---|
| `docs/story.md` | `19d241deb5867b88` | `370758d6db77a219` |
| `docs/storyboard.md` | `164a92d67805d3df` | `946da305a93f3bd0` |
| `docs/subtitles.yaml` | `e828588feb4cb38d` | `6231343bdec4e2d7` |
| `meta/release-manifest.json` | `3fbb40aa586e3e11` | `f92b15dffdf99b13` |

这些短摘要**不是安全验收哈希**；正式链路仍要核验全长 SHA-256、Request/Attempt ID、Provider Receipt、帧契约、Review Authority 和最终图片字节。

## 暂存与入库建议

1. 故事、分镜、字幕、稳定 Prompt 可以作为候选生产输入，但应先确认对应冻结状态、完整帧数、版本/SHA 绑定；然后分 Episode、分批提交。不得把 `meta/runtime`、`provider-receipts`、`shadow`、`production/publish` 的存在等同于验收。
2. 生成中间态、临时执行回执及生产成品留在本地工作区或受控资产存储，不能与故事输入使用 `git add -A` 批量提交。
3. 00-04 的 20 张 `publish` PNG 要经过真实字幕布局、Caption ↔ Image SHA、Review Authority、Release Manifest 和运营最终确认门禁。已有 PNG 不意味着允许跳过任何核验。
4. 00-05 目前 `production/publish` 没有编号 PNG；生产前须检查本地 `mysql8.0` 与 Episode 绑定、原生 Codex 能力、M00/Visual Lock 和 25 Frame Contract。**不得恢复 OpenCodex 代理生图，也不引入图片转视频**。
5. 两份旧的未提交验收测试调用当前代码中不存在的直接用户验收 API；不得为了通过测试添加可以越过 Release Critic 的假入口。新增 `tests/system/test_release_fail_closed_current_contract.py` 检验当前发布审核的真实拒绝行为。

## 后续验收完成条件

本地资产归属确认 → 正式请求/回执核验 → 字幕和图片 SHA 绑定 → Review Authority 验证 → 完整 Release Manifest → 最终用户验收 → `PUBLISH_READY`。任何一层缺证时保留 `hold` 状态，不推断 PASS。

**安全边界：只读审计；没有接触付费生图、正式 MySQL、用户原图或正式 Episode 文件写入。**
