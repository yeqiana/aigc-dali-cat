# Story OS standards 视觉经验规范解耦方案

日期：2026-09-11

定位：仓库治理第 4 步交付物。原计划把视觉经验类规范从 `standards/` 迁往 `library/visual-patterns/`，执行前扫描发现存在生产代码硬引用，按治理规则 5.2「当前生产代码引用 → 停止并报告」暂停，改为先交付解耦方案。

状态：Executed（方案 B 已执行，2026-09-11）。`standards/` 原文件与代码均未改动。

---

## 一、背景与阻塞

原计划迁移的 4 份文件：

| 文件（当前路径） | AUTHORITY_INDEX 登记 | 其它引用 | 直接搬迁后果 |
| --- | --- | --- | --- |
| `standards/导演镜头光影与异常隐藏规范_V1.0.md` | `active_subordinate`，`active: true`（第 176 行） | `contract_sync.py:224` 硬校验文件存在、`contract_sync.py:230` 硬校验 AUTHORITY_INDEX 含该 token；`制作规范_正式版.md:206`；`AIGC_Directing_Quality_V1.0.md:40` | `contract_sync.py` 直接报错 |
| `standards/环境物理与异常放大规范_V1.0.md` | `active_subordinate`（第 257 行） | `制作规范_正式版.md:287` | 权威链接断链 |
| `standards/真实性与共享风格锚点规范_V1.1.md` | `active_subordinate`（第 45 行） | `AGENTS.md:22`、`README.md:50`、`制作规范_正式版.md:275`、`standards/_superseded/风格锚点_流水席_村子_误入小镇_V1.1.md:195/473` | 权威链接断链 |
| `standards/设备物理档案与参考预算规范_V1.0.md` | `active_subordinate`（第 183 行） | 无其它引用 | `story_os_doctor.py` 报 `AUTHORITY_MISSING` |

共同阻塞点：

1. `episodes/_system/story_os_doctor.py` 会把 `standards/AUTHORITY_INDEX.json` 中所有 `active: true` 的 `path` 当作必须存在的文件；文件缺失即 ERROR `AUTHORITY_MISSING`。
2. `episodes/_system/contract_sync.py:224` 对 `standards/导演镜头光影与异常隐藏规范_V1.0.md` 做路径存在性硬校验，`:230` 再校验 AUTHORITY_INDEX 文本包含该路径 token。

因此直接 `git mv` 会让 `contract_sync.py` 与 `story_os_doctor.py` 同时失败。这属于「当前生产代码依赖」，不是文档链接问题。

---

## 二、解耦方案

### 方案 A：保持现状（零改动）

4 份规范继续留在 `standards/`，Pattern Library 只做「引用式登记」。工作量最小，门禁零风险。

缺点：`library/visual-patterns/` 不拥有实体文件，模式库不够自包含。

### 方案 B：Pattern Source 副本 + `standards/` 保持权威（推荐，零代码改动）

在 `library/visual-patterns/` 下新增「Pattern Source」条目（可为摘录、索引或适配后的提示词素材），`standards/` 原文件保持为门禁权威不动。

- `library/visual-patterns/README.md` 已声明 Pattern Library 不直接进入生产门禁。
- 不需要改 `AUTHORITY_INDEX.json`、`contract_sync.py`、`story_os_doctor.py`。
- Agent Prompt Builder / Visual Agent 从 `library/` 取素材，门禁仍从 `standards/` 取权威。

风险：同一主题存在两份文件，需要在 README 明确「`standards/` 为准，`library/` 为经验素材」，避免形成第二权威。

### 方案 C：硬搬迁 + 解耦（需要单独授权）

把 4 份文件迁到 `library/visual-patterns/`，并同步改代码与登记。改动清单见第三节。

风险最高：`contract_sync.py` / `story_os_doctor.py` 是门禁，改它们等于改 Runtime 契约，必须配套契约回归。

---

## 三、方案 C 的改动清单（仅在单独授权后执行）

1. `standards/AUTHORITY_INDEX.json`：将 4 条记录从 `active_subordinate / active: true` 改为 `reference / active: false`，`path` 指向 `library/visual-patterns/` 新位置。注意 `story_os_doctor.py` 只对 `active` 条目校验存在性，改完即不再报 `AUTHORITY_MISSING`。
2. `episodes/_system/contract_sync.py:224`：移除或替换 `Path("standards/导演镜头光影与异常隐藏规范_V1.0.md")`。
3. `episodes/_system/contract_sync.py:230`：同步移除或替换 token 列表中的该路径。
4. 文档链接重写：`AGENTS.md:22`、`README.md:50`、`standards/制作规范_正式版.md:206/275/287`、`standards/AIGC_Directing_Quality_V1.0.md:40`、`standards/_superseded/风格锚点_流水席_村子_误入小镇_V1.1.md:195/473`。
5. 回归验证：`python episodes/_system/contract_sync.py` 与 `python episodes/_system/story_os_doctor.py` 必须 0 error。

范围提示：改动 2、3 属 Runtime 代码；改动 4 中的 `制作规范_正式版.md` 是唯一创作权威，修改其正文链接等于改生产规范内容。这两点在当前任务「不修改生产规范内容 / 不修改 Runtime 核心逻辑」约束下**不可执行**，需要单独授权。

---

## 四、推荐路径

1. 本轮采用方案 B：`library/visual-patterns/` 建立引用式 Pattern Source，`standards/` 原文件不动。
2. 方案 C 延后，等出现独立授权窗口且愿意承担契约回归成本时再评估。

### 执行记录（2026-09-11）

已按方案 B 执行：

1. 新增 `library/visual-patterns/visual-experience/README.md`：4 份 `standards/` 视觉经验规范的引用式 Pattern Source（经验来源 + 非权威摘要 + 权威指针），另登记 `documentary-realism/` 实体模板。
2. 更新 `library/visual-patterns/README.md`：目录新增 `visual-experience/`，边界说明写明采用方案 B。
3. 未改动 `standards/AUTHORITY_INDEX.json`、`contract_sync.py`、`story_os_doctor.py`、`standards/制作规范_正式版.md` 与 4 份原规范。

回归：`contract_sync.py` PASS、`story_os_doctor.py` errors=0。方案 C 仍为待授权项。

---

## 五、禁止操作（本轮）

- 移动 `standards/` 下 4 份 `active` 规范。
- 修改 `AUTHORITY_INDEX.json` 的 active 登记。
- 修改 `contract_sync.py` / `story_os_doctor.py`。
- 修改 `standards/制作规范_正式版.md` 正文。
- 修改 `episodes/**` 与 EP003 生产状态。
