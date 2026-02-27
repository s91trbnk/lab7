from __future__ import annotations

import json
import os
import sys
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from calculator import CalculatorError, evaluate


ROOT = Path(__file__).resolve().parent
HTML_PATH = ROOT / "calculator.html"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Handler(BaseHTTPRequestHandler):
    def end_headers(self) -> None:
        if self.path.startswith("/api/"):
            origin = self.headers.get("Origin")
            self.send_header("Access-Control-Allow-Origin", origin or "*")
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def _send_json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_text(self, status: int, text: str, content_type: str) -> None:
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
        if self.path in {"/", "/calculator.html"}:
            if not HTML_PATH.exists():
                self._send_text(
                    HTTPStatus.NOT_FOUND,
                    "Missing calculator.html next to web_calculator.py",
                    "text/plain",
                )
                return
            self._send_text(HTTPStatus.OK, _read_text(HTML_PATH), "text/html")
            return

        if self.path == "/api/health":
            self._send_json(HTTPStatus.OK, {"ok": True})
            return

        self._send_text(HTTPStatus.NOT_FOUND, "Not found", "text/plain")

    def do_OPTIONS(self) -> None:  # noqa: N802 (stdlib naming)
        if not self.path.startswith("/api/"):
            self._send_text(HTTPStatus.NOT_FOUND, "Not found", "text/plain")
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802 (stdlib naming)
        if self.path != "/api/eval":
            self._send_text(HTTPStatus.NOT_FOUND, "Not found", "text/plain")
            return

        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length > 0 else b""

        content_type = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        expr: str | None = None

        if content_type == "application/json":
            try:
                obj = json.loads(raw.decode("utf-8") if raw else "{}")
            except json.JSONDecodeError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "Bad JSON"})
                return
            if isinstance(obj, dict):
                value = obj.get("expr")
                if isinstance(value, str):
                    expr = value
        elif content_type == "application/x-www-form-urlencoded":
            parsed = urllib.parse.parse_qs(raw.decode("utf-8"), keep_blank_values=True)
            value = parsed.get("expr", [None])[0]
            if isinstance(value, str):
                expr = value

        if expr is None:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "error": "Missing 'expr'"},
            )
            return

        try:
            result = evaluate(expr)
        except CalculatorError as e:
            self._send_json(HTTPStatus.OK, {"ok": False, "error": str(e)})
            return
        except Exception:
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": "Server error"})
            return

        self._send_json(HTTPStatus.OK, {"ok": True, "result": result})

    def log_message(self, fmt: str, *args: object) -> None:
        if os.environ.get("CALC_WEB_QUIET") == "1":
            return
        super().log_message(fmt, *args)


def main(argv: list[str]) -> int:
    host = "127.0.0.1"
    port = 8000
    if len(argv) >= 2:
        try:
            port = int(argv[1])
        except ValueError:
            print("Usage: python web_calculator.py [port]", file=sys.stderr)
            return 2

    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"Open http://{host}:{port}/ in your browser")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping...")
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

