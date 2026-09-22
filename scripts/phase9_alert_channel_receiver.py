"""Phase9 本地告警通道接收器（E2E 验证用）。

真实外部告警端点（钉钉 / 企业微信 / 自建 webhook）需要操作者提供 URL；在拿到之前，
本接收器用一个本地 HTTP 端点扮演“真实通道后端”，证明 WebhookAlertChannel 的送达
链路端到端可用：Worker CRITICAL 告警 -> POST -> 本接收器落盘 evidence JSONL。

仅用于验证，不是生产告警通道；证据只落盘本地 .storyos，不写入凭据。

退出码：
    0 = 在超时前收到 expect-count 条请求
    2 = 超时仍未收到足够请求
"""

from __future__ import annotations

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


class AlertHandler(BaseHTTPRequestHandler):
    evidence_file: Path | None = None

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except ValueError:
            payload = {"raw": body.decode("utf-8", errors="replace")}
        record = {
            "path": self.path,
            "content_type": self.headers.get("Content-Type"),
            "payload": payload,
        }
        if self.evidence_file is not None:
            with self.evidence_file.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, default=str) + chr(10))
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def log_message(self, *args):
        return


def _count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Story OS V3 Phase9 本地告警通道接收器")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18080)
    parser.add_argument("--evidence-file", required=True)
    parser.add_argument("--expect-count", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=60.0)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)
    evidence = Path(args.evidence_file)
    evidence.parent.mkdir(parents=True, exist_ok=True)
    if evidence.exists():
        evidence.unlink()
    AlertHandler.evidence_file = evidence

    server = HTTPServer((args.host, args.port), AlertHandler)
    server.timeout = 0.2
    deadline = time.monotonic() + args.timeout
    try:
        while time.monotonic() < deadline:
            server.handle_request()
            if _count(evidence) >= args.expect_count:
                break
    finally:
        server.server_close()

    received = _count(evidence)
    print("received=" + str(received) + " expected=" + str(args.expect_count))
    return 0 if received >= args.expect_count else 2


if __name__ == "__main__":
    raise SystemExit(main())
