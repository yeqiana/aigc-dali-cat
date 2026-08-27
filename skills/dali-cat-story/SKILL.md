# dali-cat-story

用于 `aigc-dali-cat` story 分支的标准化故事生产、返修和发布前审核。

## 权威层级

1. `standards/制作规范_正式版.md` — 唯一主规范。
2. 当前有效从属细则 — 只补执行细节，不与主规范并列。
3. 单集 `episode.yaml` — 只记录本集事实、锚点、状态和锁，不得覆盖 1/2。
4. 本 Skill references — 执行解释，不复制主规范全文。

## 使用流程

先读 `references/authority-map.md`，再按任务类型选择：

- 新选题 / 改剧情：`references/story-gates.md`
- 生图 / 重做某图：`references/visual-gates.md` + `references/lock-edit-protocol.md`
- 字幕：`references/subtitle-gates.md`
- 审核 / 发布：`references/review-gates.md`

新篇必须有 `episode.yaml`。可以运行：

```bash
python skills/dali-cat-story/scripts/bootstrap_episode.py <episode-dir>
```

完成后执行：

```bash
python skills/dali-cat-story/scripts/validate_all.py <episode-dir>/episode.yaml
```

发布前执行：

```bash
python skills/dali-cat-story/scripts/validate_all.py <episode-dir>/episode.yaml --release
```

## 不得做的事

- 不得为了“看起来更恐怖”统一压暗整套图片。
- 不得把共享风格锚点理解成共享剧情、人物、异常机制或构图。
- 不得在修字幕时重生成已锁定底图。
- 不得把机器 validator 的 PASS 当作视觉/剧情人工审核 PASS。
- 不得在没有查当前单集 docs 的情况下凭记忆覆盖已锁定设定。
