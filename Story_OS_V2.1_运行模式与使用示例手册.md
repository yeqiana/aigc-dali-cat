# Story OS｜Codex 最简完整生产手册

## 第 1 步：从 MD 初始化整集生产资产

适用于：现在手上只有一个故事 MD。

给 Codex：

```text
读取当前 aigc-dali-cat 仓库的 story 分支。

源文档：
episodes/12_千寻/千寻.md

为《千与千寻真人版》建立 SPIRITED_AWAY_EP001。

本次只做 Episode Bootstrap + Preproduction，不生产正式剧情帧。

要求：

1. 从源 MD 中确定 EP01 的剧情范围；
2. 不引用任何其他仓库、旧项目、ohmyphoto 或本机历史资产；
3. 所有新资产只能写入当前 aigc-dali-cat/story；
4. Visual Profile 使用：
   SPIRITED_AWAY_LIVE_ACTION_V1

5. 为 EP001 建立完整机器入口资产，包括：
   - Episode Blueprint
   - EP01 Chapter Lock
   - Visual Profile Lock
   - Character Contract
   - Location Contract
   - Device / Prop Contract
   - Asset Manifest
   - Frame Plan / Storyboard
   - Resolved Frame Contracts

6. 根据 EP01 实际需要，重新制作并锁定：
   - Character Master
   - Location Master
   - Device / Prop Master

7. 每个母版必须记录：
   - 当前路径
   - SHA
   - Contract 绑定
   - Authority 来源

8. 禁止搜索或复用当前 story 分支之外的资产。

9. 完成后自检全部入口资产。

最后只告诉我：
- EP001 最终目录
- Chapter Lock 是否 PASS
- Visual Profile 是否锁定
- Character / Location / Device Master 是否全部完成
- 是否 READY_FOR_SMOKE_TEST

不要进入正式 Production。
```

完成后的目标状态：

```text
MD
↓
EP001
↓
Blueprint
Chapter Lock
Visual Profile
Asset Manifest
Contracts
Master Assets
Frame Contracts
↓
READY_FOR_SMOKE_TEST
```

---

## 第 2 步：开发者 Validate

第 1 步完成后给 Codex：

```text
读取当前 story 分支。

验证 SPIRITED_AWAY_EP001。

本次只做开发者 Validate，不生成任何图片。

检查：

1. Episode Blueprint
2. EP01 Chapter Lock
3. SPIRITED_AWAY_LIVE_ACTION_V1
4. Character Master
5. Location Master
6. Device / Prop Master
7. Asset SHA / Contract Binding
8. Resolved Frame Contracts
9. 所有 Authority 是否只来自当前 story 分支

禁止：
- 搜索其他仓库
- 自动补旧资产
- 修改剧情
- 重新生成母版

有任何缺失立即停止。

最后输出：

VALIDATE_PASS

或者明确的失败原因。
```

这里应该很快，因为：

```text
0 张图片
```

---

## 第 3 步：Smoke Test 单图测试

Validate PASS 后：

```text
读取当前 story 分支。

对 SPIRITED_AWAY_EP001 执行开发者 Smoke Test。

只测试 Frame 01。

要求：

1. 严格读取已经锁定的：
   - EP01 Chapter Lock
   - SPIRITED_AWAY_LIVE_ACTION_V1
   - Character Master
   - Location Master
   - Device / Prop Master
   - Frame 01 Resolved Frame Contract

2. 只生成 1 张正式规格测试图。

3. 不运行：
   - Concept
   - Story Build
   - Story Critic
   - Storyboard 重建
   - Character 重建
   - Location 重建
   - Full Production
   - Release

4. 禁止读取当前 story 分支之外的任何资产。

5. 记录：
   - Smoke Test 开始时间
   - 前置验证耗时
   - 图片模型调用耗时
   - 总耗时

6. 对生成图检查：
   - 真人电影质感
   - SPIRITED_AWAY_LIVE_ACTION_V1 是否生效
   - 人物母版一致性
   - 地点母版一致性
   - 道具母版一致性
   - Frame Contract 是否满足

最后告诉我：

SMOKE_TEST_PASS / FAIL

以及：
- 总耗时
- 图片生成耗时
- 失败项
- 测试图路径

只生成这一张，不进入下一阶段。
```

这一步就是你的：

```text
单元测试 / Integration Smoke Test
```

---

## 第 4 步：正式全自动生产

Smoke Test 确认效果正确后：

```text
读取当前 story 分支。

继续 SPIRITED_AWAY_EP001。

Smoke Test 已通过。

严格沿用已经锁定的：

- EP01 Chapter Lock
- SPIRITED_AWAY_LIVE_ACTION_V1
- Character Master
- Location Master
- Device / Prop Master
- Resolved Frame Contracts

禁止：
- 重写剧情
- 重新做 Concept
- 重做已经批准的母版
- 切换 Visual Profile
- 使用任何外部仓库资产

从正式 Visual Lock 开始继续。

按 Story OS 当前正式流程完成：

Visual Lock 1+3
→ Production
→ Rolling Review
→ 必要返修
→ Final Frame Review
→ 字幕
→ 标题
→ 简介
→ Release
→ Final Candidate Snapshot

一直做到 PUBLISH_READY。

除非出现：
- Authority SHA 不一致
- 锁资产缺失
- 无法安全继续的 Runtime 故障

否则不要中途询问我。
```

---

# 以后只记这 4 步

```text
① MD → Bootstrap
        ↓
② Validate
        ↓
③ Smoke Test 1张
        ↓
④ Full Production
```

其中：

**Bootstrap** = 创建生产入口和母版资产。

**Validate** = 不生图，检查机器资产是否完整。

**Smoke Test** = 只生 1 张，测试真实生产链路。

**Full Production** = 正式做到 PUBLISH_READY。

---

# 《千与千寻 EP001》现在应该这样开始

第一条直接给 Codex：

```text
读取 story 分支。

以：
episodes/12_千寻/千寻.md

为唯一故事源。

从零初始化：
SPIRITED_AWAY_EP001

只做 Episode Bootstrap + Preproduction。

使用：
SPIRITED_AWAY_LIVE_ACTION_V1

所有 Character / Location / Device Master 必须在当前 story 分支重新建立。

禁止搜索、引用或迁移 ohmyphoto 以及任何外部旧资产。

做到 READY_FOR_SMOKE_TEST 后停止。
```

这就是你现在最适合的生产入口。
