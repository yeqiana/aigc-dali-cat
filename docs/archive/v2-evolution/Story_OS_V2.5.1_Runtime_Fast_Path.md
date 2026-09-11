# Story OS V2.5.1｜Runtime Fast Path

目标：只优化运行时，不改变 Story / Visual / Production / Release 创作门禁。

## 本次从真实《仲夏夜惊魂》执行中确认的问题

- 修正后的活跃执行约 12 小时，而图片后端资源时间约 43.7 分钟；主要耗时在控制层恢复、探测、复审和候选循环。
- Context 压缩/新会话后反复重读仓库、ledger、queue、工具源码。
- Rolling Review 在视觉能力未验证时仍可能给出 REPAIR_NOW，引发误返修。
- 单帧在正式 ingest 前可能反复尝试大量原始候选。

## V2.5.1 Fast Path

1. `runtime_capability_cache.py`：Runtime 能力 6h 缓存；不主动跑昂贵模型探针。
2. `runtime_resume_capsule.py`：恢复上下文先读一个 compact capsule，不重新理解整个仓库。
3. `rolling_frame_review.py`：视觉能力没有显式 verified 时，只能 UNCERTAIN/DEFER_TO_FINAL，禁止 REPAIR_NOW。
4. `raw_candidate_budget.py`：Original/Repair/Exception 原始候选默认各最多 2 次；技术失败不计。
5. `runtime_fast_path.py`：统一 `prepare/resume/capabilities/candidate/slo` 入口。
6. 90/120 分钟 SLO：GREEN <=90m，YELLOW <=120m，RED >120m；只做遥测，不阻断发布。

## 最简单使用

```bat
python episodes/_system/story_os.py fast-path prepare "episodes/XX_系列/01_剧集"
python episodes/_system/story_os.py run "episodes/XX_系列/01_剧集" --full-auto --resume
```

新上下文/压缩恢复：

```bat
python episodes/_system/story_os.py fast-path resume "episodes/XX_系列/01_剧集"
```

视觉 worker 真实探针成功后，记录一次：

```bat
python episodes/_system/story_os.py fast-path capabilities "episodes/XX_系列/01_剧集" --vision verified
```

每次主会话准备再试一个原始候选前：

```bat
python episodes/_system/story_os.py fast-path candidate "episodes/XX_系列/01_剧集" --frame 10 --kind repair --reason "retry visual reading"
```

第三次会直接返回 `STOP_IMAGE_LOOP`。
