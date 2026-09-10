# Story OS V3 Phase9 Runtime Metrics Endpoint（P9.33）

更新时间：

2026-09-10

## 1. 目标

Worker / Watchdog 已把 Prometheus textfile 原子落盘，但没有可被采集的 HTTP 端点，采集管线仍断在「只落盘」这一步。本批补一个标准库 HTTP sidecar，把最新 metrics 文件以 Prometheus exposition 格式暴露在 /metrics，让任何 Prometheus 都能拉取。

## 2. 交付物

文件：

scripts/phase9_metrics_exporter.py

- 端点：GET /metrics（text/plain; version=0.0.4; charset=utf-8）、GET /healthz（200 JSON）。
- 标准库实现（http.server.ThreadingHTTPServer），不引入新框架、不引入新依赖。
- 只读指定 metrics 文件；文件缺失 / 不可读返回 503 错误文本，不抛异常。
- 不写凭据、不注册系统服务、不假设已部署 Prometheus / Grafana / node_exporter。

## 3. 真机 E2E 证据

环境：真实 Redis 127.0.0.1:6379 + 真实 Worker（--no-mysql 离线模式，健康 HEALTHY）。

- Worker 一次 tick 退出码 0，健康分 100，0 告警；产出 60 行 Prometheus metrics。
- 采集端点 127.0.0.1:18082 就绪，GET /metrics 返回 200，Content-Type text/plain; version=0.0.4; charset=utf-8。
- 响应包含 storyos_runtime_worker_up{worker_id="metrics-drill"} 1 与 storyos_runtime_health_state。
- GET /healthz 返回 200 {"ok":true}。
- 证据：.storyos/metrics/（gitignored 本地取证）：worker-evidence.json、e2e-result.json。

## 4. 边界与风险

- 真实 Prometheus / Grafana 采集实例仍需操作者部署并配置 scrape 指向该端点；本轮只证明 exposition 侧端到端可用。
- 端点只读单个 textfile，不做聚合 / 历史；历史能力由采集实例负责。
- 未注册系统服务 / 计划任务；sidecar 与 Worker 需由外层载体分别拉起。

## 5. 测试

tests/platform：300 passed（296 → 300，+4：metrics exporter 离线 4 例，含回环 socket 端点验证）。
