# Story OS V1.2｜Production Engine 升级包

适配：`yeqiana/aigc-dali-cat` 的 `story` 分支（基于 2026-08-27 当前结构设计）。

本升级包不替换你的 `episodes/` 历史成片、研究数据或发布资产。它只新增 Production Engine，并对少量现有规范/状态机文件做**可备份、可回滚的定点补丁**。

## V1.2.1 打包修复

修复首个 V1.2 ZIP 中两份中文 `standards/` 文件名的编码问题。安装器现在会按文件内容自动识别并修复已经落入仓库的乱码文件名，不影响已完成的 V1.2 代码补丁。

如果已经安装过首个 V1.2 包，直接用本修正版再次运行同一安装命令即可；补丁会显示 `[OK] already patched`，并自动把乱码规范文件清理/恢复成正确中文文件名。


## 这次最重要的变化

### 1. 未指定画幅时统一默认 4:5

```text
默认：4:5  → 1080×1350
可选：9:16 → 1080×1920（必须明确指定）
```

默认规则同时落到：

- `AGENTS.md`
- 根 `SKILL.md`
- `standards/制作规范_正式版.md`
- `standards/最终字幕视觉规范_V1.1.md`
- `episodes/_system/episode_state.py`
- `episodes/_system/validate_episode.py`
- `episodes/_system/production_ledger.py`

因此不是“文档默认 4:5、脚本仍验 9:16”的半升级。

历史已锁定 9:16 的 episode 不追溯修改；其 `release-manifest.json -> episode.aspect_ratio=9:16` 会继续得到 1080×1920 验收。

## 2. Production Engine

新增：

```text
episodes/_system/
├── canvas_spec.py
├── production_ledger.py
├── contact_sheet.py
└── test_production_engine.py
```

逐帧保存：

- prompt hash / 字符数 / bytes
- capture profile ID
- model
- reference path / role / kind / SHA-256
- request fingerprint
- 技术失败记录
- 内容返修次数
- 当前候选
- approved asset
- lock SHA-256
- batch

`production-ledger.json` **不是第二状态机**，不会覆盖 `episode-state.json.current_state`。

## 3. 技术失败与内容失败分离

```text
网络失败 / timeout / no candidate
→ TECH_FAILED
→ 不消耗内容返修
```

真正的角色、道具、机位、真实性、电影感等内容失败才进入：

```text
CONTENT_FAILED
→ REPAIR_AUTHORIZED
→ REPAIRING
```

每帧最多一次内容返修。返修后再次内容失败进入 `NEEDS_USER`。

## 4. Original / Repair / Approved / Publish 分离

新生产目录：

```text
production/
├── originals/
├── repairs/
├── approved/
├── publish/
└── contact-sheets/
```

原图不再因为重做而被覆盖。

## 安装

把本 ZIP 解压到任意目录，然后在 `aigc-dali-cat` 的 `story` 工作树执行：

```bash
python <升级包目录>/INSTALL_V1.2.py --repo .
```

先看兼容性、不修改文件：

```bash
python <升级包目录>/INSTALL_V1.2.py --repo . --dry-run
```

安装器会自动把被修改的旧文件备份到：

```text
.story-upgrade-backups/v1.2-YYYYMMDD-HHMMSS/
```

## 新篇初始化

现在不传 `--aspect-ratio`：

```bash
python episodes/_system/episode_state.py init \
  episodes/10_新系列/01_新故事 \
  --id 10-01 \
  --series 10_新系列 \
  --title "新故事" \
  --frame-count 20
```

得到：

```text
4:5 / 1080×1350
```

只有明确需要 9:16 时：

```bash
... --aspect-ratio 9:16
```

## Production Ledger

初始化：

```bash
python episodes/_system/production_ledger.py init <episode_dir>
```

它优先读取当集 manifest；如果 manifest 也没指定画幅，才使用全局默认 4:5。

登记生成请求：

```bash
python episodes/_system/production_ledger.py begin <episode_dir> \
  --frame 01 \
  --capture-id phone_primary \
  --prompt-file workbench/prompts/01.txt
```

记录成功候选：

```bash
python episodes/_system/production_ledger.py success <episode_dir> \
  --frame 01 \
  --path production/originals/01.png
```

图片尺寸必须精确符合该 episode 画幅。

内容通过：

```bash
python episodes/_system/production_ledger.py review <episode_dir> \
  --frame 01 --decision pass --notes "通过"

python episodes/_system/production_ledger.py promote <episode_dir> --frame 01
```

技术失败：

```bash
python episodes/_system/production_ledger.py tech-fail <episode_dir> \
  --frame 01 --code timeout --message "service timeout"
```

不会占用内容返修。

## 自动联系表

安装 Pillow 后：

```bash
python -m pip install Pillow
python episodes/_system/contact_sheet.py <episode_dir> --source candidate
```

或：

```bash
python episodes/_system/contact_sheet.py <episode_dir> --source approved
```

## 安装后测试

```bash
python episodes/_system/test_production_engine.py -v
python episodes/_system/test_validator.py -v
python episodes/_system/validate_episode.py --all --metadata-only
```

## 回滚

安装完成时控制台会显示备份目录。恢复被修改的旧文件：

```bash
python <升级包目录>/ROLLBACK_V1.2.py \
  --repo . \
  --backup .story-upgrade-backups/v1.2-YYYYMMDD-HHMMSS
```

新加的 V1.2 文件不会自动删除，防止误删你安装后产生的数据。

## 设计边界

保留你现有 Story OS 的优势：

```text
选题 / 最近5篇反同质化 / 故事 / 推流适配 / 发布 / 数据复盘
```

本次只补下层：

```text
Canvas → Generate → Fingerprint → Retry → Review → Repair → Approve → Lock → Package
```

即：**Story OS 决定做什么，Production Engine 保证每一张怎么可靠做出来。**
