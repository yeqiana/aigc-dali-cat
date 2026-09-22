# Story OS V2.2.4｜Codex 最简完整生产手册

## 一句话流程

```text
故事 MD
↓
Bootstrap
↓
Bootstrap Validate
↓
Visual Test 1张
↓
Preproduction
↓
Preproduction Validate
↓
Production Smoke Test 1张
↓
Visual Lock 1+3
↓
Full Production
↓
PUBLISH_READY
```

---

# 1. 准备故事 MD

最开始可以只有：

```text
episodes/12_千寻/千寻.md
```

不用自己创建 JSON。

---

# 2. Bootstrap：生成入口资产

直接给 Codex：

```text
读取 aigc-dali-cat 当前 story 分支。

源故事：

episodes/12_千寻/千寻.md

为 EP01 执行轻量 Bootstrap。

本阶段只负责创建生产入口：

- Episode Blueprint
- Chapter Lock
- Visual Profile Lock
- Asset Manifest

不要：

- 做完整 Preproduction
- 做 Character Master
- 做 Location Master
- 做 Prop Master
- 做完整 Storyboard
- 做 Resolved Frame Contracts
- 生图

画风锁定：

Visual Profile：
SPIRITED_AWAY_LIVE_ACTION_V1

必须严格使用仓库：
standards/visual_profiles/SPIRITED_AWAY_LIVE_ACTION_V1.json

不得使用默认 M00。
不得重新解释成手机伪纪录片。
不得自行更换 Profile。
Authority 只能来自当前 story 分支。

完成后停在：

BOOTSTRAPPED
```

---

# 3. 怎么指定画风 / 质感

## 最简单方式：直接指定已有 Visual Profile

《千与千寻真人电影版》直接写：

```text
画风锁定：

Visual Profile：
SPIRITED_AWAY_LIVE_ACTION_V1

必须严格使用仓库：
standards/visual_profiles/SPIRITED_AWAY_LIVE_ACTION_V1.json

不得使用默认 M00。
不得重新解释成手机伪纪录片。
不得自行更换 Profile。
```

就够了。

这个 Profile 当前已经定义：

```text
1990年代日本真人奇幻电影
35mm胶片
低饱和
轻微胶片颗粒
自然光
真实皮肤
真实实景布景
日本90年代生活环境
自然年代服饰
夏季潮湿空气
真人电影摄影
```

并且禁止：

```text
动画脸
二次元
cosplay
游戏CG
3D渲染
塑料皮肤
过度锐化
HDR感
AI油腻感
概念设计图
商业棚拍
AI插画
```

所以以后不需要再把几十条画风提示词全部重复给 Codex。

只写：

```text
Visual Profile：
SPIRITED_AWAY_LIVE_ACTION_V1
```

即可。

---

## 如果以后想指定一种全新的画风

例如：

```text
画风要求：

1980年代中国西北电影，
16mm纪录片，
偏黄灰，
真实胶片颗粒，
冬季干燥空气，
自然光，
不要现代数码HDR。
```

这时候告诉 Codex：

```text
当前没有现成 Visual Profile。

根据上述要求：

1. 新建一个正式 Visual Profile；
2. 写入 standards/visual_profiles/；
3. 分配唯一 profile_id；
4. Episode meta/visual-profile.json 锁定该 Profile；
5. Episode Blueprint 绑定同一个 Profile；
6. 然后再执行 Bootstrap Validate。

不得只把画风保留在聊天提示词里。
```

也就是说：

**画风一定要资产化。**

不是：

```text
聊天里说过
```

而是：

```text
Visual Profile JSON
↓
Episode Lock
↓
后续所有生图自动继承
```

---

# 4. Bootstrap Validate

Bootstrap 完成后，让 Codex 执行：

```text
执行：

python -X utf8 scripts/story_validate.py bootstrap "episodes/12_千寻/01_那条不存在的隧道"

只进行 Bootstrap Validate。

如果 PASS，告诉我：

BOOTSTRAP_VALIDATE_PASS

否则停止并报告缺失项。
```

这一关只验证：

```text
Episode Blueprint
Chapter Lock
Visual Profile
Asset Manifest
```

通过后：

```text
READY_FOR_VISUAL_TEST
```

---

# 5. Visual Test：先看一张画风

这个阶段：

**不需要完整 Preproduction。**

直接给 Codex：

```text
读取当前 story 分支。

对：

episodes/12_千寻/01_那条不存在的隧道

执行 Visual Test。

前提：

BOOTSTRAP_VALIDATE_PASS

严格使用：

SPIRITED_AWAY_LIVE_ACTION_V1

测试场景：

1990年代日本乡间，
搬家车停在废弃隧道入口，
千寻一家站在隧道外。

只生成 1 张。

图片模型：

gpt-image-2

要求：

- 真人演员
- 35mm胶片
- 低饱和
- 夏季潮湿空气
- 真实自然光
- 日本90年代生活环境
- 写实实景

禁止：

- 动画
- 二次元
- cosplay
- CG
- AI插画
- 塑料皮肤
- HDR

本图身份必须是：

NON_AUTHORITY_TEST_ONLY

不得成为：
- Character Master
- Location Master
- Production Frame

完成后告诉我：

- Visual Profile 是否正确加载
- 图片路径
- 图片模型
- 生图耗时
- 总耗时

然后停止。
```

