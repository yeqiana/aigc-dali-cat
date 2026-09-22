"""Runtime Alert Channel（P9.32）—— CRITICAL 告警的真实送达通道。

P9.29-P9.31 交付了告警产生（RuntimeAlertManager）、事件生命周期（Incident）与
恢复执行（RecoveryExecutor），但告警 JSON 一直只落盘 JSONL，没有真正送达人。
本模块补上第一类真实通道：WebhookAlertChannel，把告警 POST 到可配置端点。

设计约束：
- 只用标准库（urllib），不引入新框架、不引入新依赖。
- URL 由调用方通过 CLI / 环境变量注入；本模块不写死、不回读任何密钥。
- deliver() 永不抛异常：送达失败要如实记进 AlertDeliveryResult，不能拖垮 Worker tick。
- 支持两种格式：json（原始 JSON）、dingtalk（钉钉 markdown 包装，不含签名）。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, Protocol
from urllib import request


@dataclass(frozen=True)
class AlertDeliveryResult:
    ok: bool
    status: str
    code: int | None = None
    error: str | None = None
    channel: str = ""


class AlertChannel(Protocol):
    def deliver(self, alert: Mapping[str, Any]) -> AlertDeliveryResult:
        ...


def format_dingtalk(alert: Mapping[str, Any]) -> dict:
    """把内部告警记录包装成钉钉 markdown 消息体（不包含签名）。"""
    level = str(alert.get("level") or "UNKNOWN")
    reason = str(alert.get("reason") or "unknown")
    worker_id = str(alert.get("worker_id") or "-")
    runtime = str(alert.get("runtime") or "-")
    timestamp = str(alert.get("timestamp") or "-")
    lines = [
        "### Story OS Runtime 告警（" + level + "）",
        "- worker: " + worker_id,
        "- runtime: " + runtime,
        "- reason: " + reason,
        "- at: " + timestamp,
    ]
    detail = alert.get("detail")
    if detail:
        lines.append("- detail: " + json.dumps(detail, ensure_ascii=False, default=str))
    return {
        "msgtype": "markdown",
        "markdown": {
            "title": "StoryOS[" + level + "] " + reason,
            "text": chr(10).join(lines),
        },
    }


class WebhookAlertChannel:
    """把告警 POST 到指定 webhook URL；transport 可注入以便离线测试。"""

    def __init__(self, url: str, *, format: str = "json", timeout: float = 15.0, opener=None) -> None:
        if not url:
            raise ValueError("url is required")
        if format not in ("json", "dingtalk"):
            raise ValueError("unsupported format: " + format)
        self.url = url
        self.format = format
        self.timeout = float(timeout)
        self._opener = opener

    def _payload(self, alert: Mapping[str, Any]) -> bytes:
        body = format_dingtalk(alert) if self.format == "dingtalk" else dict(alert)
        return json.dumps(body, ensure_ascii=False, default=str).encode("utf-8")

    def deliver(self, alert: Mapping[str, Any]) -> AlertDeliveryResult:
        data = self._payload(alert)
        req = request.Request(
            self.url,
            data=data,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            opener = self._opener if self._opener is not None else request.build_opener()
            with opener.open(req, timeout=self.timeout) as resp:
                return AlertDeliveryResult(
                    ok=True,
                    status="DELIVERED",
                    code=getattr(resp, "status", None),
                    channel="webhook:" + self.format,
                )
        except Exception as exc:  # noqa: BLE001 - 送达失败要如实记，不能抛
            return AlertDeliveryResult(
                ok=False,
                status="FAILED",
                channel="webhook:" + self.format,
                error=type(exc).__name__ + ": " + str(exc),
            )


class CompositeAlertChannel:
    """把告警扇出到多个通道；任一失败不影响其它通道，也不拖垮调用方。"""

    def __init__(self, channels) -> None:
        self.channels = list(channels)

    def deliver(self, alert: Mapping[str, Any]) -> list:
        return [channel.deliver(alert) for channel in self.channels]


def build_webhook_channel(url, *, format: str = "json", timeout: float = 15.0):
    """URL 未配置时返回 None（等于没有通道），保持默认安全姿态。"""
    if not url:
        return None
    return WebhookAlertChannel(url, format=format, timeout=timeout)
