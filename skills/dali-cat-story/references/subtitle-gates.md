# Subtitle Gates

字幕内容遵循 `standards/字幕人话化与声音卡规范_V1.1.md`；视觉遵循 `standards/最终字幕视觉规范_V1.0.md`。

## 文件结构

推荐单集使用 `docs/subtitles.yaml`：

```yaml
voice_card:
  person: "我"
  age: "20多岁"
  role: "返乡青年"
  knowledge_boundary: "普通人，不懂民俗术语"
  recording_reason: "记录回村路上捡到的旧MP4"
  knows_now: "只知道设备里出现不属于自己的画面"
  does_not_know: "不知道异常来源"
  stress_language: "越害怕句子越短"
frames:
  1: "..."
silent_frames: []
clues: []
```

## 自动检查

- 声音卡关键字段是否填写。
- 1..N 每帧是否有字幕或明确列为静默图。
- 静默图与字幕图是否冲突。
- 同一句字幕是否重复。
- 连续多帧是否反复用“我发现 / 更怪的是 / 直到…”等模板开头（WARN）。
- 线索是否登记了回收帧（WARN/FAIL 取决于字段完整性）。

自动检查不替代连续三图朗读测试。
