# Story OS V3 Phase9 Metrics Pipeline Config（P9.34.4）

更新时间：

2026-09-11

## 1. 目标

阻塞项 #5「Real Metrics Pipeline」在 P9.33 已交付 exposition 侧端点（/metrics + /healthz 真机 E2E），但仍停在「真实 Prometheus / Grafana 采集实例待接」。本批补齐采集侧的配置资产，让操作者接入真实实例时零配置成本，把 #5 从「端点已交付、采集实例待接」收敛为「采集侧配置已交付，真实实例接入待操作者」。

## 2. 交付内容

文件：

- config/monitoring/prometheus/prometheus.yml：Prometheus scrape 配置，job 「storyos-runtime」，target 「127.0.0.1:18081」，scrape_interval 30s。
- config/monitoring/grafana/storyos-runtime-dashboard.json：Grafana dashboard（schemaVersion 38，10 面板），含 Worker / Runtime 两个查询变量与 Prometheus 数据源变量。

不做的事：

- 不安装 / 不假设已部署 Prometheus、Grafana、node_exporter。
- 不写凭据；配置只含 host/port/job 名与指标名。
- 不改任何运行时行为（exporter / worker / launcher 零改动）。

## 3. 指标契约（与 render_metrics 对齐）

本批配置基于 scripts/phase9_runtime_worker.py 的 render_metrics 已确认的指标名与标签，共 20 组：

| 指标 | 类型 | 标签 |
| --- | --- | --- |
| storyos_runtime_worker_up | gauge | worker_id |
| storyos_runtime_worker_ticks_total | counter | worker_id |
| storyos_runtime_worker_alerts_total | counter | worker_id |
| storyos_runtime_worker_open_incidents | gauge | worker_id |
| storyos_runtime_worker_consistency_scans_total | counter | worker_id |
| storyos_runtime_worker_last_tick_timestamp_seconds | gauge | worker_id |
| storyos_runtime_worker_heartbeat_ok | gauge | worker_id |
| storyos_runtime_probe_ok | gauge | worker_id, dependency(redis/mysql) |
| storyos_runtime_store_rows | gauge | worker_id, table |
| storyos_runtime_health_score | gauge | runtime |
| storyos_runtime_alert_level | gauge(one-hot) | runtime, level(INFO/WARNING/CRITICAL) |
| storyos_runtime_traces_total / _success_total / _failed_total / _running / _stuck | gauge | runtime |
| storyos_runtime_agent_success_rate / storyos_runtime_workflow_success_rate | gauge | runtime |
| storyos_runtime_consistency_entities | gauge | entity, verdict |
| storyos_runtime_health_state | gauge(one-hot) | runtime, status(HEALTHY/DEGRADED/UNHEALTHY/UNKNOWN) |

默认 runtime 标签值为 V3_RUNTIME。

## 4. Dashboard 面板

10 面板：

1. Runtime Health Score（gauge，0-100，红<60 / 橙60-85 / 黄85-95 / 绿>95）
2. Worker Up（stat，0/1）
3. Open Incidents（stat，>0 红）
4. Last Tick Age（stat，秒，>60 橙 / >180 红，用于识别陈旧文件）
5. Worker Tick Rate（timeseries，rate 5m）
6. Alerts Total（timeseries，increase 5m）
7. Dependency Probe（timeseries，按 dependency）
8. Store Rows（timeseries，按 table）
9. Traces（timeseries，total/success/failed/running/stuck）
10. Success Rate（timeseries，agent/workflow）

变量：DS_PROMETHEUS（数据源）、worker（worker_id 多选）、runtime（runtime 多选）。

## 5. 验证

- dashboard JSON：Python json.load 校验通过，10 面板、标题 Story OS V3 Runtime、uid storyos-runtime-v3。
- scrape 配置：job_name storyos-runtime、target 127.0.0.1:18081，与 launcher 默认 --metrics-port 一致。
- 指标名逐一比对 render_metrics 源码，无拼写漂移。

本批不新增运行时代码与测试（纯配置资产），故 tests/platform 基线不变：333 passed（口径见 reports/phase9_final_freeze_checklist.md 第 3 节；该文此前记 329，系二次实测前的旧计数）。

## 6. 边界与风险

- 真实 Prometheus / Grafana 实例仍需操作者部署；本批只交付可直接引用的配置资产。
- 端点只读单个 textfile，不做聚合 / 历史；历史与告警规则由采集实例负责（告警通道另见 #6 WebhookAlertChannel）。
- 端口 18081 为 launcher/exporter 默认值；操作者若改 --metrics-port，需同步改 target。

## 7. 结论

采集侧配置已交付（Prometheus scrape job + Grafana dashboard）。阻塞项 #5 由「端点已交付、采集实例待接」收敛为「采集侧配置已交付，真实实例接入待操作者」。
