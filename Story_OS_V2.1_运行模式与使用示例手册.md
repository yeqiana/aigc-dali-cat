# Story OS V2.1｜运行模式与使用示例手册

> 适用版本：Story OS V2.1 + Runtime Optimization R2  
> 目标：统一 ChatGPT 网页版、Codex、Work 等运行环境下的使用入口。  
> 核心原则：**Execution Mode 决定“这次跑到哪里”，Story Input Mode 决定“故事由谁提供、允许改多少”。**

---

# 一、Execution Mode 总览

Story OS 当前支持以下执行模式：

| Execution Mode | 用途 | 是否允许改剧情 | 是否生图 | 典型运行环境 |
|---|---|---:|---:|---|
| `full_auto` | 从一句话做到最终交付 | 按 Story Input Policy | 是 | ChatGPT / Codex |
| `preproduction_only` | 只完成全部生图前资产 | 是 | 否 | ChatGPT / Work |
| `image_continue` | 接管已完成的前期资产，从生图继续 | 否 | 是 | Codex |
| `resume` | 从上次验证过的断点继续 | 否 | 按断点 | Codex / ChatGPT |
| `repair_only` | 只返修失败或 Dirty 资产 | 否 | 必要时 | Codex |
| `release_only` | 图片已经通过，只做发布资产 | 否 | 否 | Codex / ChatGPT |
| `data_review` | 发布后数据复盘 | 否 | 否 | ChatGPT / Codex |

---

# 二、full_auto｜从一句话做到最终交付

适合：

- 不想自己写剧情；
- 想让 Story OS 自己完成 Concept、Story、Visual Lock、生图、审核和最终 Release；
- 不需要 ChatGPT → Codex 分段接力。

## 最简示例

```text
https://github.com/yeqiana/aigc-dali-cat.git

读取 story 分支。

全自动做一篇「仲夏夜惊魂」。

做到最终交付，不要每一步询问我。
```

系统应识别：

```text
Execution Mode = full_auto
Story Input Mode = auto_create
Image Model = gpt-image-2（未显式指定时）
```

## 指定图片模型

```text
https://github.com/yeqiana/aigc-dali-cat.git

读取 story 分支。

全自动做一篇「仲夏夜惊魂」。

图片模型使用 gpt-image-2。

做到最终交付，不要每一步询问我。
```

## 预期链路

```text
Runtime Request
→ Character Contract
→ Resource Resolver
→ Recent-5
→ Concept Divergence
→ Concept Ambition
→ Story Build
→ Story Critic
→ Storyboard
→ STORYBOARD_LOCKED
→ Environment / Impact Contract
→ Resolved Frame Contracts
→ Visual Lock 1+3
→ Continuous Production
→ Rolling Review
→ Final Frame Review
→ Text / Intro / Release
→ Final Candidate Snapshot
→ PUBLISH_READY
```

---

# 三、preproduction_only｜ChatGPT 只做前期资产，不生图

这是目前最推荐的 **ChatGPT 网页版使用模式**。

适合：

```text
ChatGPT 网页版
→ 完成高质量前期创作资产
→ 提交 GitHub
→ Codex 接管图片生产
```

## 推荐提示词

```text
https://github.com/yeqiana/aigc-dali-cat.git

读取 story 分支。

按仓库当前 Story OS 制作一篇「仲夏夜惊魂」。

使用 preproduction_only 模式：

- 全自动完成全部生图前资产；
- 不要生成任何图片；
- 不要每一步询问我；
- Story OS 自己完成选题、Concept、人物选择、Story Build、Story Critic、Storyboard、Character Contract、Environment / Impact Contract、Resolved Frame Contracts、Resource Selection、简介策略等前期工作；
- 严格执行 Character / Entry Pool、Recent-5、Concept Ambition、NO-ANOMALY TEST、人物连续性和时代真实性；
- 做到正式可以交给 Codex 生图的状态；
- 最后生成并校验 meta/preproduction-handoff.json；
- 前期资产全部自检通过后再交付。

不要因为不生图而降低 Story、Storyboard、Frame Contract 或前期审核质量。
```

## 应完成到

```text
Runtime Request
→ Character Contract
→ Resource Library
→ Concept
→ Story
→ Story Critic
→ Storyboard
→ STORYBOARD_LOCKED
→ Environment / Impact Contract
→ Resolved Frame Contracts
→ Prompt / Resource preparation
→ Intro Policy
→ Provisional Release Draft
→ meta/preproduction-handoff.json
→ STOP
```

## 该模式禁止

```text
image_generation
Visual Lock 正式图片
Batch 图片
Final Frame Review
正式 Release Finalize
```

## 最终至少应存在

```text
meta/runtime-request.json
meta/character-contract.json
meta/episode-state.json
meta/story-gates.json
meta/resource-selection.json
meta/intro-policy.json
meta/preproduction-handoff.json

story/
meta/frame-contracts/
```

