# Story OS V2.6.1｜本会话升级记录交接文档

> 日期：2026-09-05  
> 项目：`aigc-dali-cat`  
> 分支：`story`  
> 核心 Episode：`episodes/10_彼此的天上/02_玻璃另一边的手`  
> 会话目标：以《彼此的天上》EP002 作为 Story OS V2.6.1 第一次真实 Runtime Smoke Test，同时补齐 WORK / WEB / Codex 图像执行闭环。

---

# 0. 最重要的交接结论

本会话围绕 Story OS V2.6.1 做了三层升级设计和真实 Smoke Test：

1. **WORK Runtime 前期生产闭环**：Story Critic / Recent-5 / PREIMAGE / Handoff / Visual Lock 1+3。
2. **Hybrid Runtime**：本地 Story OS 冻结规则，GPT 网页端生成 + 实际像素审核 + 连续推进，最终一次 ZIP 回仓。
3. **Codex 图片执行 fallback**：仅图片执行层可显式切 Codex；Story / Contract / Gate 不交给 Codex 重写。

本会话中曾在工作区真实实现并验证 Hybrid Runtime、Web Execution State、Web Delivery、连续 Host Loop、Codex UTF-8 与图片回收等改造，并跑过相关回归。

**但截至本交接文档创建时，当前 checkout 已回到干净状态：**

- 当前分支：`story`
- 当前 HEAD：`aba66e6a9ee4f9e93aaba04bc6210ed7c6da3906`
- HEAD commit：`feat(episode): add 彼此的天上 EP002 preproduction assets`
- `git status`：clean
- EP002 当前 `story_os.py status`：`IDEA_LOCKED`
- `docs/Story_OS_V2.6.1_Hybrid_Runtime_正式架构方案_V1.0.md`：当前缺失
- `episodes/_system/web_delivery.py`：当前缺失
- `episodes/_system/web_execution_state.py`：当前缺失
- `story_os.py web-delivery`：当前 CLI 不存在

因此：

> **下面记录的 Hybrid / Web 连续生产 / Codex 执行器修复属于“本会话已经设计、实现、验证过，但当前 checkout 需要重新落盘”的升级成果。**

下一会话不得把这些内容误判为已经安装完成。

---

# 1. 本会话起始基线

本会话开始时仓库已经进入 Story OS V2.6.1 Product Runtime First 方向，基线 commit 包括：

- `faa0e26 feat(story-os): close WORK-first product runtime architecture`
- `aba66e6 feat(episode): add 彼此的天上 EP002 preproduction assets`

V2.6.1 原始核心规则：

- 默认 Runtime：`WORK`
- WORK / WEB 不得因为本机存在 `codex.exe` 就静默启动 Codex
- 本地 Codex 仅显式选择 `CODEX` 时允许
- Product Runtime 图片缺真实文件传输时：`HOST_ACTION_REQUIRED / HOST_WAIT`
- `meta/episode-state.json` 是唯一正式 Stage Authority
- Visual Lock 使用真实 **1+3 barrier**

EP002 的故事核心在本会话内要求保持不重写：

- 2023，中国大陆，川西山谷普通民宿
- 主角为 24 岁普通年轻情侣
- 唯一异常：持续降雨 / 降温 / 低云时，两处正常有人居住的空间短暂局部重叠，同一扇玻璃同时属于两边房间
- 禁止鬼怪、怪物、裂缝、组织解释、科学揭秘、实体穿越
- 结局回到现实复核：窗外只有无法站人的陡墙 / 斜坡，无平台、无脚印、无物理残留

---

# 2. EP002 前期 Smoke Test：本会话曾完成的工作

## 2.1 Fresh Story Semantic Critic

本会话曾对最终 Story + Storyboard 做 fresh `WORK_ISOLATED` Story Critic。

正式 review 结果：PASS。

绑定 SHA：

- Story SHA：`f6a4ddb633048f46f0d7e5011ab396910c11c7e9a079ce8a2cb989af28a5c2bf`
- Storyboard SHA：`7ad1fefcf2ba8fbbf59ff5eafe98f24b76ed3e6e4a26a59eb7f7025648c548df`

