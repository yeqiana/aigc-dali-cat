# Story OS MySQL JSON 瘦身测试计划

## 1. 目标与当前基线

本计划验证 Story OS 在 JSON → MySQL / Runtime Workspace / Redis 分层后的数据边界，重点确认：

- MySQL JSON 列只保存结构化投影、索引和可审计摘要；单个 `PAYLOAD` 不超过 16KB。
- 需要保留的完整文档写入 Runtime Workspace，并以 SHA-256、相对路径、字节数和版本信息引用。
- 读取时能按引用恢复完整文档；引用损坏、SHA 不一致、路径越界必须失败。
- 历史压缩只更新 MySQL 投影，不删除 Episode JSON；`EXPORT_ONLY`、Redis 热状态和 File 类不被误处理。
- 迁移、重跑、校验、回滚边界可验证；不得出现绕过统一策略的 MySQL JSON 写入。

当前已知基线：历史压缩已完成 169 行，最后一次只读审计 `oversized_columns=0`，重复 dry-run `candidate_rows=0`。本次测试不重复执行 `--apply`。

## 2. 测试范围

| 范围 | 对象 | 目标 |
| --- | --- | --- |
| 策略单元 | `platform/repository/mysql/payload_policy.py` | 字节上限、投影、引用、脱敏、确定性 |
| Repository | 所有已接入 bounded JSON 的 MySQL Repository | 统一拒绝超大直写，保持已有接口行为 |
| 持久化 | Prompt、Runtime Review、Metric、Approval、Release、Validation Report | 大对象外置/摘要化、投影入库、读取回填 |
| 历史压缩 | `scripts/phase9_mysql_payload_compact.py` | 计划、应用、reconcile、幂等、失败保护 |
| 审计 | `scripts/phase9_mysql_json_audit.py` | 全 JSON 列扫描、字节统计、零超限 |
| 数据边界 | 真实 MySQL 与 Runtime Workspace | UTF-8、空值、遗留数据、缺文件、SHA 漂移 |
| 稳定性 | 并发、重复运行、事务失败、外部文件写入 | 不产生半成功状态 |
| 性能 | 合成大对象、真实表扫描、投影吞吐 | 建立当前基线，不先臆定生产阈值 |
| 旁路检查 | MySQL JSON 写入调用点、敏感字段 | 防止以后重新写入巨大 JSON |

## 3. 用例矩阵

### 3.1 正例

| 编号 | 场景 | 通过条件 |
| --- | --- | --- |
| P-01 | 小于 16KB 的投影入库 | 原值可读，`OCTET_LENGTH(PAYLOAD)` 不超限 |
| P-02 | 超大 Prompt / Review / Metric / Approval / Release | 完整文档外置，表内仅保存有限投影和引用 |
| P-03 | 通过 SHA 读取外置文档 | SHA、路径、字节数校验通过并恢复原文 |
| P-04 | 同一记录重复 upsert / compact | 结果稳定，不新增重复外置文档，不扩大 PAYLOAD |
| P-05 | 历史完整 PAYLOAD 压缩 | 只改表内投影，不删 Episode JSON，reconcile 数量一致 |
| P-06 | 全量审计 | 所有 JSON 列扫描完成，`oversized_columns=0` |

### 3.2 反例与安全拒绝

| 编号 | 场景 | 通过条件 |
| --- | --- | --- |
| N-01 | Repository 直接写入超过 16KB JSON | 明确抛错，提示外置，不允许静默截断 |
| N-02 | 外部引用 SHA 不匹配 | 读取或更新失败，不污染数据库 |
| N-03 | 外部引用路径绝对路径、`..` 越界或指向目录 | 拒绝，不能逃逸 Runtime Workspace |
| N-04 | 外部文件缺失或内容不可解析 | 失败并保留原数据库行 |
| N-05 | Episode storage id 缺失、重复或无法唯一映射 | 压缩失败并报告，不按业务 id 猜测 |
| N-06 | projection 本身超过 16KB | 拒绝写入，不能以“投影”名义继续存大 JSON |
| N-07 | `--reconcile` 没有 `--apply` | 命令行拒绝，保持只读 |
| N-08 | 投影包含 prompt 正文、超长 source_files、完整 execution sessions 或密钥 | 断言不出现；敏感内容不得进入表内摘要 |

### 3.3 边界值

| 编号 | 场景 | 通过条件 |
| --- | --- | --- |
| B-01 | 空对象、空数组、null、空字符串 | 语义保持，策略不崩溃 |
| B-02 | 恰好 16,384 字节 | 允许；数据库实际 `OCTET_LENGTH` 仍不超限 |
| B-03 | 16,385 字节 | 拒绝或必须外置 |
| B-04 | 中文、emoji、组合字符 | 按 UTF-8 字节而不是字符数计算 |
| B-05 | 深层嵌套和超长数组 | 投影只保留必要摘要，不递归复制大字段 |
| B-06 | MySQL 字节数与 Python canonical JSON 字节数差异 | 以数据库 `OCTET_LENGTH` 为最终边界校验 |
| B-07 | 空表、NULL、遗留非标准 JSON | 审计报告可解释，不能误报为已迁移 |

### 3.4 压测与性能

