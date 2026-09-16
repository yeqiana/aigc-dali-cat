# Story OS V3 Phase9 Runtime Alert Channel（P9.32）

更新时间：

2026-09-10

## 1. 目标

P9.29-P9.31 已交付告警产生、事件生命周期与恢复执行，但 CRITICAL 告警一直只落盘 JSONL，没有真正送达人。本批交付第一类真实告警通道，把 CRITICAL 告警从「只落盘」推进到「有真实送达通道」。

## 2. 交付物

### WebhookAlertChannel

文件：

platform/operations/runtime_alert_channel.py

- 标准库实现（urllib），不引入新框架、不引入新依赖。
- 两种格式：json（原始 JSON）、dingtalk（钉钉 markdown 包装，不含签名）。
- deliver() 永不抛异常：送达失败如实记进 AlertDeliveryResult，不拖垮 Worker tick。
- transport 可注入，离线可测。
- build_webhook_channel(url)：URL 未配置时返回 None（默认安全姿态，等于无通道）。

### Worker 挂载

文件：

scripts/phase9_runtime_worker.py

- 新增 --alert-webhook URL、--alert-webhook-format json|dingtalk。
- CRITICAL 告警在落盘 JSONL 之外，同步 POST 到 webhook；送达结果写入 alert_log 的 alert_webhook_result。
- 证据只记 alert_webhook_configured 布尔，不写 URL / 凭据。

### 本地接收器

文件：

scripts/phase9_alert_channel_receiver.py

- E2E 验证用本地 HTTP 端点，收到 POST 落盘 evidence JSONL，收到 expect-count 条后退出 0。

## 3. 真机 E2E 证据

环境：真实 Redis 127.0.0.1:6379 + 拒绝 MySQL 端口 127.0.0.1:1（真实连接拒绝）。

- Worker 一次 tick 产生真实 CRITICAL mysql_unreachable 告警（连接拒绝 10061）。
- --alert-webhook 把告警 JSON POST 到本地接收器 127.0.0.1:18099。
- 接收器捕获 1 条 CRITICAL 告警：worker_id=alert-channel-drill、reason=mysql_unreachable、incident_id=inc_alert-channel-drill_1_mysql_unreachable。
- 证据（.storyos/alert-channel/，gitignored 本地取证）：
  - worker-evidence.json：alert_counts CRITICAL=1，alert_webhook_configured=true
  - receiver-evidence.jsonl：1 条 POST，content_type application/json; charset=utf-8
  - 退出码：worker=2（仍有 CRITICAL 告警）、receiver=0（收到 1 条）

## 4. 边界与风险

- 真实外部端点（钉钉 / 企业微信 / 自建 webhook）仍待操作者提供 URL；本轮只证明本地端到端链路。
- 钉钉 markdown 不含加签（自定义机器人安全设置需另行处理）。
- 本模块只做送达，不建事件、不触发恢复；事件与恢复仍由既有 RuntimeAlertManager / RecoveryExecutor 负责。
- 本地接收器仅用于验证，不是生产告警通道。

## 5. 测试

tests/platform：296 passed（288 → 296，+8：runtime_alert_channel 离线 7 例 + worker webhook 集成 1 例）。