正式 review 曾落：

- `meta/story-semantic-review.json`
- `meta/runtime/reviews/story-semantic-attempt-1-request.json`

要求：旧 `.story-semantic-review.candidate.json` 不得直接冒充正式 PASS。

## 2.2 Recent-5 Fresh Review

曾完成 fresh Recent-5 语义对比，结果 PASS。

对比历史 Episode：

- 《瓶中世界》
- 《鳌太线·热汤》

EP002 与历史机制在九维比较中无近似命中，最大 similarity 曾记录为 0。

## 2.3 Story Lock / Stage

本会话曾通过：

- `validate_episode --target STORYBOARD_LOCKED`
- `machine_gate --target STORYBOARD_LOCKED`
- `evidence_gate --target STORYBOARD_LOCKED`

并曾将 EP002 正式推进到：

`STORYBOARD_LOCKED`

注意：**当前 checkout 已回到 `IDEA_LOCKED`，这一 Stage 结果现在不在当前工作区。**

---

# 3. PREIMAGE_COMPILE：本会话曾生成 / 锁定的合同

本会话曾完成完整 PREIMAGE_COMPILE，并通过 `production_readiness_v221.py --stage preimage`。

曾生成并验证：

## 3.1 Character Appearance Anchor

发现 derived anchor stale 后只重建派生缓存，未重写 Character Contract。

## 3.2 Capture Event Contract

`meta/capture-event-contract.json`

关键规则：

- Frame 01：P02 自拍 / 合影逻辑
- Frame 02–20：主要由 P01 使用普通手机记录
- 每帧包含 why_capture_now / device_position / subject awareness / operator state / framing / retained reason
- 每帧最多一个有因果来源的相机缺陷

## 3.3 World State

`meta/world-state.json`

曾验证 SHA：

`e1f3d8ac82e0647a78e7616bfd4b8db523915954efa12eb26f297b7ad155a384`

## 3.4 Temporal Continuity

`meta/temporal-continuity.json`

时序：

- F01：雨天下午
- F02：傍晚大雨
- F03–17：雨停、降温、低云、玻璃残留水膜
- F18–20：次日上午现实复核

## 3.5 Wardrobe Contract

`meta/wardrobe-contract.json`

锁定：

- P01：灰色上装 + 深灰休闲裤 + 普通运动鞋
- P02：浅灰上装 + 深色直筒裤 + 普通运动鞋

## 3.6 Environment / Impact Contract

曾把 20 帧 narrative / impact directive 编译进 `story-gates.json`。

Visual Impact 核心：

- F01：普通生活 baseline
- F03：第一次明显异常
- F08：P02 擦内侧雾气
- F09：另一边成年人擦外侧水膜回应
- F10–13：异常升级
- F14：高潮，另一边成年人把身边孩子迅速拉开
- F18–20：现实复核 / residue / leaving payoff

重要规则：Narrative escalation 不得错误串行化所有 pixel generation。

## 3.7 Resolved Frame Contracts

曾完成 20 帧 resolved frame contract：

`meta/runtime/contracts/frames/01.json ... 20.json`

Frame 01 曾绑定：

`bba10b9ed82fdf46fd274e514db84e1d820488819d1c6b2a69e2655d052d03e0`

## 3.8 Prompt Packages

曾编译 20 个 production prompt + prompt package，默认：

- model：`gpt-image-2`
- quality：`high`
- 4:5 / 1080×1350 目标画布

---

# 4. 本会话发现并修过的 Story OS Runtime Bug

以下属于本次 Smoke Test 最有价值的工程发现。

## 4.1 Resource Library 地点误匹配

### 问题

EP002 明确是“川西山谷普通民宿”，旧 resolver 却因为泛化 tag `village_home` 错误匹配：

`LOC_NORTHWEST_VILLAGE`

把“西北农村”视觉资源错误注入川西 Episode。

### 本会话修法

曾修改：

`episodes/_system/resource_library.py`

加入更严格的 specific fuzzy matching，并升级 resolver cache version。

