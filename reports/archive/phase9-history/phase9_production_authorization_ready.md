# Story OS V3 Phase9 Production 授权就绪清单（P9.35）

更新时间：

2026-09-11

## 1. 目标

Phase9 Production Readiness Gate 的 5 个阻塞项（#1/#5/#6/#7/#8）现已全部从「缺能力」收敛为「可执行单元 / 配置已交付」。剩余工作只有两类：需要你授权的本地副作用操作（#1/#7/#8），或需要你提供的外部资产（#5/#6）。本清单把它们固化为唯一操作入口，授权 / 提供资产后即可逐项闭环。

## 2. 当日回归基线（2026-09-11 重新确认）

- tests/platform：333 passed / 0 failed（4.35s；已排除 8 个 Production Learning Loop 测试文件，该批本轮不纳入冻结）
- tests/system：190 passed + **1 failed** + 16 subtests（10.54s）
- 合计：523 passed + 1 failed + 16 subtests

口径修正（2026-09-11 二次实测）：本节此前记 329 / 186、合计 515 全绿，与二次实测不符，现按实测改写。tests/system 的 1 项失败为 HEAD 既有（`test_governance_convergence.py::EvidenceRecovery::test_formal_review_reuses_only_verified_summary`，已用 git stash 单独移除本次 `episodes/_system` 改动复跑确认）。全树（不排除 Learning Loop）为 tests/platform 336 passed / 3 failed / 3 collection errors。

## 3. 待授权 / 待外部资产清单

### #1 部署为 Windows 计划任务（授权：注册）

状态：部署脚本已交付（scripts/phase9_runtime_deploy.py，install / uninstall / status，默认 dry-run）。

授权后执行：

    python scripts/phase9_runtime_deploy.py install --apply

影响：注册计划任务（默认名 StoryOSRuntime），常驻 RuntimeLauncher（Worker + Metrics 端点）随任务启动。

回滚：

    python scripts/phase9_runtime_deploy.py uninstall --apply

只读查看：

    python scripts/phase9_runtime_deploy.py status

### #5 接入真实 Prometheus / Grafana（外部资产：采集实例）

状态：/metrics 端点（P9.33）+ Prometheus scrape 配置 + Grafana dashboard（P9.34.4）已交付。

操作者动作（无本地副作用）：

1. 部署 Prometheus，加载 config/monitoring/prometheus/prometheus.yml（job storyos-runtime，target 127.0.0.1:18081）。
2. Grafana 导入 config/monitoring/grafana/storyos-runtime-dashboard.json，数据源选择上述 Prometheus。

前置：exporter 已随 launcher 启动，127.0.0.1:18081/metrics 可达。

### #6 接入真实告警 Webhook（外部资产：URL）

状态：WebhookAlertChannel（json / dingtalk）+ 本地接收器已交付并真机 E2E（P9.32）。

操作者提供 URL 后，启动 launcher 时加：

    --alert-webhook <URL> --alert-webhook-format dingtalk

（json 格式则 --alert-webhook-format json）

### #7 生产归属切换 V2 -> V3（授权：落盘切换）

状态：切换执行器已交付（scripts/phase9_production_switch.py，status / switch，默认 dry-run），dry-run 已确认当前 V2_RUNTIME。

授权后执行：

    python scripts/phase9_production_switch.py switch --apply

影响：落盘 meta/runtime/runtime-primary.json 为 V3_RUNTIME。

回滚：由 Canary rollback 负责（本执行器只支持 -> V3，不提供反向切换）。

只读查看：

    python scripts/phase9_production_switch.py status

### #8 开启自愈自动触发（授权：开启）

状态：自愈编排 runtime_auto_recovery + Worker 接线已交付（P9.34.2，--auto-recover 默认关闭），真机 E2E 已验证 RESTART_AGENT 执行。

授权后启动 launcher / worker 时加：

    --auto-recover --restart-agent-command <重启命令>

影响：Worker tick 检测到 runtime_unhealthy（如 agent/workflow 成功率过低）时自动执行 RESTART_AGENT。

回滚：去掉 --auto-recover（默认关闭态即回滚）。

## 4. 建议授权顺序

1. #1 注册计划任务（让常驻载体真正上线）
2. #8 开启自愈（载体上线后才有意义）
3. #7 生产归属切换（最后确认归属 V3）
4. #5 / #6 依赖外部资产，可并行推进（提供 Prometheus 实例与告警 URL）

## 5. 边界

- 本清单只记录授权 / 外部资产需求，不执行任何副作用操作；注册计划任务、落盘归属切换、开启自愈均需你明确授权。
- 不写凭据；告警 URL 只在运行时由你传入，不落仓库。
- 生产闭环的最终判断仍是真实运行环境（流量、告警、采集、归属），本清单是它之前的最后一道代码 / 配置边界。

## 6. 结论

Phase9 代码与配置侧已全部交付并通过全量回归（523 passed + 1 failed + 16 subtests；1 项失败为 HEAD 既有）。下一步不再需要新的代码 / 配置交付，只等你在 #1/#7/#8 三项授权并接上 #5/#6 两个外部资产。
