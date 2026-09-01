# Story OS V2.2.3｜最简完整生产使用手册

## 总流程

只记住这 7 步：

```text
① 准备故事 MD
      ↓
② Bootstrap
      ↓
③ Bootstrap Validate
      ↓
④ Preproduction
      ↓
⑤ Preproduction Validate
      ↓
⑥ Smoke Test
      ↓
⑦ Visual Lock → Production → Release
```

---

# ① 准备故事 MD

最开始只需要一个 Markdown。

例如：

```text
episodes/12_千寻/千寻.md
```

MD 里面写清：

* 做什么故事
* 本集范围
* 大概剧情
* 特殊要求

不需要自己写 JSON。

---

# ② Bootstrap：生成入口资产

### 目的

把：

```text
故事.md
```

变成机器可以继续执行的入口。

这一阶段应该很快，不做完整前期，不生图。

### 给 Codex

```text
读取 aigc-dali-cat 当前 story 分支。

源故事：

episodes/12_千寻/千寻.md

为这篇故事执行轻量 Episode Bootstrap。

要求：

1. 读取源 MD；
2. 确定 Episode ID；
3. 确定本集 Chapter Scope；
4. 创建 Episode Blueprint；
5. 创建 Chapter Lock；
6. 创建 Visual Profile；
7. 创建 Asset Manifest；

本阶段只创建生产入口资产。

不要：
- 做完整人物母版
- 做地点母版
- 做道具母版
- 做 Storyboard
- 做 Resolved Frame Contracts
- 生图
- 进入 Preproduction
- 进入 Smoke Test

完成状态：

BOOTSTRAPPED

然后停止。
```

---

# 怎么指定画风 / 质感

## 最简单的方法

直接在 Bootstrap 指令里增加一个：

```text
【画风锁定】
```

例如：

```text
【画风锁定】

Visual Profile ID：
SPIRITED_AWAY_LIVE_ACTION_V1

画风：
1990年代日本真人奇幻电影。

质感：
35mm胶片，
低饱和，
轻微胶片颗粒，
真实皮肤和真实布景，
自然光，
夏季潮湿空气，
轻微高光溢出，
真实摄影机曝光。

摄影：
真实电影摄影，
不是概念设计图，
不是商业棚拍，
不是AI插画。

世界原则：
real-world-first，
supernatural-second。

必须保留：
- 真人演员
- 日本90年代生活环境
- 自然服装
- 写实实景
- 潮湿夏季空气感

禁止：
- 动画脸
- 二次元
- cosplay
- 游戏CG
- 3D渲染
- 塑料皮肤
- 过度锐化
- HDR感
- AI油腻感
```

Codex 应该把这些内容正式写入：

```text
Visual Profile
```

而不是只记在聊天上下文里。

---

## 如果没有现成 Visual Profile

不要写：

```text
使用 SPIRITED_AWAY_LIVE_ACTION_V1
```

然后假设仓库里已经有。

应该写：

```text
如果当前 story 分支不存在
SPIRITED_AWAY_LIVE_ACTION_V1：

根据下面的画风定义，
在当前 Episode / story 分支正式创建该 Visual Profile，
然后写入 Episode Blueprint。

禁止搜索其他仓库寻找同名 Profile。
```

这样不会再发生：

```text
Profile 不存在
→ Validate Failed
```

---

## 如果是普通原创故事

例如你平时的真实手机相册风：

```text
【画风锁定】

使用 Story OS 默认真实手机纪录 Visual Profile。

核心质感：

- 2020年代真实中国手机相册
- iPhone / 国产旗舰手机随手拍
- 私人照片而非电影剧照
- 自然曝光
- 真实手机HDR但不过度
- 轻微噪点
- 构图不完美
- 人物动作自然
- 天气物理明显
- 真实材质
- 异常可以巨大，但拍摄物理必须可信

禁止：

- AI插画
- 概念艺术
- 电影海报
- 过度电影灯光
- 塑料皮肤
- 3D游戏CG
- 过度锐化
```

---

# ③ Bootstrap Validate

Bootstrap 完成后，直接执行仓库真实命令：

```bat
python -X utf8 scripts/story_validate.py bootstrap "你的Episode目录"
```

例如：

```bat
python -X utf8 scripts/story_validate.py bootstrap "episodes/12_千寻/01_那条不存在的隧道"
```

应该得到：

```text
BOOTSTRAP_VALIDATE_PASS
```

代表：

```text
READY_FOR_PREPRODUCTION
```

这一阶段只检查：

```text
✓ Episode Blueprint
✓ Chapter Lock
✓ Visual Profile
✓ Asset Manifest
```

不检查人物母版等重资产。

如果失败：

不要进入下一步。

让 Codex只修 Bootstrap 缺失项。

---

# ④ Preproduction：完整前期生产

Bootstrap Validate PASS 后，再给 Codex：

