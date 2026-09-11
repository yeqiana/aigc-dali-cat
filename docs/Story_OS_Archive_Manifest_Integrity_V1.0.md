# Story OS Archive Manifest Integrity V1.0

更新日期：2026-09-11
范围：归档治理（不修改 Runtime、不修改生产流程、不修改 Gate 逻辑）
状态：已完成最小闭环修复（未提交 git）

## 一、背景

W-22 Story Semantic Trace 验证时发现：EP003 归档之后，`meta/release-manifest.json` 的 `artifacts.story` 仍然指向归档前路径

`episodes/10_彼此的天上/03_雾中的另一座生活区/...`

而实际文件已经移动到

`episodes/_archive/20260911_EP003_abandoned_雾中的另一座生活区/...`

结果是 Story Lock 路径不可解析。这是归档治理问题，不是 W-22 逻辑问题。

## 二、审计结果：当前归档机制

### 2.1 现有归档产物

| 产物 | 位置 | 内容 | 是否够用 |
| --- | --- | --- | --- |
| 非 Episode 标记 | `episodes/_archive/.storyos-non-episode.json` | 声明 kind / scope / `archived_from` / `archived_at` | 有 from，没有 to |
| pre-move 哈希清单 | `episodes/_archive/EP003_abandoned_manifest_20260911.txt` | 445 个文件的 sha256 + bytes + episode 内相对路径 | 能证明搬前内容，不能映射仓库路径 |
| 扫描豁免 | `episode_discovery.EXCLUDED_PARTS` 含 `_archive` | 归档目录不参与 Episode 扫描/门禁/推进 | 正确 |

结论：已有「搬前事实」，缺「搬后映射」。即：有 relocation 的**记录**（from + 文件哈希），没有 relocation 的**解析能力**（旧仓库路径 → 现仓库路径）。

### 2.2 破坏面（EP003 实测）

移动本身是完好的：所有关键产物的 sha256 与 pre-move 哈希清单逐字节一致。真正失效的只是**仓库相对路径解析**。

| 证据文件 | 指向归档前路径的引用数 |
| --- | --- |
| `meta/production-ledger.json` | 231 |
| `meta/visual-final-freeze.json` | 20 |
| `meta/frame-reviews/NN.json` | 20 个文件各 4 |
| `meta/story-gates.json` | 8 |
| `meta/release-manifest.json` | 5 |

全目录 JSON 扫描（249 个文件）：仓库相对引用合计 1510 条，其中 338 条仍可直接解析（同系列未搬动的兄弟集、series 级文件），1054 条需要前缀重映射后解析，118 条为自由文本 / runtime 临时引用（advisory）。

### 2.3 影响

- `validate_episode.py` 的 `require_repo_path` 对这些引用会直接报 `missing_path`；归档目录因 `EXCLUDED_PARTS` 不参与扫描，所以当前不会触发，但**归档证据本身已不可验证**。
- W-22 的 Story Lock 绑定校验因此得到 `sha256=null`，属于 fail-closed 的正确行为，但根因在归档侧。

## 三、最小修复方案

原则：**加一份移动事实 + 一个解析器 + 一个校验器**，不动 Runtime、不动 Gate、不重写被归档 Episode 的冻结记录。

1. Archive Relocation Manifest：`episodes/_archive/relocations.json`，记录 `from` / `to` / `prefix_map` / 完整性锚点。
2. Resolver：把仓库相对路径先按原样解析，失败再按 `prefix_map` 映射到新位置。direct 优先，保证未搬动的兄弟集引用不受影响。
3. Verifier：只对**已声明的锚点** fail closed —— Story Lock、分镜、视觉规范、字幕、制作复盘、核心证据文件；重新计算 sha256，并与 pre-move 哈希清单交叉核对。

   哈希口径（2026-09-11 修正）：取**仓库规范形态**的内容摘要，文本文件先归一化行尾为 LF，而不是工作树原始字节。`.gitattributes` 声明 `* text=auto eol=lf`，LF 才是 git 存取的形态；若按原始字节取哈希，同一个证据文件在作者机器（CRLF 工作树）与干净检出 / CI（LF）会算出两个值，校验就只在写出它的那台机器上通过——恰好把 fail closed 反过来。pre-move 清单交叉核对只在清单记录的**字节长度**与当前规范长度一致时才判 fail：长度不一致说明该条记录的是 CRLF 展开后的工作树字节（EP003 清单里 `meta/story-gates.json` 就是这样一条），任何检出都无法复现那些字节，因而无从证伪；此时以锚点摘要为准，它同样 fail closed。
4. 自由文本引用只做 advisory 统计，不作为硬失败。

