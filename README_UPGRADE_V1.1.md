# Story OS V1.1 整合修复

本升级针对 V1.0 评审发现的架构问题：

1. 消除 `episode.yaml stage` 与原 `_system` 的双状态源。
2. `episode-state.json` 恢复为唯一机器阶段事实源。
3. 新增 `meta/story-gates.json`，只保存门禁证据。
4. Codex 通过 `AGENTS.md → SKILL.md` 自动接入 Story OS。
5. `AGENTS.md` 的推流规范版本从 V1.3 对齐到 V1.4。
6. VISUAL_CALIBRATED 前强制 4 张视觉准入 + 连续性锚点。
7. PRODUCTION_PASSED 前强制声音卡/字幕/连续性/真实性 review。
8. PUBLISH_READY 本地验收增加 1080×1920 与锁图 SHA-256。
9. GitHub Actions 改为调用原生 `_system`，而不是验证第二套 manifest。
10. 旧剧集不批量迁移；重新进入制作时显式 `migrate-gates`。

## 安装后新篇

```bash
python episodes/_system/episode_state.py init \
  episodes/10_新系列/01_新故事 \
  --id 10-01 \
  --series 10_新系列 \
  --title "新故事" \
  --frame-count 20
```

## 旧篇重新进入制作

```bash
python episodes/_system/episode_state.py migrate-gates <episode_dir>
```

## 验收

```bash
python episodes/_system/test_validator.py -v
python episodes/_system/validate_episode.py --all --metadata-only
```

V1.0 的 `episode.yaml` 模板与对应第二状态机 validators 会由安装器删除；已有真实 episode 资产不会删除。
