# Story Gates

## 选题前置

执行主规范中的：

- 同系列“四把锁”反换皮。
- 最近5篇账号级同质化检查。
- 核心异常机制 + 中段升级逻辑 + 高潮兑现方式的“机制换皮一票否决”。
- 地点陌生感、日常动机、具体异常、可争论真相等选题准入。

把机器能记录的结果写进 `episode.yaml`：

```yaml
anti_homogeneity:
  recent5_checked: true
  four_locks_diff_count: 2
  mechanism_skin_swap_veto: false
```

这里的 `mechanism_skin_swap_veto: true` 表示**触发一票否决**，validator 必须 FAIL。

## 故事闭环

进入正式分镜前至少锁定：

- `hook_frames`
- `visual_admission_frames`（四张视觉准入）
- `escalation_frames`
- `climax_frame`
- `payoff_frame`
- `task_closed: true`
- `competing_explanations >= 2`（若当前主规范仍要求可争论真相）

机器只检查这些状态是否存在、编号是否合法；“好不好看/够不够强”仍需人工审核。