目标规则：

- `游乐园` ↔ `废弃游乐园` 可以具体模糊命中
- 单独的 `village_home` 不得覆盖显式 `川西山谷小镇普通民宿`

曾自测：PASS。

---

## 4.2 WORK Image Scheduler 绕过 1+3 Barrier

### 问题

旧 `image_scheduler.run_scheduler()` 在 WORK / WEB 分支里直接取全部 `queued` items 生成 Product Request，导致：

- Frame 01 baseline 未审核
- 03 / 10 / 14 已经一起进入真实 Product Request

这违反 Visual Lock 1+3。

### 本会话修法

曾修改：

`episodes/_system/image_scheduler.py`

由：

`all queued items`

改成：

`ready_items()` + max workers 限制。

修复后真实计划：

- ready：Frame 01 only
- blocked：03 / 10 / 14 depends_on 01

曾运行 scheduler self-test：PASS。

---

## 4.3 Visual Lock 旧 schema 兼容问题

旧 EP002 `story-gates.json` calibration 缺：

- `schema_version: 2`
- `policy: four_admission_v21`

导致 V2.1+ Visual Lock 被错误判成“不需要”。

本会话曾按模板迁移为：

```json
{
  "schema_version": 2,
  "policy": "four_admission_v21",
  "items": []
}
```

然后成功生成 1+3 plan：

- V-B：01 ordinary baseline
- V-A：03 first major anomaly
- V-W：10 worst capture condition
- V-H：14 high impact

---

# 5. Hybrid Runtime：本会话正式定义的新架构

本会话最终确认用户真正需要的不是：

`网页生图 → 每张回本地 → 本地审核`

而是：

> **本地 Story OS 规则权威 → GPT 网页端生成 + actual-pixel 审核 + 自动返修 + 连续推进 → 全部 PASS 后一次性 ZIP → 最终回仓只做 fail-closed 验收与归档。**

正式模式名：

`WORK_PREIMAGE__WEB_EXECUTE_AND_REVIEW__FINAL_IMPORT`

## 5.1 职责拆分

### Local Story OS

负责：

- Story / Storyboard Authority
- Character / World / Temporal / Wardrobe / Capture Event
- Resolved Frame Contracts
- Visual Profile
- Review checks
- dependency graph
- repair budget
- 最终 Episode State

### GPT Web

负责：

- 图片生成
- actual-pixel review
- repair
- barrier release
- 下一批继续生成
- 最终 ZIP 组装

### FINAL_IMPORT

只负责：

- ZIP 安全校验
- request fingerprint
- asset SHA
- exact-canvas
- Frame Contract drift
- WEB_ISOLATED review evidence
- ledger / lineage
- deterministic gates
- 正式 Stage 落地

**FINAL_IMPORT 不再是首次内容审核点。**

---

# 6. Hybrid Runtime 本会话曾实现的代码结构

本会话曾新增：

## 6.1 `episodes/_system/web_delivery.py`

能力曾包括：

- `web-delivery prepare`
- `show`
- `web-state`
- `record-web-state`
- `export-trace`
- `verify`
- `import`
- `self-test`

支持：

`--scope full-production`

即一次 PREIMAGE 后冻结完整 20 帧 Web Production Session。

## 6.2 `episodes/_system/web_execution_state.py`

定义非 Stage Authority 的网页执行状态，例如：

- `VISUAL_LOCK_BASELINE`
- `VISUAL_LOCK_PARALLEL3`
- `VISUAL_LOCK_FINAL_REVIEW`
- `PRODUCTION_BATCH`
- `PRODUCTION_FINAL_REVIEW`
- `RELEASE_PREP`
- `FINAL_EXPORT`
- `WAIT_FINAL_IMPORT`

## 6.3 Web Execution Trace

最终 ZIP 要求包含：

- `manifest.json`
- `request.json`
- `web-execution-trace.json`
- exact-canvas final PNG
- SHA-bound review evidence

Trace 必须能证明顺序：

`01 PASS → 03/10/14 → Visual Lock PASS → Production → Full Frame Review PASS → WAIT_FINAL_IMPORT`