新增代码：`episodes/_system/archive_relocation.py`（`build` / `resolve` / `scan` / `verify` / `self-test` CLI）。

## 四、数据结构

```json
{
  "schema_version": 1,
  "purpose": "Archive relocation registry: ...",
  "relocations": [
    {
      "schema_version": 1,
      "episode_id": "10-03",
      "series": "10_彼此的天上",
      "title": "雾中的另一座生活区",
      "kind": "abandoned_episode_archive",
      "archived_at": "2026-09-11",
      "relocated_at": "...",
      "from": "episodes/10_彼此的天上/03_雾中的另一座生活区",
      "to": "episodes/_archive/20260911_EP003_abandoned_雾中的另一座生活区",
      "evidence_state": "frozen",
      "file_manifest": "episodes/_archive/EP003_abandoned_manifest_20260911.txt",
      "prefix_map": [
        {"from": "episodes/10_彼此的天上/03_雾中的另一座生活区/",
         "to": "episodes/_archive/20260911_EP003_abandoned_雾中的另一座生活区/"}
      ],
      "anchors": [
        {"name": "story", "source": "release-manifest.artifacts.story",
         "recorded_path": "...归档前...", "resolved_path": "...归档后...",
         "status": "relocated", "sha256": "...", "bytes": 5784}
      ],
      "reference_health": {"total": 1510, "direct": 338, "relocated": 1054, "unresolved": 118}
    }
  ]
}
```

## 五、使用

```bash
# 生成 / 刷新某个已归档 Episode 的重定位条目
python episodes/_system/archive_relocation.py build <archived_episode_dir> --write

# 校验全部归档 Episode 的锚点与哈希
python episodes/_system/archive_relocation.py verify --all

# 单条解析：把一条旧的仓库相对路径映射到现在的实际位置
python episodes/_system/archive_relocation.py resolve episodes/10_彼此的天上/03_雾中的另一座生活区/docs/...

# advisory 扫描：统计 direct / relocated / unresolved 引用
python episodes/_system/archive_relocation.py scan <archived_episode_dir>
```

`verify` 的失败码：`archive_dir_missing` / `relocation_prefix_missing` / `prefix_map_mismatch` / `anchor_unresolved` / `anchor_hash_drift` / `file_manifest_hash_mismatch` / `relocation_schema_unsupported` / `relocation_entry_invalid`。

## 六、验证结果（EP003）

- `verify --all`：PASS（在 CRLF 工作树与干净 LF 检出两种环境下均 PASS）。
- Story Lock 锚点：`status=relocated`，解析到 `episodes/_archive/20260911_EP003_abandoned_雾中的另一座生活区/docs/02_雾中的另一座生活区_StoryLock_DRAFT_V1.0.md`，sha256 `2ed0c8c9...`，与 pre-move 哈希清单完全一致。
- 分镜 / 视觉规范 / 字幕 / 制作复盘 / 核心证据文件：规范摘要全部一致。
- 例外一条：`meta/story-gates.json` 的 pre-move 清单条目记录的是 CRLF 工作树字节（清单 `22273` 字节 / `6ccede86...`），规范形态为 `21715` 字节 / `d6dc3186...`。两者字节数不同，该条目无法在任何检出中复现，因此不参与交叉核对；其内容由锚点摘要 `d6dc3186...` fail closed 覆盖。上面「全部一致」的旧表述据此更正。
- 测试（干净 LF 检出、commit `f82596b` + 本次修正）：`tests/system/test_archive_relocation.py` 19 项通过；`python -m unittest discover -s tests/system` 302 项通过、0 失败；`contract_sync.py` 与 `story_os.py doctor` 均 PASS。

## 七、边界（本阶段不做什么）

- 不修改 Runtime、生产流程、machine gate。
- 不重写被归档 Episode 的冻结记录（release-manifest / story-gates / production-ledger / frame-reviews 保持原样）。
- 不重新生产 Episode，不删除任何历史资产。
- 不引入评分，不引入自动修复。
- 归档目录仍不参与 Episode 扫描与阶段推进。

## 八、后续建议

1. 归档流程规范化：移动前写 per-Episode 标记（含 `archived_from`），移动后立即 `build --write` + `verify --all`，把 verifier 作为归档完成的验收条件。
2. 当前 `_archive/.storyos-non-episode.json` 是仓库级单标记；多个 Episode 归档时应改为每个归档目录内各自一份标记。
3. 若未来允许归档 Episode 重新进入生产，需先决定「用重定位解析」还是「物理搬回」，二者不可混用。
4. 归档动作目前是人工旁路；可在 workflow 层增加归档 Step（本阶段不做）。

