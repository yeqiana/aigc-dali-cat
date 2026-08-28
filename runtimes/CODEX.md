# CODEX Runtime V2.0.2

Codex 是文件原生全自动生产 runtime。用户明确“全自动执行”后，正常节点不反复询问继续。

一键入口：

```bash
python episodes/_system/story_os.py run <episode_dir> --full-auto
```

V2.0.2 的“完成”不再等于 Codex worker 进程返回 0。worker 返回后必须执行 deterministic postflight；最终只允许：`COMPLETE / PAUSED / BLOCKED`。

正式生图使用：

```bash
python episodes/_system/codex_subscription_image.py generate-for-frame <episode_dir> --frame NN --prompt-file <prompt.txt> --output <candidate.png> --log <log.jsonl>
```

backend 会：订阅态 image_generation → 保存 raw → 读取 production ledger canvas → 规范化成精确 1080×1350 或 1080×1920 → 再交给 production ledger。

全自动批准必须使用 delegated provenance：

```bash
python episodes/_system/delegated_approval.py record <episode_dir> story_lock
python episodes/_system/delegated_approval.py record <episode_dir> visual_lock
```

它不会写 `user_approved=true`。Evidence Gate 接受两条真实路径：`direct_user_review` 或 `delegated_auto_review + continuous_execution_authorized`。

最终 delegated ZIP 必须使用真实 publish 资产，禁止把 approved base 静默当 publish。ZIP 必须包含正文、封面、字幕、发布文案、传播卡、release manifest、text audit、checksums 和 delegated report。
