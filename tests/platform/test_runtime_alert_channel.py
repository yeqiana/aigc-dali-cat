"""Runtime Alert Channel（P9.32）的离线回归测试。

不碰真实网络 / HTTP 服务，锁住通道语义：
1. dingtalk 包装正确；
2. json 格式透传原始告警；
3. transport 成功 -> DELIVERED + code；
4. transport 失败 -> FAILED + error（不抛）；
5. 空 URL -> ValueError；
6. 非法格式 -> ValueError；
7. build_webhook_channel 空 URL 返回 None；
8. CompositeAlertChannel 扇出且互不拖累。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from platform.operations.runtime_alert_channel import (  # noqa: E402
    CompositeAlertChannel,
    WebhookAlertChannel,
    build_webhook_channel,
    format_dingtalk,
)


class _FakeResp:
    def __init__(self, status=200):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _FakeOpener:
    def __init__(self, *, status=200, exc=None):
        self.status = status
        self.exc = exc
        self.requests = []

    def open(self, req, timeout=None):
        self.requests.append(req)
        if self.exc:
            raise self.exc
        return _FakeResp(self.status)


def _alert():
    return {
        "worker_id": "w1",
        "runtime": "V3_RUNTIME",
        "level": "CRITICAL",
        "reason": "mysql_unreachable",
        "timestamp": "2026-09-10T16:00:00",
        "detail": {"error": "refused"},
    }


def test_format_dingtalk_wraps_alert():
    body = format_dingtalk(_alert())
    assert body["msgtype"] == "markdown"
    text = body["markdown"]["text"]
    assert "CRITICAL" in text
    assert "mysql_unreachable" in text
    assert "w1" in text


def test_json_format_posts_raw_alert():
    opener = _FakeOpener(status=200)
    channel = WebhookAlertChannel("http://127.0.0.1:1/alert", opener=opener)
    result = channel.deliver(_alert())
    assert result.ok is True
    assert result.status == "DELIVERED"
    assert result.code == 200
    sent = json.loads(opener.requests[0].data.decode("utf-8"))
    assert sent["reason"] == "mysql_unreachable"


def test_delivery_failure_is_captured_not_raised():
    opener = _FakeOpener(exc=TimeoutError("slow"))
    channel = WebhookAlertChannel("http://127.0.0.1:1/alert", opener=opener)
    result = channel.deliver(_alert())
    assert result.ok is False
    assert result.status == "FAILED"
    assert "TimeoutError" in (result.error or "")


def test_empty_url_is_rejected():
    with pytest.raises(ValueError):
        WebhookAlertChannel("")


def test_unsupported_format_is_rejected():
    with pytest.raises(ValueError):
        WebhookAlertChannel("http://x", format="sms")


def test_build_webhook_channel_returns_none_without_url():
    assert build_webhook_channel(None) is None
    assert build_webhook_channel("") is None
    assert build_webhook_channel("http://x") is not None


def test_composite_fans_out_without_cross_failure():
    ok = WebhookAlertChannel("http://a", opener=_FakeOpener(status=200))
    bad = WebhookAlertChannel("http://b", opener=_FakeOpener(exc=TimeoutError("x")))
    results = CompositeAlertChannel([ok, bad]).deliver(_alert())
    assert [item.ok for item in results] == [True, False]