并满足：

```text
episode-state = STORYBOARD_LOCKED
handoff_ready = true
```

---

# 四、image_continue｜Codex 接管 ChatGPT 前期资产，从生图继续

适合：

```text
ChatGPT 已完成 preproduction_only
↓
前期资产已经提交 GitHub
↓
Codex 从 Visual Lock / Image Production 开始继续
```

## 推荐提示词

```text
https://github.com/yeqiana/aigc-dali-cat.git

读取 story 分支。

接管「仲夏夜惊魂」已经完成的前期资产。

严格按仓库当前 Story OS 的 image_continue 模式执行：

- 先验证 meta/preproduction-handoff.json；
- 验证 Story、Character Contract 和稳定前期资产的 Authority SHA；
- 不要重写剧情；
- 不要重新做 Concept / Story Build；
- Derived Cache 如果失效可以自动重建；
- 从 Visual Lock 开始继续；
- Visual Lock 按当前 1+3 策略执行；
- 图片模型使用 Runtime Request 中锁定的模型，未显式指定则使用 gpt-image-2；
- 然后完成 Production、Rolling Review、Final Frame Review、必要返修、字幕、简介、Release、Final Candidate Snapshot；
- 一直做到 PUBLISH_READY；
- 不要每一步询问我。

如果 Handoff Authority SHA 不一致，停止并明确报告 HANDOFF_SHA_MISMATCH，不得偷偷重写前期故事。
```

## 如果原始 Runtime Request 是 preproduction_only

先激活当前执行覆盖：

```bat
python -X utf8 episodes/_system/story_os.py handoff activate episodes\你的故事
```

系统只写：

```text
meta/runtime-execution.json
```

原来的：

```text
meta/runtime-request.json
```

保持不可变。

## 接管链路

```text
Git Pull
→ Verify Handoff
→ Verify Authority SHA
→ Rebuild Derived Cache if needed
→ Visual Lock baseline
→ Visual Lock parallel-three
→ Production
→ Rolling Review
→ Final Frame Review
→ Repair Queue
→ Intro / Text Finalize
→ Release
→ Snapshot
→ PUBLISH_READY
```

## 遇到以下情况必须停止

```text
HANDOFF_MISSING
HANDOFF_NOT_READY
HANDOFF_SHA_MISMATCH
HANDOFF_CHARACTER_*
```

不得自动重写 Story 规避错误。

---

# 五、resume｜从断点继续

适合：

- Plus / Codex 额度中断；
- Codex CLI 中途失败；
- 网络异常；
- 手动停止后继续；
- 已完成一部分 Visual / Batch / Review。

## 推荐提示词

```text
https://github.com/yeqiana/aigc-dali-cat.git

读取 story 分支。

继续制作「仲夏夜惊魂」。

使用 resume 模式，从上次已验证的断点继续。

已经 PASS 且 SHA 未漂移的 Story、Visual Lock、图片、Review 和 Release 资产全部复用，不要为了保险重新生成。

一直继续到 PUBLISH_READY，不要每一步询问我。
```

## Resume 原则

```text
检查当前 Episode State
↓
读取 Runtime DAG Checkpoint
↓
重新跑 machine / evidence gate
↓
仍然有效
→ REUSED

无效 / Dirty
→ 只重跑对应 Step
```

## 示例

如果已经完成：

```text
CREATIVE_STORY = PASS
VISUAL_LOCK = PASS
```

中断后：

```text
CREATIVE_STORY → REUSED
VISUAL_LOCK → REUSED
PRODUCTION → CONTINUE
```

不会重新编故事，也不会重做 4 张 Visual Lock。

---

# 六、repair_only｜只返修失败图片/资产

适合：

- 已经完成 Batch；
- 只有几张图片有问题；
- Final Review 标出 Repair Queue；
- 不希望重新生成通过的图片。

## 推荐提示词

```text
https://github.com/yeqiana/aigc-dali-cat.git

读取 story 分支。

只返修「仲夏夜惊魂」当前未通过的图片和 Dirty 资产。

使用 repair_only 模式。

要求：
- 已经 PASS 且 SHA 未漂移的图片禁止重做；
- 只处理 Repair Queue / technical failure / semantic failure；
- 保持 Character Contract、Frame Contract、Visual Lock 和人物连续性；
- 修复完成后重新执行对应的实际像素审核；
- 不修改已经锁定的 Story；
- 不要每一步询问我。
```

## 执行原则

```text
Repair Queue
↓
Dirty Dependency Check
↓
只生成失败帧
↓
Fast Scout
↓
Final Review
↓
PASS
```

技术失败：

```text
timeout
provider failure
capacity
model unavailable
```

不得消耗内容返修次数。

---

# 七、release_only｜只做字幕、简介和最终发布资产

