# Story OS V1.5 — 现有规范机器化

V1.5 不再新增创作规则，目标是把已经存在于主规范中的硬条件变成机器可验证执行层。

## 这次真正机器化的内容

1. **真实性卡**：年代、地点、拍摄者、设备、三种拍摄状态、第一视角物理解释成为 VISUAL gate 的结构化证据。
2. **三张真实性校准**：固定为普通基线 / 最差成立条件 / 首次重大异常；图号、准入关系、SHA 与联系表都可校验。
3. **Reference Gate**：身份 / 道具 / 地点 / capture_style 可登记为 reference asset，支持 required anchors 和 SHA 锁定。
4. **逐帧真实性审查**：每帧一个 JSON，普通相册四问、机位物理、非电影化、连续性与七项摄影红旗进入机器门禁。
5. **Production Ledger 联动**：帧数、状态、返修次数、approved asset 与 lock hash 不一致时禁止进入 PRODUCTION_PASSED。
6. **旧项目兼容**：迁移项目默认 `strict=false`，不会批量伪造历史证据；显式 `enable-machine-gates` 后才严格执行。
7. **状态迁移双重门禁**：`validate_episode.py` + `machine_gate.py` 必须同时通过。
8. **CI**：新增机器门禁单测和 metadata-only 全仓库扫描。

## 不机器化的内容

以下保持人工/多模态终审：真实感、滑动欲望、角色视觉相似度、高潮够不够强、结尾是否值得回看。机器只保证“已有判断不会因为证据缺失、hash 漂移、返修越界而被绕过”。

## 新篇最短流程

```bash
python episodes/_system/episode_state.py init <episode_dir> --id ... --series ... --title ...
python episodes/_system/evidence_tool.py init-reviews <episode_dir>
# 填故事门禁 / 真实性卡 / 四张视觉准入
# 锁三张校准并生成 calibration sheet
python episodes/_system/machine_gate.py <episode_dir> --target VISUAL_CALIBRATED
# 逐帧生产 + review + promote/lock
python episodes/_system/machine_gate.py <episode_dir> --target PRODUCTION_PASSED
```

## 老篇重新制作

```bash
python episodes/_system/episode_state.py migrate-gates <episode_dir>   # 若还没有 story-gates
python episodes/_system/episode_state.py enable-machine-gates <episode_dir>
```

开启严格模式不等于通过。所有证据仍必须真实补齐。
