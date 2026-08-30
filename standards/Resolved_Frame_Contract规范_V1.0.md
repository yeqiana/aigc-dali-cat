# Resolved Frame Contract 规范 V1.0

> Story OS V2.1 Phase 4 subordinate engineering standard。  
> `meta/runtime/contracts/` 下的文件全部是 **derived cache**，不是第二权威源。

## 1. 目标

正式校准与生产每一帧时，不再让生成 Worker 临时猜测应该组合哪些规则。

每帧统一解析：

```text
Story
+ Storyboard frame
+ Visual Profile / Visual DNA
+ Capture Profile
+ Authenticity Card
+ Continuity
+ Environment Contract
+ Frame Directive / Impact
+ References
↓
Resolved Frame Contract
↓
frame_contract_sha256
```

生成器与最终 Reviewer 必须绑定相同 `frame_contract_sha256`。

## 2. 权威关系

权威源仍然是：

- Story
- Storyboard
- `meta/story-gates.json`
- Visual Profile
- 已批准 References

派生缓存：

```text
meta/runtime/contracts/frames/01.json
...
meta/runtime/contracts/frames/NN.json
meta/runtime/contracts/frame-contract-index.json
```

派生缓存不得反向修改权威源。

## 3. 局部失效

Frame Contract 的 SHA 尽量使用逐帧输入：

- Story SHA：故事变更默认影响全部帧；
- Storyboard：优先抽取当前 frame 的局部 SHA；
- Environment：使用 `environment_frame_sha256`；
- Directive：使用 `frame_directive_sha256`；
- Reference：按当前帧适用范围绑定 SHA。

如果 Storyboard 格式无法可靠抽取当前帧，则安全降级到全 Storyboard SHA，此时可能扩大 dirty 范围，但不得漏失效。

## 4. 生成证据链

Production Ledger 的 generation request 必须记录：

```json
{
  "frame_contract": {
    "schema_version": 1,
    "path": "meta/runtime/contracts/frames/10.json",
    "contract_sha256": "..."
  }
}
```

候选成功登记前，再次对当前 Frame Contract 校验。

## 5. 审核证据链

最终 Frame Semantic Review 必须：

1. 重算当前 Frame Contract；
2. 检查批准图片对应的 Production Ledger generation attempt；
3. generation attempt 的 `frame_contract_sha256` 必须等于当前 SHA；
4. frame review evidence 同样写入 `frame_contract_sha256`。

如果合同变了：

- 不得让旧生成 attempt 冒充新合同；
- 应重新生成，或在明确允许的后续机制中重新验证/迁移。

## 6. Generator

正式 `codex_subscription_image.py generate-for-frame` 必须自动：

1. 编译当前 Frame Contract；
2. 将 `<frame_contract>` 注入 image worker；
3. 返回 `frame_contract_sha256`；
4. 保持 scene prompt 与合同分层：短 scene prompt 不负责重复所有全局规则。

## 7. 运行顺序

```text
Story Lock
→ Environment / Impact Contract
→ compile-all Frame Contracts
→ Visual Lock calibration
→ verify Frame Contracts again
→ Production
```

Phase 4 不引入 3-worker 并发；调度并发在后续阶段处理。
