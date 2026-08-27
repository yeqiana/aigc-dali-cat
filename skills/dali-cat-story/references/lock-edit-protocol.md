# Lock & Minimal Edit Protocol

用于解决高频返工问题：用户只要求改字幕，却把底图、构图、人物或质感一起改了。

## 修改语义

| 用户意图 | edit_mode |
|---|---|
| 只改字幕 / 只改文字 / 底图别动 | `subtitle_only` |
| 只裁切/改比例，不改变画面内容 | `crop_only` |
| 对目标图重做但保持人物/场景锚点 | `regenerate_frame` |
| 全套重构 | `regenerate_sequence` |

## 锁定资产

把原始底图 SHA-256 写进 `episode.yaml`：

```yaml
locks:
  edit_mode: subtitle_only
  assets:
    - path: workbench/locked/19.png
      sha256: "..."
      reason: "图19底图锁定，只允许替换字幕"
```

运行：

```bash
python skills/dali-cat-story/scripts/validate_locked_edits.py episode.yaml
```

若文件内容变化，直接 FAIL。

## 输出分离

推荐：

- 锁定底图：`workbench/locked/19.png`
- 新字幕版本：单集最终版本的 `subtitled/19.png` 或 `publish/19.png`

不要在原锁定文件上直接烧录字幕后再声称“底图未改”。
