# Story OS V2.2 R2 — Activation & Legacy Compatibility

R2 修复 R1 验收暴露的四类问题：

1. 缺 `shot-progression-review.json` 时 0 帧空转 `VERIFIED`。
2. V2.2 由“文件存在”错误激活。
3. legacy Frame Contract 被写入空的 `[VISUAL NARRATIVE CORE V2.2] {}`。
4. legacy Final / Incremental / Visual Lock Review 被无条件套上 V2.2 检查。

## 正式激活

```text
Episode tool_version >= 2.2.0
→ Visual Narrative Core FORMAL REQUIRED
→ meta/shot-progression-review.json
   schema_version=2 + status=LOCKED
→ 缺失 / 0 帧 / 未 LOCK 都是 HARD FAIL
```

## Legacy

```text
Episode tool_version < 2.2.0
→ VISUAL_NARRATIVE_NOT_APPLICABLE
→ 不写 V2.2 Frame Contract prompt/hash
→ Final/Incremental/Visual Lock 不执行 V2.2-only checks
```

## Cross-Episode Regression

Legacy 只能显式：

```bat
python -X utf8 scripts/story_visual_narrative.py prepare-regression "<episode>"
```

只创建测试文件：

- `meta/visual-narrative-core.json`
- `meta/tests/visual-narrative-regression/shot-progression-review.json`

其 Authority 固定为：

`NON_AUTHORITY_REGRESSION_ONLY`

禁止自动晋升 Production Authority。

## 产品版本

安装器将仓库 `story_os_manifest.json` 从 2.1.0 提升到 2.2.0。

不会修改任何旧 Episode 的 `tool_version`，所以不会 retroactive 污染 legacy。
