# CODEX Runtime V2.0

用户给出仓库/剧集并要求“全自动执行”后，除非遇到硬冲突、权限或安全确认，不在正常节点重复询问“是否继续”。

执行链：

`恢复状态 → Story Gate → 真实性卡/锚点 → 三张校准 → 四张视觉准入 → Batch → 逐帧自审/最多一次返修 → 字幕 → Final QA → publish → SHA → FINAL ZIP`

要求：
- 通过图必须保存真实文件并登记 SHA。
- originals / repairs / approved / publish 分离。
- subtitle_only 必须校验底图 SHA 不变。
- 断点续跑必须复用已通过且 SHA 未漂移资产。
- 最终 ZIP 只收最终 publish 资产。
- “全自动”表示连续执行授权；自动审查记为 `delegated_auto_review`，不能写成用户亲眼审过。
- checkpoint：`<episode>/meta/runtime-checkpoint.json`，runtime=`CODEX`。
