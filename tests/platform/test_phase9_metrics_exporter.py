"""Phase9 真实 Metrics 采集端点（P9.33）的离线回归测试。

不碰真实 Redis / MySQL，锁住 exposition 语义：
1. load_metrics_text 正常读取；
2. 文件缺失返回 metrics_file_missing；
3. 未配置返回 metrics_file_not_configured；
4. /metrics 与 /healthz 通过真实回环 socket 返回正确内容与 Content-Type。
"""

from __future__ import annotations

import json
import threading
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase9_metrics_exporter import (  # noqa: E402
    CONTENT_TYPE_METRICS,
    build_server,
    load_metrics_text,
)


def test_load_metrics_text_reads_file(tmp_path):
    metrics = tmp_path / "metrics.prom"
    metrics.write_text("# HELP up test\n# TYPE up gauge\nup 1\n", encoding="utf-8")
    text, error = load_metrics_text(metrics)
    assert error is None
    assert "up 1" in text


def test_load_metrics_text_missing(tmp_path):
    text, error = load_metrics_text(tmp_path / "nope.prom")
    assert text == ""
    assert error == "metrics_file_missing"


def test_load_metrics_text_none():
    text, error = load_metrics_text(None)
    assert text == ""
    assert error == "metrics_file_not_configured"


def test_http_serves_metrics_and_healthz(tmp_path):
    metrics = tmp_path / "metrics.prom"
    metrics.write_text(
        "# HELP storyos_runtime_worker_up 常驻 Worker 是否在本次 tick 正常运行\n"
        "# TYPE storyos_runtime_worker_up gauge\n"
        'storyos_runtime_worker_up{worker_id="w1"} 1\n',
        encoding="utf-8",
    )
    server = build_server(metrics, "127.0.0.1", 0)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(f"http://{host}:{port}/metrics", timeout=5) as resp:
            assert resp.status == 200
            assert resp.headers.get("Content-Type") == CONTENT_TYPE_METRICS
            body = resp.read().decode("utf-8")
            assert 'storyos_runtime_worker_up{worker_id="w1"} 1' in body

        with urlopen(f"http://{host}:{port}/healthz", timeout=5) as resp:
            assert resp.status == 200
            assert json.loads(resp.read()) == {"ok": True}

        with pytest.raises(HTTPError) as exc:
            urlopen(f"http://{host}:{port}/nope", timeout=5)
        assert exc.value.code == 404
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
