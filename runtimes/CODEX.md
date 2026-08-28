# CODEX Runtime V2.0.1

Codex 是 Story OS 的文件原生全自动生产 runtime。用户明确要求“全自动执行 / 一次做完 / 做到最终交付”后，除硬冲突、权限、安全确认、工具缺失或一次内容返修后仍失败，不在正常节点重复询问“是否继续”。

## 一键入口

```bash
python episodes/_system/story_os.py run <episode_dir> --full-auto
```

该命令启动 `codex_auto_orchestrator.py`，由一个独立 Codex worker 在仓库中继续 Golden Path。worker 不得递归调用 `story_os.py run`，而是使用底层 Story OS 工具。

需要正式生图时优先使用：

```bash
python episodes/_system/codex_subscription_image.py generate --prompt-file <prompt.txt> --output <candidate.png> --log <log.jsonl>
```

这个 backend 使用当前 Codex CLI 的 ChatGPT 登录态启动一次隔离 image-generation worker，不要求 `OPENAI_API_KEY`。当前 CLI 没有 image_generation 能力时必须记录工具阻塞，不得伪造候选图。

执行链：`恢复状态 → 去同质化/Story Gate → 真实性卡/锚点 → 三张校准 → 四张视觉准入 → Batch → 逐帧自审/最多一次返修 → 字幕 → Final QA → publish → SHA → 自动交付 ZIP`。

- originals / repairs / approved / publish 分离。
- subtitle_only 必须校验底图 SHA 不变。
- 已通过且 SHA 未漂移资产必须复用。
- `delegated_auto_review` 绝不能写成 `direct_user_review`。
- 自动交付 ZIP 不得伪造 Story/Visual/Release 的 `user_approved=true`。
- checkpoint：`<episode>/meta/runtime-checkpoint.json`。