适合：

- 图片已经全部通过；
- Production 已经 PASS；
- 只差字幕、简介、封面文字、Release Snapshot。

## 推荐提示词

```text
https://github.com/yeqiana/aigc-dali-cat.git

读取 story 分支。

「仲夏夜惊魂」的图片已经全部审核通过。

使用 release_only 模式：

- 不重新生成图片；
- 不重写 Story；
- 只完成最终字幕、简介、发布文案、Release Audit 和 Final Candidate Snapshot；
- 简介开头按当前 intro opener policy 执行；
- 标题只生成 1 个内部候选，不作为实际发布必填；
- 做到 PUBLISH_READY；
- 不要每一步询问我。
```

## Release 链路

```text
Production PASS
↓
Intro Policy
↓
Caption Finalize
↓
Text / Image Audit
↓
Publish Copy
↓
Release Manifest
↓
Final Candidate Snapshot
↓
PUBLISH_READY
```

---

# 八、data_review｜发布后数据复盘

适合：

- 作品已经发布；
- 有播放、完读、点赞、评论、收藏等数据；
- 想更新 Account Learning / Recent-5。

## 推荐提示词

```text
https://github.com/yeqiana/aigc-dali-cat.git

读取 story 分支。

使用 data_review 模式复盘「仲夏夜惊魂」的发布数据。

结合当前仓库的发布后漏斗规范，分析：
- 冷启动表现；
- 前5张 / 前10张承接；
- 完读 / 停留；
- 点赞 / 收藏 / 评论；
- 题材、人群、开头、视觉异常和结尾的有效性；
- 哪些经验应该进入 Account Learning；
- 下一篇应该保留和避免什么。

不要修改已经发布的 Story 或成片。
```

如果用户提供数据截图/表格，应以实际数据为准。

---

# 九、Story Input Mode 总览

Execution Mode 和 Story Input Mode 是两回事。

例如：

```text
full_auto + auto_create
full_auto + user_seed
preproduction_only + core_constraints
image_continue + locked_story
```

都可以成立。

Story Input Mode 当前有：

```text
auto_create
user_seed
core_constraints
locked_story
```

---

# 十、auto_create｜完全不提供剧情

适合：

- 只给一个题目；
- 让 Story OS 自己选方向。

## 示例

```text
读取 story 分支。

全自动做一篇「仲夏夜惊魂」。

做到最终交付，不要每一步询问我。
```

系统：

```text
story_input.mode = auto_create
```

Story OS 应自己完成：

```text
Recent-5
→ Character / Entry Pool
→ 8–12 Concept Divergence
→ Concept Ambition
→ Story Build
→ Story Critic
```

没有剧情输入**不是错误**。

---

# 十一、user_seed｜提供粗剧情

适合：

- 有一个大概想法；
- 但希望 Story OS 继续强化。

## 示例

```text
读取 story 分支。

全自动做一篇「仲夏夜惊魂」。

剧情大概是：

四个朋友暑假去一个已经废弃的游乐园。
进去之后，他们发现园里的设施明明没有通电，却会在他们走过之后自己启动。
最后他们发现自己小时候来过这里，但几个人都完全不记得。

按 Story OS 强化后制作，不要机械拆我的剧情。
```

系统：

```text
story_input.mode = user_seed
rewrite_policy = strengthen_and_rewrite
```

Story OS 应允许：

```text
加强异常机制
调整结构
补逻辑
重排节奏
强化高潮
重做结尾
```

但保留用户核心意图。

---

# 十二、core_constraints｜有必须保留的核心设定

适合：

- 有几个不能动的剧情锚点；
- 其余都允许 Story OS 优化。

## 示例

```text
读取 story 分支。

全自动做一篇「仲夏夜惊魂」。

必须保留：

1. 主角是 2008 年的四个大学同学；
2. 他们喝酒后去废旧游乐园做挑战；
3. 其中一个女生中途失踪；
4. 最后一张必须是主角在旧合照里看到失踪女生；
5. 不要使用抢修员、警察、记者、调查员。

其余剧情按 Story OS 自己优化。
```

系统：

```text
story_input.mode = core_constraints
```

硬约束不能改，但 Story OS 可以重构其它部分。

---

# 十三、locked_story｜剧情已经锁死

适合：

- Story 已经定稿；
- 只允许逻辑/表达小修；
- 或 ChatGPT 前期 → Codex 生图接管。

## 示例

```text
读取 story 分支。

「仲夏夜惊魂」剧情已经定了，不要改剧情。

严格使用仓库中现有 Story、Storyboard、Character Contract 和 Frame Contracts。

只继续后续执行和必要的逻辑/格式修补。
```

系统：

```text
story_input.mode = locked_story
allow_structure_rewrite = false
```

允许：

```text
错字修正
机器合同补齐
逻辑一致性小修
派生缓存重建
```

