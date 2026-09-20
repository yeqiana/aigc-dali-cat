# Absorbed Rules Summary

本文件总结已内化并落入 StoryOS 代码与规则库的核心条目：

1. **Operate 模式优先**：严禁把生产调度后台做成营销展示页。
2. **状态契约唯一性**：状态必须是 `RUNNING`、`PASSED`、`QUEUED`、`RETRYING`、`BLOCKED`、`FAILED`、`NOT_STARTED`，严禁私自发明。
3. **状态文字强绑定**：不可单靠颜色区分状态。
4. **禁止全量粗暴刷新**：5 秒心跳数据只做局部下沉更新，严禁 `location.reload()`，保证用户滚动条、Drawer、Tab、搜索词绝不丢失。
5. **操作合法性**：PASSED 绝对不给跳过按钮；高危动作必须有二次确认。
6. **Preflight 范围锁定**：动工前预估文件范围，超范围立刻报警。
7. **Git Safety**：严禁 `reset --hard`，不污染工作区。
8. **证据化验收**：浏览器验收必须列举视口与状态证据。
9. **有限轮次精修**：达到 DoD 后立即停止无意义微调。
