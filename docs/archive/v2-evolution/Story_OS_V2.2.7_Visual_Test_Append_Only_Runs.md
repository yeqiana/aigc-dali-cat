# Story OS V2.2.7｜Visual Test Append-Only Runs

## 核心语义

每次用户要求 Visual Test，都代表一次**全新的测试运行**。

历史记录：

**只用于审计，不参与新测试的执行决策。**

正式规则：

```text
Visual Test request
↓
NEW RUN_ID
↓
NEW plan
↓
NEW raw/output paths
↓
NEW image generation request
↓
NEW report
```

绝不：

- 因为以前 Visual Test PASS 而跳过；
- 复用旧测试图；
- 复用旧 report；
- 因为 Profile SHA 没变而命中缓存；
- 因为 scene 相同而命中缓存；
- 在开始新 Visual Test 前遍历旧测试判断是否需要生成。

## 目录

每次运行单独保存：

```text
meta/tests/visual/
├─ VT_.../
│  ├─ plan.json
│  ├─ generation.json
│  ├─ report.json
│  └─ prompt.txt
└─ latest.json
```

图片：

```text
media/tests/visual/
└─ VT_.../
   ├─ raw.png
   └─ output.png
```

`latest.json` 只是方便打开最新一次结果：

```text
NON_AUTHORITY
NON_GATE
NON_REUSE
```

Visual Test 执行代码不会读取它来决定是否生成。

## 开始一次新 Visual Test

```bat
python -X utf8 scripts/story_test.py visual "<episode>" --scene "..." --image-model gpt-image-2 --strict-model
```

每执行一次都会产生新的：

```text
run_id = VT_...
```

并返回：

```text
VISUAL_TEST_NATIVE_IMAGE_REQUIRED
```

当前主会话随后必须生成**一张全新的图片**。

## 成功后 finalize

使用本次输出的 `run_id`：

```bat
python -X utf8 scripts/story_test.py visual-finalize "<episode>" --run-id "VT_..."
```

## 生图被拦截/失败也要留档

```bat
python -X utf8 scripts/story_test.py visual-record-failure "<episode>" --run-id "VT_..." --status GENERATION_BLOCKED --reason "moderation_blocked"
```

允许状态：

- `GENERATION_BLOCKED`
- `GENERATION_FAILED`
- `GENERATION_CANCELLED`

这样失败的 Visual Test 也不会丢失历史。

## 人工验收

```bat
python -X utf8 scripts/story_test.py visual-review "<episode>" --run-id "VT_..." --decision PASS --note "Visual Texture / Capture Grammar 均通过"
```

或者：

```bat
python -X utf8 scripts/story_test.py visual-review "<episode>" --run-id "VT_..." --decision FAIL --note "Capture Grammar 仍过于第三人称"
```

## 查看历史

历史查询是显式人工命令：

```bat
python -X utf8 scripts/story_test.py visual-history "<episode>"
```

它不会被新的 `visual` 命令自动调用。