禁止：

```text
换主角
换结局
重新选 Concept
重排整篇结构
```

---

# 十四、推荐工作流｜ChatGPT 网页版 + Codex

这是目前最推荐的真实生产方式。

## 第一步：ChatGPT 网页版

```text
https://github.com/yeqiana/aigc-dali-cat.git

读取 story 分支。

全自动制作一篇「仲夏夜惊魂」的全部前期资产。

使用 preproduction_only 模式。

做到正式生图交接状态，不要生成图片，不要每一步询问我。
```

ChatGPT 完成：

```text
Concept
Story
Storyboard
Character
Environment
Frame Contracts
Resources
Intro
Handoff
```

---

## 第二步：提交 GitHub

将本次 Episode 前期资产写入/上传到：

```text
story 分支
```

确保：

```text
meta/preproduction-handoff.json
```

一起提交。

---

## 第三步：Codex

```text
https://github.com/yeqiana/aigc-dali-cat.git

读取 story 分支。

接管「仲夏夜惊魂」已经完成的前期资产。

使用 image_continue 模式。

不要重写剧情，从生图开始一直做到最终交付，不要每一步询问我。
```

如果需要显式激活：

```bat
python -X utf8 episodes/_system/story_os.py handoff activate episodes\你的故事
```

---

# 十五、推荐工作流｜Codex 全自动

如果不需要 ChatGPT 前期分工：

```text
https://github.com/yeqiana/aigc-dali-cat.git

读取 story 分支。

按仓库当前 Story OS 全自动制作一篇「仲夏夜惊魂」。

做到最终交付，不要每一步询问我。
```

即可。

---

# 十六、常用模式速查

## 网页 ChatGPT 只做前期

```text
读取 story 分支。
全自动做一篇「XXX」的全部前期资产，
使用 preproduction_only，
做到正式生图交接状态，不要生图，不要每一步问我。
```

## Codex 接着生图

```text
读取 story 分支。
接管「XXX」已经完成的前期资产，
使用 image_continue，
不要重写剧情，从生图开始做到最终交付。
```

## 中断继续

```text
读取 story 分支。
继续「XXX」，
使用 resume，
从上次验证通过的断点继续。
```

## 只返修

```text
读取 story 分支。
只返修「XXX」未通过的图片，
使用 repair_only，
PASS 图片禁止重做。
```

## 只做发布资产

```text
读取 story 分支。
「XXX」图片已经通过，
使用 release_only，
只做字幕、简介、Release 和 Snapshot。
```

## 发布后复盘

```text
读取 story 分支。
使用 data_review 复盘「XXX」的发布数据。
```

---

# 十七、简介默认开头策略

简介最终优先参考以下四种结构。

## 1. 年份 + 行动

```text
2008年，我和几个朋友去了XXX。
```

适合：

```text
2004–2010
旅行
返乡
挑战
废弃场所
```

## 2. 状态 + 时机 + 出行

```text
最近上班有些疲惫，刚好趁着周末，我和几个朋友去了XXX。
```

可自然变化：

```text
最近上学有些倦怠……
最近生活有点闷……
最近工作有些累……
```

## 3. 身份 + 最近发现

```text
XXX是XXX大学的研二学生，最近他发现了……
```

适合：

```text
第三人称
学生
课题组
研究/科考
```

## 4. 临近节点 + 决定

```text
临近XXX，我和几个朋友决定去XXX。
```

例如：

```text
临近国庆……
快到暑假……
临近毕业……
春节前几天……
```

## 使用原则

模板只是：

```text
结构参考
```

不是：

```text
机械把 XXX 换成地点
```

最终简介必须像真人自然叙述。

---

# 十八、标题策略

Story OS 仍然默认生成：

```text
1 个标题
```

但用途为：

```text
internal_candidate_only
```

它主要用于：

- Episode 内部识别；
- 文件/项目管理；
- 必要时的备用发布候选。

默认：

```text
PUBLISH_READY 必填 = false
最终交付默认包含 = false
简介默认携带标题 = false
实际发布必须使用 = false
```

---

# 十九、核心原则

以后使用 Story OS，可以记住两句话：

```text
Execution Mode
=
这次要跑到哪里
```

```text
Story Input Mode
=
故事是谁提供的、允许改多少
```

推荐默认生产方式：

```text
ChatGPT 网页版
→ preproduction_only
→ GitHub
→ Codex image_continue
→ PUBLISH_READY
```

这样能够同时利用：

- ChatGPT 前期长文本创作与审稿；
- GitHub 权威资产冻结；
- Handoff SHA；
- Codex 图片生产；
- Runtime DAG；
- Continuous Scheduler；
- Step Resume；
- Prompt Cache；
- Resource Library；
- Final Review；

并且不会因为运行环境切换而重新编故事。