| 编号 | 场景 | 记录指标 |
| --- | --- | --- |
| L-01 | 2K/10K/100K 合成大对象投影 | 总耗时、平均耗时、P95、峰值内存、投影平均字节 |
| L-02 | 真实表只读审计重复 3 次 | 总耗时、行数、数据库负载、结果一致性 |
| L-03 | 真实数据 dry-run 重复 3 次 | candidate、skip、error、耗时均稳定且 candidate=0 |
| L-04 | 同一记录并发重复 compact | 最终一份有效文档和一条稳定投影 |
| L-05 | 外置文件写入后数据库更新失败 | 不产生“表已引用但文件不存在”的不可恢复状态 |
| L-06 | 中途异常后重跑 | 可继续或安全跳过，不重复破坏既有证据 |

性能阈值先以本次实测基线为准：不为了通过测试修改业务逻辑，不把单机开发环境耗时直接宣称为生产 SLA。若出现数量或结果漂移，优先判为失败而不是只看耗时。

### 3.5 其他方向

- 兼容性：旧行仍可读取；新投影可被现有 Repository 正常消费。
- 完整性：原文 SHA、引用 SHA、投影身份字段和 storage id 一致。
- 可观测性：audit / compact 报告只输出统计和错误摘要，不输出 PAYLOAD、prompt 或凭据。
- 权威边界：不处理 `EXPORT_ONLY` 的删除，不把 `episode-state.json`、`story-gates.json`、release 导出视图当普通候选删除。
- 分层边界：不把 Redis hot state 当 MySQL 历史 JSON；不把 runtime worker 日志、archive revision、test fixture 塞入数据库。
- 旁路防回归：扫描 MySQL JSON 写入点，确认没有绕过统一策略的 `json.dumps` / 原始 `PAYLOAD` 写入。
- 交付回归：System、Platform、Doctor、Mock Pipeline 的已有门禁不能因瘦身回归。

## 4. 执行顺序

1. 先运行策略、Repository、Persistence 单元测试。
2. 再运行边界和反例测试；发现缺口时补测试，不改变生产数据。
3. 运行 Platform 全量与 System 全量测试。
4. 运行真实库只读 audit、compact dry-run，并保存统计结果。
5. 运行合成投影压测和真实审计性能基线。
6. 做 MySQL JSON 写入旁路扫描、敏感字段扫描和工作区变更复核。

## 5. 验收标准

### P0 必须通过

- 所有策略、Repository、Persistence 测试通过。
- 超大 JSON 不能直写，外置文档可校验、可恢复。
- 历史压缩重复 dry-run 为 0 candidate、0 error。
- 真实 MySQL audit 为 0 个超 16KB JSON 列。
- Platform 与 System 全量测试通过。
- 没有发现新的 MySQL 巨大 JSON 写入旁路。

### P1 建议通过

- 全部边界、反例、遗留数据兼容用例通过。
- 并发重复、异常恢复、敏感字段和权威边界检查通过。

### P2 记录基线

- 合成 2K/10K/100K 投影和真实审计的耗时、P95、内存、数据库负载。
- P2 仅用于后续优化，不以开发机单次结果替代生产容量验收。

## 6. 结果记录

| 批次 | 命令/范围 | 结果 | 证据 |
| --- | --- | --- | --- |
| T-01 | 策略、Repository、Persistence 回归 | PASS：54 passed | pytest 定向回归 |
| T-02 | Platform 全量 | PASS：423 passed / 5 warnings | pytest 全量 |
| T-03 | System 全量 | PASS：1134 passed / 1 skipped / 90 subtests | pytest 全量 |
| T-04 | MySQL JSON audit | PASS：23 列在 8KB / 12KB / 16KB 下均 0 超限；当前最大 8,167B | `phase9_mysql_json_audit.py` |
| T-05 | compact dry-run 重复性 | PASS：默认 0 candidate / 310 skipped / 0 error；严格 8KB 回填 12 行并全部 reconcile | `phase9_mysql_payload_compact.py` |
| T-06 | 边界、反例、旁路扫描 | PASS：40 个策略/持久化用例；`--reconcile` 无 `--apply` 以 exit 2 拒绝；MySQL 写入统一经 bounded policy | pytest + 静态扫描 |
| T-07 | 压测与性能基线 | PASS：2K/10K/100K × 5 投影；约 3.5K–5.5K ops/s | `phase9_mysql_json_perf.py` |

### 6.1 本次性能基线

测试环境为当前开发机，使用合成对象、纯内存、不开 MySQL/Redis。100K 档每类投影结果如下：

| 投影 | 总耗时 | 吞吐 | P95 |
| --- | ---: | ---: | ---: |
| Prompt Package | 23.000s | 4,347.78 ops/s | 192.8µs |
| Runtime Review | 23.236s | 4,303.66 ops/s | 198.3µs |
| Metric Snapshot | 18.117s | 5,519.53 ops/s | 149.3µs |
| Approval | 26.999s | 3,703.82 ops/s | 249.6µs |
| Release | 28.162s | 3,550.85 ops/s | 255.9µs |

结果说明：投影平均 347–606 字节，明显低于 16KB 上限；性能随数量近似线性。该结果是投影 CPU 基线，不代表包含磁盘、网络、事务和生产并发的 SLA。

历史数据补充收口：在原有 16KB 压缩完成后，又以 12KB 阈值回填 5 行、以 8KB 阈值回填 12 行；两轮均为写外置文档、投影回写、回读校验，`episode_json_deleted=0`。最终真实库在 8KB 阈值下也无超限行。

## 7. 已知限制

- 本次默认不对生产库注入故障，不做破坏性回滚演练；事务失败场景先用测试替身验证。
- MySQL 与 Redis 的网络、磁盘和生产并发条件未在本机完全复现；性能结果只能作为当前环境基线。
- 只有明确授权后才可再次执行数据库写入型 `--apply`；本轮测试不包含该动作。