Codex 实际可以执行：

```bat
python -X utf8 scripts/story_test.py visual "episodes/12_千寻/01_那条不存在的隧道" --scene "1990年代日本乡间，搬家车停在废弃隧道入口，千寻一家站在隧道外" --image-model gpt-image-2 --strict-model
```

---

# 6. 你只需要看 Visual Test 这一张

重点看四件事：

```text
① 真人感对不对

② 35mm胶片质感对不对

③ 日本90年代感觉对不对

④ 有没有动画 / CG / AI味
```

如果不满意：

现在修改：

```text
Visual Profile
```

然后重新 Visual Test。

不要进入完整前期。

---

# 7. Preproduction：正式制作前期资产

Visual Test 满意以后给 Codex：

```text
读取当前 story 分支。

继续当前 Episode。

Visual Test 已确认画风正确。

现在执行完整 Preproduction。

严格继承：

- Story / Chapter Lock
- SPIRITED_AWAY_LIVE_ACTION_V1
- Asset Manifest

完成：

- Character Contract
- Character Master
- Location / Environment Contract
- Location Master
- Device / Prop Contract
- 必要 Prop Master
- Storyboard
- Frame Plan
- Resolved Frame Contracts
- Asset SHA / Digest
- Contract Binding
- Authority
- Preproduction Handoff

所有 Authority：

current_story_branch

禁止：

- 搜索其他仓库
- 搜索旧项目
- 使用 ohmyphoto
- 偷偷更换画风
- 进入 Full Production

完成后停在：

READY_FOR_PREPRODUCTION_VALIDATE
```

---

# 8. Preproduction Validate

让 Codex执行：

```text
执行：

python -X utf8 scripts/story_validate.py preproduction "episodes/12_千寻/01_那条不存在的隧道"

如果通过：

PREPRODUCTION_VALIDATE_PASS

否则立即停止并报告缺失项。
```

这一关才检查：

```text
Character Contract
Location Contract
Prop Contract
Resolved Frame Contracts
SHA
Binding
Authority
```

通过后：

```text
READY_FOR_PRODUCTION_SMOKE_TEST
```

---

# 9. Production Smoke Test

这个测试和 Visual Test 不一样。

Visual Test：

```text
只看画风
```

Production Smoke Test：

```text
验证真实正式生产链
```

让 Codex：

```text
对当前 Episode 执行 Production Smoke Test。

前提：

PREPRODUCTION_VALIDATE_PASS

选择 1 个正式 Frame。

必须使用：

- Character Master
- Location Master
- Prop Master
- Visual Profile
- Resolved Frame Contract
- 正式图片生成后端

只生成 1 张。

不得进入完整 Production。

完成后告诉我：

PRODUCTION_SMOKE_TEST_PASS / FAILED

以及：

- Frame
- 图片路径
- Character Master 是否生效
- Location Master 是否生效
- Visual Profile 是否生效
- Frame Contract 是否生效
- 图片模型
- 生图耗时
```

---

# 10. 正式生产

Production Smoke Test 通过以后：

```text
读取当前 story 分支。

继续当前 Episode。

当前已经通过：

BOOTSTRAP_VALIDATE_PASS
VISUAL_TEST
PREPRODUCTION_VALIDATE_PASS
PRODUCTION_SMOKE_TEST

严格继承：

- Story Lock
- Chapter Lock
- Visual Profile
- Character Master
- Location Master
- Prop Master
- Resolved Frame Contracts

不得重新决定画风。
不得重写剧情。
不得搜索外部资产。

现在执行：

Visual Lock 1+3
↓
Full Production
↓
Rolling Review
↓
必要返修
↓
Final Frame Review
↓
字幕
↓
标题
↓
简介
↓
Release
↓
Final Candidate Snapshot

一直做到：

PUBLISH_READY

除非发生：

- Authority SHA 不一致
- 必要资产缺失
- Runtime 无法安全继续

否则不要中途询问我。
```

---

# 最后只记这一套

```text
① MD
   ↓
② Bootstrap
   ↓
③ Bootstrap Validate
   ↓
④ Visual Test 1张
   ↓
   看画风
   ↓
⑤ Preproduction
   ↓
⑥ Preproduction Validate
   ↓
⑦ Production Smoke Test 1张
   ↓
⑧ Visual Lock 1+3
   ↓
⑨ Full Production
   ↓
⑩ PUBLISH_READY
```

---

# 画风怎么指定，最终口诀

已有画风：

```text
Visual Profile：
SPIRITED_AWAY_LIVE_ACTION_V1
```

就够了。

新画风：

```text
用自然语言描述
↓
让 Codex 创建 Visual Profile JSON
↓
Episode 锁定 Profile ID
↓
Bootstrap Validate
↓
Visual Test
```

**不要把画风只存在提示词里。**

正式原则：

```text
画风描述
→ Visual Profile
→ Episode Lock
→ Visual Test
→ 全生产继承
```
