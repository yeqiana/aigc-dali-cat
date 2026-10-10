# StoryOS Agent 瘦身 PR #21：合并前门禁（2026-10-10）

## 当前阶段

- Draft PR：`#21`；实际发布链和数据库权威未改动。
- **CI 必须以本 PR 最后一次 HEAD 为准**，不能以过期的成功 Workflow 放行。
- Linux、Windows Story Gates + Qodana、正式生产的全部相关安全测试需要完成，失败时先查日志。
- 原生 Codex `-C <episode>` / 相对 Host Request 仍需在目标用户 Windows 主机做真实接入验收；pytest Mock 只能证实参数组装，不证明用户登录、文件沙箱或模型可以访问附件。
- 性能基线工具只读旧 Episode 回执，不连接 MySQL，输出中缺失值为未知而不是零。
- 未完成真实同配置 Episode 的耗时、Token、质量对照前，不声明生产加速百分比。

## 已知历史瓶颈证据

《五十亩山地之后》14 条现存模型执行回执含 3 个 TIMEOUT、3 个 FAILED，三个 TIMEOUT 均发生在前期资产步骤，耗时约 900 秒；Prompt Authoring 一个失败回执超过 38 分钟。这些都不是 Provider 错误分类结论，禁止仅凭本报告重试或重置 Attempt。

## 永久不回退

MySQL Episode / Attempt / Production Revision Authority、唯一 Episode Owner、跨 Worktree 总计最多 5 在途图片名额、原生 Codex 图片通道与 Fail-Closed、正式 Release/Review Evidence、图文而非视频、不可确定结果不得被自动计为失败/退款。

只有正式 CI + 更完整的性能/接入证据通过，才考虑将 Draft PR 标记为可评审和合并；本轮不会替用户执行真实生图。
