# Fast Frame Scout 与 Final Candidate Snapshot 规范 V1.0

## Phase 7：Fast Frame Scout

Scout 是**提前拦明显错图**的低成本/风险分级层，不是 Final Critic。

三种结果：

- `PASS_FAST`：没看到明显硬伤，但**不能**写 Production PASS；
- `REPAIR_NOW`：高置信明显错误，立即进入内容失败/返修路径；
- `DEFER_TO_FINAL`：低风险或不确定，交给最终全篇 Critic。

High Risk 包括：

- identity
- key prop
- first anomaly
- anomaly amplified
- climax
- payoff / residue / ending
- POV / recorder
- impact 3–4
- 困难环境条件

Low Risk 默认不额外花一次模型调用，直接 `DEFER_TO_FINAL`。

Scout 技术失败同样 `DEFER_TO_FINAL`，不能拖死生产。

最终 `Frame Semantic Critic` 永远保留。

## Phase 8：Final Candidate Snapshot

在 Release Critic / Compliance / Text Audit / Final Frame Review 都通过后、进入 `PUBLISH_READY` 前，冻结：

- Story SHA
- Storyboard SHA
- Story Gates 稳定合同子集 SHA
- Publish 正文图片 SHA
- Cover SHA
- Captions SHA
- Publish Copy SHA
- Propagation Card SHA
- Release Manifest SHA
- Production / Frame / Visual / Text / Release / Compliance evidence SHA
- Publication object hash

生成：

```text
meta/final-candidate-snapshot.json
```

Snapshot 不是新创作权威，而是**最终候选冻结证据**。

## Delivery Adapter

V2.1 Snapshot 启用后，Delivery ZIP 不允许再扫描“当前目录最新文件”自行组装。

必须：

```text
Final Candidate Snapshot
↓
verify SHA
↓
读取 snapshot.lock.delivery_files
↓
ZIP
```

如果任一源文件漂移：

```text
snapshot STALE
→ Delivery BLOCK
```

这样 CODEX 在 `PUBLISH_READY` 完成生产；ZIP 仍只是可选 Delivery Adapter。
