#!/usr/bin/env python3
"""로컬 미리보기 전용. 정적 파일 + /api/scan, /api/apply 목업.
주소에 old → 위험 신호 2개, typo → 접속 실패, busy → 429, 그 외 → 통과."""
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).parent


class Handler(SimpleHTTPRequestHandler):
    def _json(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/scan":
            return super().do_GET()
        url = parse_qs(parsed.query).get("url", [""])[0].lower()
        if "busy" in url:
            return self._json(429, {})
        if "typo" in url:
            return self._json(200, {"alive": False, "error": "unreachable"})
        if "old" in url:
            return self._json(200, {"alive": True, "notsecure": True, "php": "PHP 5.6", "eol": True})
        return self._json(200, {"alive": True, "notsecure": False, "php": "", "eol": False})

    def do_POST(self):
        if urlparse(self.path).path != "/api/apply":
            return self._json(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        if "fail" in body.get("company", ""):
            return self._json(400, {"error": "접수에 실패했어요. 잠시 후 다시 시도해 주세요."})
        return self._json(200, {"ok": True})


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 4600), partial(Handler, directory=str(ROOT))).serve_forever()