不能只在 manifest 最后伪造一组 PASS。

---

# 7. Web Host Loop：解决“生一张就停”

本会话实际发现：即使有 `web-execution-state.next_action`，如果没有 Host Loop 消费它，网页端仍然会：

`生图 → 当前 assistant turn 结束 → 等用户继续`

用户明确要求：

> 全程不想再手工发“继续”。

因此本会话曾把正式规则补成：

```text
image_generation_is_not_a_terminal_action = true
continue_without_user_prompt = true
```

每次生成后必须：

1. inspect actual pixels
2. record WEB_ISOLATED decision
3. PASS → 立即消费 next_action
4. REPAIR → 自动修复后重新审核

只有以下状态允许真正停止：

- `REPAIR_REQUIRED`（超预算）
- `BLOCKED`（硬阻断）
- `WAIT_FINAL_IMPORT`

---

# 8. 安全误拦自动改写规则

用户在本会话明确要求：

如果正常剧情因为某些词或未成年人相关措辞被图片模型误拦，不要停下来让用户继续。

正式策略：

`良性场景安全拦截 → 自动做安全措辞改写 → 重生 → 重审`

原则：

- 不改变 Story 核心
- 不绕过真实政策
- 只降低不必要的高风险表述
- 不必要时避免突出未成年人、伤害、血迹、威胁、惊悚措辞
- 连续误拦允许自动做更保守表达
- 只有真正 hard policy block / 超预算才停

---

# 9. Codex 只负责图片执行的 fallback 设计

网页端在 EP002 实测中发生过明显语义跑偏：

- 本应继续普通民宿 / 空间重叠故事
- 连续生成成“孩子隔玻璃、学校 / 机构环境”类画面

因此本会话确认一条 fallback：

> **可以显式切 Codex 做图片执行，但 Codex 不得接管 Story / PREIMAGE / Gate。**

正确职责：

- Story OS：继续锁 Story / Frame Contract / Visual Lock / Review
- Codex：只执行锁定 prompt + Frame Contract 的图片生成
- 生成后仍走 Story OS 的 Ledger / Baseline / Visual / Semantic Review

禁止：

`CODEX full-auto` 因派生 SHA 漂移而重新进入 `STORY_REVIEW_REQUIRED` 并重跑故事。

本会话实测曾发生这个问题，因此后续必须使用“image execution only”，不要把 Codex 当全流程 owner。

---

# 10. Codex 图片执行器本会话发现的两个 Windows Bug

## 10.1 中文 Prompt stdin 非 UTF-8

### 现象

Codex 报：

`Failed to read prompt from stdin: input is not valid UTF-8`

### 原因

`codex_subscription_image.py` 的 `subprocess.run(... input=..., text=True)` 未显式指定 stdin encoding，Windows 默认编码可能为 GBK。

### 本会话修法

曾在 `episodes/_system/codex_subscription_image.py` 中对 subprocess stdin / text I/O 显式使用：

`encoding="utf-8"`

修后 backend self-test：PASS。

---

## 10.2 Codex 已生图，但 worker 无法复制 `out.png`

### 现象

Codex 日志显示图片已经生成，但 worker 执行文件复制失败：

`CreateProcessWithLogonW failed: 1385`

最终 worker 说未能确认 `out.png`。

实际生成图存在于：

`C:\Users\<user>\.codex\generated_images\<thread_id>\*.png`

### 本会话修法

曾增强：

`episodes/_system/image_artifact_collector.py`

逻辑：

1. 从 Codex JSON log 解析 `thread_id`
2. 只扫描：
   `~/.codex/generated_images/<thread_id>`
3. 找最新真实 PNG/JPEG
4. 回收为正式 candidate

不得扫描整个 HOME，避免并行 worker 拿错图。

实测成功找回：

`exec-e29c675a-80b8-4dea-b73b-74d8e08da8d4.png`

之后 Frame 01 scheduler 曾进入 `generated`。

---

# 11. EP001 → EP002 人物与画风连续性新要求

用户在本会话后段明确补充：

