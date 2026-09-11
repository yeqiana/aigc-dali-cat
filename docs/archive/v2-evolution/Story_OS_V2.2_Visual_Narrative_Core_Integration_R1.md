# V2.2 Visual Narrative Core Integration R1

这不是外围规则包，而是主链集成包。

实际修改：

- `frame_contract.py`
  - Visual Narrative Core 纳入 frame hash material
  - 纳入 prompt_contract
  - 因此改变正式生成请求并被 Production Ledger SHA 绑定

- `visual_lock_v21.py`
  - Visual Lock 前先验证 Visual Narrative Core
  - 1+3 实际像素审查新增 Camera Authorship / Moment / Defect / Screen Physics

- `codex_subscription_image.py`
  - 不覆盖
  - 安装时做语义接口检查
  - 当前后端已经把 `frame_contract["prompt_contract"]` 送进 image worker

- `rolling_frame_review.py`
  - 增加 ghost camera / result-only / narrative redundancy / defect physics / screen physics 预审

- `frame_semantic_review.py`
  - 增加 V2.2 硬检查与 issue code

- `incremental_frame_review.py`
  - 与全量终审保持相同 V2.2 标准

安装：

```bat
python -X utf8 install.py --repo D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat
```

验证某集：

```bat
python -X utf8 scripts/story_visual_narrative.py verify "episodes/你的Episode"
python -X utf8 scripts/story_visual_narrative.py show "episodes/你的Episode" --frame 10
```

旧 Episode 的 `shot-progression-review.json` 若 schema < 2，不会被强制启用。
