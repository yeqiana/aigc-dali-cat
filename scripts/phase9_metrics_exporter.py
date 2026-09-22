"""Phase9 真实 Metrics 采集端点（P9.33）。

Worker / Watchdog 已把 Prometheus textfile 原子落盘，但没有可被采集的 HTTP 端点，
采集管线仍断在“只落盘”这一步。本文件补一个标准库 HTTP sidecar，把最新 metrics 文件
以 Prometheus exposition 格式暴露在 /metrics，任何 Prometheus 都能拉取。

端点：
    GET /metrics  -> 200, text/plain; version=0.0.4; charset=utf-8（最新 metrics 文件内容）
    GET /healthz  -> 200, application/json {"ok":true}
    其它路径       -> 404, application/json {"ok":false,"error":"not found"}

明确不做的事：
    - 不安装 / 不假设 Prometheus、Grafana、node_exporter：只做 exposition 侧。
    - 不写凭据；只读指定的 metrics 文件。
    - 不注册系统服务 / 计划任务。

退出码：
    0 = 正常收到中断后优雅退出
    3 = 参数错误或端口绑定失败
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


CONTENT_TYPE_METRICS = "text/plain; version=0.0.4; charset=utf-8"


def load_metrics_text(metrics_file) -> tuple[str, str | None]:
    """读取最新 metrics 文件；文件缺失 / 不可读时返回错误文本（不抛）。"""
    if metrics_file is None:
        return "", "metrics_file_not_configured"
    try:
        return Path(metrics_file).read_text(encoding="utf-8"), None
    except FileNotFoundError:
        return "", "metrics_file_missing"
    except OSError as exc:
        return "", "metrics_file_unreadable: " + type(exc).__name__


class MetricsHandler(BaseHTTPRequestHandler):
    metrics_file: Path | None = None

    def do_GET(self):
        if self.path == "/healthz":
            self._write_json(200, {"ok": True})
            return
        if self.path == "/metrics":
            self._write_metrics()
            return
        self._write_json(404, {"ok": False, "error": "not found"})

    def _write_json(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _write_metrics(self):
        text, error = load_metrics_text(self.metrics_file)
        if error is not None:
            self._write_json(503, {"ok": False, "error": error})
            return
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", CONTENT_TYPE_METRICS)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        return


def build_server(metrics_file, host="127.0.0.1", port=18081):
    MetricsHandler.metrics_file = Path(metrics_file) if metrics_file else None
    return ThreadingHTTPServer((host, port), MetricsHandler)


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Story OS V3 Phase9 真实 Metrics 采集端点")
    parser.add_argument("--metrics-file", required=True, help="要暴露的 Prometheus textfile 路径")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18081)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)
    try:
        server = build_server(args.metrics_file, args.host, args.port)
    except OSError as exc:
        print("启动失败：" + type(exc).__name__ + ": " + str(exc))
        return 3

    host, port = server.server_address
    print("Story OS V3 Phase9 Metrics 采集端点")
    print("  metrics_file=" + str(args.metrics_file))
    print("  endpoint=http://" + host + ":" + str(port) + "/metrics")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