## 11.1 Frame 01 必须是情侣合影

不是只拍环境 / 侧后脑 / 驾驶手。

第一张应承担：

- 社交关系建立
- 男女主 identity master
- EP001 → EP002 视觉连续性
- Visual Lock baseline

推荐镜头：

> 雨天自驾途中，女友用普通手机前置自拍，男友在驾驶位自然入镜；两人都是普通年轻情侣，不摆拍、不网红、不电影感。

## 11.2 男女主必须和 EP001 保持一致

EP002 不能只做到“普通年轻男女”，而应明确继承 EP001：

- 同一个男主
- 同一个女主
- 脸型 / 年龄感 / 发型 / 气质连续
- 服装允许 Episode 内合理换装，但身份必须稳定

## 11.3 画风必须延续 EP001

继续保持：

- 真实手机相册感
- 中国大陆普通生活环境
- 克制、低饱和
- 非影视灯光
- 非广告大片
- 非 AI 精修脸
- 自然肤质、自然抓拍

本会话曾对一张“雨中车内侧后视角”候选评估：

- 画风方向约 8.6/10
- 场景气质约 8.8/10
- 人物身份锚定约 6.7/10

结论：可以作为环境 / 风格参考，但不适合作为最终 identity baseline。

随后用户明确要求重做为情侣合影版。

---

# 12. 本会话曾达到的测试结果

在 Hybrid Runtime 改造工作树仍存在时，曾跑过：

- 18 related tests：PASS
- Story OS Config：VALID
- Story OS Doctor：`errors=0 warnings=0`
- Image Scheduler self-test：PASS
- Visual Lock self-test：PASS
- `git diff --check`：PASS

还曾确认：

`runtime_dag.py` 的 Windows GBK 修复是用户原有改动，本会话不得覆盖：

- plan / show JSON 使用 `ensure_ascii=True`
- 防止 GBK console 因历史 U+FFFD 等字符崩溃

---

# 13. 当前仓库实际状态（交接时复核）

复核时间：2026-09-05 21:09 +08:00 左右。

```text
branch: story
HEAD: aba66e6a9ee4f9e93aaba04bc6210ed7c6da3906
commit: feat(episode): add 彼此的天上 EP002 preproduction assets
git status: clean
EP002 story_os status: IDEA_LOCKED
```

当前缺失：

- `docs/Story_OS_V2.6.1_Hybrid_Runtime_正式架构方案_V1.0.md`
- `episodes/_system/web_delivery.py`
- `episodes/_system/web_execution_state.py`
- `story_os.py web-delivery` CLI
- 本会话 Hybrid Runtime 的 runtime-contract / WORK / WEB / START_HERE / SKILL 修改
- Codex UTF-8 stdin 修复
- generated_images thread recovery 修复
- 本会话后续生成的 Frame 01 candidate / baseline review / queue state

因此当前仓库不能直接按“Hybrid 已安装”继续。

---

# 14. 下一会话恢复顺序（强烈建议）

不要一上来重新创作故事。

建议按以下顺序恢复：

## Step 1：确认当前 commit / clean state

```bash
git status --short --branch
git log -5 --oneline
```

## Step 2：重新安装 Hybrid Runtime

优先重新落盘本会话已经验证过的设计：

- `web_delivery.py`
- `web_execution_state.py`
- `story_os.py web-delivery` CLI
- `runtime-contract.json`
- `WORK.md`
- `WEB.md`
- `START_HERE.md`
- `SKILL.md`
- external WEB_ISOLATED finalizer
- web execution trace verifier
- final import verifier

正式模式仍使用：

`WORK_PREIMAGE__WEB_EXECUTE_AND_REVIEW__FINAL_IMPORT`

## Step 3：重装两个 Codex Windows 修复

- stdin UTF-8
- thread-scoped generated_images recovery

## Step 4：重新跑相关测试

至少：

- Hybrid tests
- Config VALID
- Doctor 0/0
- Image Scheduler self-test
- Visual Lock self-test
- Codex image backend self-test
- Artifact collector self-test

## Step 5：恢复 EP002 前期

