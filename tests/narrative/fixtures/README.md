# StoryOS Narrative QA Fixtures

> Schema: v1  
> 建立日期：2026-09-18  
> 性质：研究/回归资产，不是当前 Production Gate，不改变任何 Episode 状态。

## 目标

把真实生产中已经出现过的“剧情、字幕、画面证据、转场、连续性、Reference”问题固化成可复用正例、反例和边界例，供后续 Story Agent、Storyboard、Frame Contract、Prompt Compiler、Reviewer 改造时做语义回归。

当前阶段 **只建立 Fixture，不新增 Narrative Gate，不修改 Runtime/Workflow/Scheduler**。

## Fixture 口径

- `positive`：应该通过，防止新规则误杀已成立的表达。
- `negative`：应该失败，防止历史真实问题复发。
- `boundary`：不能机械判失败，用于控制误报。
- `real`：直接来自 StoryOS 历史/当前生产证据。
- `synthetic_mutation`：以真实案例为底本，只改一个关键条件形成标准反例。

每条 Fixture 记录：

- `source_episode`：来源剧集。
- `source_evidence`：证据路径/帧。
- `scenario`：最小可理解场景。
- `expected`：未来 Narrative QA 应给出的判定。
- `current_coverage`：StoryOS 当前是否已经覆盖。
- `future_capability`：这条 Fixture 主要约束哪个 VNext 能力。

## 文件

| 文件 | 范围 |
|---|---|
| `plot.json` | 因果、揭露顺序、信息增量、高潮形式 |
| `caption.json` | 字幕支持、越界解释、画面外旁述、时间语义 |
| `visual_evidence.json` | Expected Evidence、Forbidden Evidence、证据强度 |
| `transition.json` | 相邻帧动作/摄影者/状态桥接 |
| `continuity.json` | 时间、环境、衣着、dirty propagation、稳定状态 |
| `reference.json` | Required Anchor 执行、authority、未来 inherit/ignore |

## 使用原则

1. Fixture 的 `expected` 是回归事实，不允许为了让新实现“全绿”而反向改期望。
2. 历史负例已经修复的，必须保留“修复前 FAIL + 修复后 PASS”成对案例。
3. 当前还没有自动判别器的 Fixture 可以先处于 `design_only`，不能伪装成已自动覆盖。
4. Fixture 不直接依赖内容仓库实时路径；路径只作为 provenance，核心输入必须自包含。
5. 后续若接自动测试，优先采用确定性规则；只有确实需要看图的项目才进入 actual-pixel critic。

