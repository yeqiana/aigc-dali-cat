# Story OS V2.6.1 全链路 Mock Runtime 性能基准

日期：2026-09-06  
用途：作为 V2.6.1 新规则、Product Runtime First、Caption/Image Audit V2.6.1、Release Critic 缩图策略后的本地运行性能基准。

## 1. Mock Story

标题：**《凌晨一点，返乡大巴多停了一站》**

设定：
- 主角：二十多岁的普通年轻男性；
- 进入方式：夏末深夜乘大巴返乡；
- 异常载体：后视镜、车窗反光、重复路灯、地图上不存在的旧收费站；
- Visual Lock：1+3；
- 总帧数：20；
- 图片比例：1080×1350 / 4:5；
- 字幕：左侧中部、最多 2 行；
- Release：Caption/Image Audit 使用 5 图分块；Final Release Critic 只保留关键发布语义图。

## 2. Mock 边界

本次只 Mock 外部昂贵能力：

- 图片生成模型 → `MOCK_SYNTHETIC_PNG`，生成真实 1080×1350 PNG；
- 独立视觉/Critic 模型 → 固定返回 PASS。

以下链路执行真实 Story OS 代码：

- Stage performance ledger；
- 20 张真实 PNG 文件写入与 SHA；
- 1+3 Visual Lock 布局；
- Production Ledger；
- Text Audit；
- canonical subtitle renderer；
- subtitle-layout-audit；
- Caption/Image Audit V2.6.1 dirty 判断、5 图分块、最终发布图 SHA 绑定；
- Caption Audit 二次执行 NOOP/REUSE；
- Release artifact SHA 集；
- Release Critic 输入裁剪；
- Release semantic schema/hash 校验；
- Governance 校验；
- Final Candidate Snapshot build + verify；
- 最终状态 `PUBLISH_READY`；
- Episode Performance Critical Path。

因此本报告衡量的是 **Story OS 本地编排 / 文件 / SHA / 渲染 / Gate 开销**，不包含真实网络、GPT 推理、gpt-image-2 生图时间。

## 3. 三次稳定性复跑

三次完整链路墙钟：

| Run | Total Wall |
|---|---:|
| 1 | 2.720 s |
| 2 | 2.709 s |
| 3 | 2.766 s |
| **Median** | **2.720 s** |

波动约 0.057 秒，Mock 本地链路稳定。

## 4. Stage 中位耗时

| Stage | Median |
|---|---:|
| CREATIVE_STORY | 0.001566 s |
| PREIMAGE_COMPILE | 0.009289 s |
| VISUAL_LOCK | 0.072017 s |
| PRODUCTION | 0.271713 s |
| RELEASE | **2.320477 s** |

说明：Mock 模式下外部模型耗时被移除，因此 CREATIVE / PREIMAGE / 图片生成只剩本地文件与元数据成本；真实生产不能直接用以上数字估算模型时间。

## 5. Release 子步骤中位耗时

| Release 子步骤 | Median |
|---|---:|
| Text Audit | 0.001143 s |
| 20 图 canonical subtitle render | **1.553624 s** |
| 20 图 Caption/Image Audit 本地部分 + Mock Critic | 0.166459 s |
| Visual Freeze + Compliance evidence | 0.036050 s |
| Release hashes + semantic schema validation | 0.101403 s |
| Release verify | 0.099423 s |
| Final Snapshot build + verify | **0.336372 s** |

### 本地主要耗时排序

1. 字幕渲染 20 图：约 1.55 秒；
2. Final Snapshot build + verify：约 0.34 秒；
3. Caption/Image Audit 本地 SHA/dirty/证据处理：约 0.17 秒；
4. Release hash + verify 合计约 0.20 秒。

以上都远低于真实模型调用耗时，不构成分钟级卡顿来源。

## 6. Caption/Image Audit 验证

首次审核实际分块：

- 01–05
- 06–10
- 11–15
- 16–20

结果：**严格 4 × 5 图**。

二次对相同成片执行：

- dirty frames：0；
- Critic chunk calls：0；
- NOOP/REUSE 中位耗时：**0.157893 s**。

结论：相同最终图 + 相同字幕 SHA 不会重复触发多模态审核。

## 7. Release Critic 输入规模

全 Release artifact role：26。  
Final Release Critic role：9。  
其中图片 role：**6**：

- cover
- body01
- body02
- body03
- climax
- payoff

因此不会再把 20 张正文图一次性塞进最终 Release Critic。

全帧字幕遮挡检查由 Caption/Image Audit 的 4 × 5 图 SHA-bound 审核承担。

## 8. Final 状态

本轮完整 Mock 验收：

- 20/20 Mock images generated：PASS
- Visual Lock 1+3：PASS
- Subtitle Layout：PASS
- Caption/Image Audit：PASS
- Caption 5×4 chunking：PASS
- Caption second-run NOOP：PASS
- Release Semantic：PASS
- Governance：PASS
- Final Release Critic 6 key images：PASS
- Final Candidate Snapshot build：PASS
- Final Candidate Snapshot verify：PASS
- Episode Performance final status：`PUBLISH_READY`

## 9. 性能结论

### 当前没有发现本地编排级明显卡顿

V2.6.1 本地完整 Mock Critical Path 中位值约 **2.72 秒**。这说明新增导演规则、字幕规则、SHA 绑定、增量审计和 Final Snapshot 本身不会造成分钟级或小时级卡顿。

真实生产的主要耗时仍将来自：

1. CREATIVE / PREIMAGE 的真实模型推理；
2. gpt-image-2 图片生成；
3. Visual Lock / Frame Critic / Caption Critic 的真实多模态调用；
4. 网络、Host Wait、技术失败和重试。

### V2.6.1 建议回归阈值

后续新增规则后，重复本 Mock Benchmark：

- Median total > 3.4 s：警告（约 +25%）；
- Median total > 4.1 s：性能回归（约 +50%）；
- Caption reuse 出现任何 Critic chunk：P0 回归；
- Final Release Critic 图片 role > 6：检查是否重新引入全量多图审核；
- Caption 首次审核 chunk size > 5：P0 回归。

## 10. 对真实生产的意义

本报告不能把 2.72 秒理解为真实一篇故事只需 2.72 秒。

它证明的是：**去掉外部 AI 耗时之后，Story OS 本地流程只有秒级开销。**

因此下一次真实新篇如果仍然需要 2–3 小时，应优先从真实模型调用次数、单次生图耗时、Host Wait、失败重试、重复 Critic 请求、图片并发利用率中找原因，而不是继续怀疑 Story OS 的 JSON/SHA/Gate 本地逻辑。