```text
读取当前 story 分支。

Episode：

[你的 Episode 目录 / Episode ID]

Bootstrap Validate 已通过。

现在执行完整 Preproduction。

严格继承：

- Episode Blueprint
- Chapter Lock
- Visual Profile
- Asset Manifest

不要重新改本集范围。
不要偷偷更换画风。

完成：

1. Character Contract
2. Character Master
3. Location / Environment Contract
4. Location Master
5. Device / Prop Contract
6. 必要 Device / Prop Master
7. Storyboard / Frame Plan
8. Resolved Frame Contracts
9. Asset SHA / Digest
10. Contract Binding
11. Authority
12. Preproduction Handoff

Authority Scope：

current_story_branch

所有资产只能在当前 aigc-dali-cat/story 内创建。

禁止：
- 搜索其他仓库
- 搜索旧项目
- 使用 ohmyphoto
- 使用历史废弃资产
- 进入正式剧情生图

画风必须严格继承已经锁定的 Visual Profile。

做到：

READY_FOR_PREPRODUCTION_VALIDATE

后停止。
```

---

# ⑤ Preproduction Validate

前期完成后执行：

```bat
python -X utf8 scripts/story_validate.py preproduction "你的Episode目录"
```

例如：

```bat
python -X utf8 scripts/story_validate.py preproduction "episodes/12_千寻/01_那条不存在的隧道"
```

应该得到：

```text
PREPRODUCTION_VALIDATE_PASS
```

代表：

```text
READY_FOR_SMOKE_TEST
```

这一关检查完整生产资产：

```text
✓ Bootstrap 已通过
✓ Character Contract
✓ Location Contract
✓ Device / Prop Contract
✓ Asset Manifest
✓ Resolved Frame Contracts
✓ Authority / Binding
✓ SHA / Digest
✓ current_story_branch Authority
```

不 PASS：

禁止 Smoke Test。

---

# ⑥ Smoke Test：开发者单图测试

Preproduction Validate PASS 后：

给 Codex：

```text
读取当前 story 分支。

对：

[Episode ID]

执行 Developer Smoke Test。

前提：

PREPRODUCTION_VALIDATE_PASS。

要求：

1. 只选择 1 张具有代表性的正式 Frame；
2. 严格读取已经锁定的：
   - Chapter Lock
   - Visual Profile
   - Character Master
   - Location Master
   - Device / Prop Master
   - Resolved Frame Contract

3. 调用正式生产使用的图片模型；
4. 只生成 1 张；
5. 不重新做任何前期资产；
6. 不搜索外部资产；
7. 不进入 Full Production。

重点检查：

- 画风是否真正生效
- 质感是否正确
- 人物母版是否生效
- 地点母版是否生效
- 道具连续性
- Prompt / 模型调用链
- 输出路径

最后输出：

SMOKE_TEST_PASS

或者：

SMOKE_TEST_FAILED

并告诉我：

- 测试图路径
- Visual Profile 是否生效
- Character 是否生效
- Location 是否生效
- 总耗时
- 图片模型调用耗时

完成后停止。
```

---

# Smoke Test 看什么

你实际上只需要看这张图片。

### 第一：画风对不对

例如你指定：

```text
35mm真人电影
```

出来是不是：

```text
真人电影照片
```

而不是：

```text
动画 / CG / AI插画
```

### 第二：质感对不对

看：

* 光线
* 颗粒
* 曝光
* 色彩
* 材质
* 天气
* 摄影机感觉

### 第三：人物对不对

看：

* 脸
* 年龄
* 服装
* 身材
* 发型

### 第四：场景对不对

看：

* 建筑
* 空间
* 年代
* 地理
* 天气

如果不对：

**现在改。**

不要等 20 张全生完再改。

---

# ⑦ Visual Lock + 正式生产

Smoke Test PASS 后给 Codex：

```text
读取当前 story 分支。

继续生产：

[Episode ID]

当前状态：

PREPRODUCTION_VALIDATE_PASS
SMOKE_TEST_PASS

严格继承已经冻结的：

- Story / Chapter Lock
- Visual Profile
- Character Master
- Location Master
- Device / Prop Master
- Resolved Frame Contracts

禁止：

- 重写剧情
- 改本集范围
- 更换画风
- 重做已批准母版
- 搜索外部仓库资产

现在开始正式流程：

Visual Lock 1+3
↓
Production
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

除非出现 Authority SHA 不一致、
必要资产缺失、
或无法安全继续的 Runtime 故障，

否则不要每一步询问我。
```

---

# 最终只需要记这几个入口

## 新故事

```text
故事.md
```

↓

### 1

给 Codex：

```text
Bootstrap
```

↓

### 2

本地运行：

```bat
python -X utf8 scripts/story_validate.py bootstrap "Episode目录"
```

↓

### 3

给 Codex：

```text
Preproduction
```

↓

### 4

本地运行：

```bat
python -X utf8 scripts/story_validate.py preproduction "Episode目录"
```

↓

### 5

给 Codex：

```text
Smoke Test，只生1张
```

↓

### 6

你看测试图。

画风正确：

```text
PASS
```

↓

### 7

给 Codex：

```text
Visual Lock + Full Production，做到 PUBLISH_READY
```

---

# 一句话版本

以后生产任何故事：

```text
MD
→ Bootstrap
→ 验入口
→ Preproduction
→ 验前期
→ Smoke Test 1张
→ 看画风
→ 正式生产
```

## 画风在哪指定？

**第一次就在 Bootstrap 阶段指定。**

之后：

```text
Bootstrap
      ↓
Visual Profile Lock
      ↓
Preproduction继承
      ↓
Smoke Test验证
      ↓
Production冻结
```

后面的阶段只能继承，不应该偷偷重新决定画风。