以当前 repo 真实 Authority 为准重新验证：

- Story / Storyboard SHA
- Character Contract
- NO-ANOMALY TEST
- fresh Story Semantic Review
- Recent-5
- PREIMAGE
- Handoff
- Resolved Frame Contracts

如果权威 Story / Storyboard SHA 与本交接记录一致，可重建 derived artifacts，不要重写 Story 核心。

## Step 6：重新做 Visual Lock Frame 01

必须遵守最新用户要求：

> **Frame 01 = EP001 同一对男女主的雨天自驾情侣合影 / 自拍。**

审核重点：

- EP001 男主身份连续
- EP001 女主身份连续
- 两张脸都足够做 identity master
- 同时仍是普通手机相册照，不是写真
- 画风与 EP001 一致

Frame 01 actual-pixel PASS 后才放行：

- 03
- 10
- 14

## Step 7：后续全自动

用户已经明确授权：

> **不要再让用户逐步发送“继续”。**

默认执行：

`generate → review → repair if needed → re-review → consume next_action → next frame/batch`

只有：

- hard policy block
- repair budget exhausted
- 真正不可恢复技术阻断
- WAIT_FINAL_IMPORT

才允许停止。

---

# 15. 下一会话禁止事项

1. 不得因为当前 EP002 又是 `IDEA_LOCKED` 就擅自重写已锁故事核心。
2. 不得把旧 candidate review 直接冒充 fresh PASS。
3. 不得在 Frame 01 未实际像素 PASS 前生成 03 / 10 / 14 正式 Visual Lock。
4. 不得让网页端生成一张图后就结束整个执行链。
5. 不得把 Codex full-auto 当 Hybrid 的替代品。
6. 不得让 Codex 因 derived SHA 漂移去重写 Story。
7. 不得把安全误拦直接当 Episode BLOCKED；良性场景先自动安全改写重试。
8. 不得把“同类普通年轻男女”当成 EP001 人物连续性通过。
9. 不得覆盖用户已有的 `runtime_dag.py` Windows GBK 修复。
10. 未经用户明确要求，不 commit、不 push。

---

# 16. 大白话总结

这次会话真正解决的是：

> Story OS 前期已经很完整，但真正进入“出图”以后，WORK 网页端、文件回传、网页审图、连续执行、Codex fallback 之间还有断层。

本会话把正确方向跑清楚了：

```text
本地 Story OS 锁故事和规则
        ↓
网页 / Codex 只负责真实图片执行
        ↓
图片出来立即 actual-pixel 审核
        ↓
不过就自动修，不问用户“继续吗”
        ↓
PASS 自动往下一张 / 下一批
        ↓
最终只把 PASS 图和证据一次性回仓
        ↓
本地做 SHA / Contract / Ledger / Gate 归档
```

同时通过 EP002 真实 Smoke Test 找到了几个只有正式生产才会暴露的 Bug：

- Resource 地区误匹配
- WORK scheduler 绕过 1+3 barrier
- Visual Lock calibration schema 老旧
- 网页端只有状态、没有 Host Loop
- 网页图片语义跑偏时缺 fallback
- Windows Codex stdin 非 UTF-8
- Codex 已生图但无法复制 `out.png`
- EP002 Frame 01 对 EP001 人物 identity 锚定不足

这些就是下一版 Story OS 真正值得固化的升级内容。

---

# 17. 建议版本定位

如果下一会话把本交接中的 Hybrid / Host Loop / Codex Image Executor 修复正式重新安装、测试并 commit，建议不要继续偷偷叫纯 V2.6.1。

可考虑：

- `Story OS V2.6.2 Hybrid Runtime Closure`

或保持主版本不变，但增加 capability revision：

- `V2.6.1-H1 Hybrid Delivery`
- `V2.6.1-H2 Continuous Web Host Loop`
- `V2.6.1-H3 Codex Image Executor Recovery`

核心不是版本号，而是必须让 manifest / runtime-contract 明确声明这些 capability 是否真实安装，避免下一次再出现“方案里有，checkout 里没有”的状态错觉。
