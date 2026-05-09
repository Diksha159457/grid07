from __future__ import annotations

import json
from pathlib import Path
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from grid07.combat_engine import CombatEngine
from grid07.content_engine import ContentEngine
from grid07.router import PersonaRouter

STATIC_DIR = Path(__file__).resolve().parent / "static"


class Grid07RequestHandler(BaseHTTPRequestHandler):
    router = PersonaRouter()
    content_engine = ContentEngine()
    combat_engine = CombatEngine()

    def _read_json(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        if not content_length:
            return {}
        body = self.rfile.read(content_length).decode("utf-8")
        return json.loads(body)

    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_file(self, filename: str, content_type: str, status: int = HTTPStatus.OK) -> None:
        file_path = STATIC_DIR / filename
        content = file_path.read_bytes()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", ""}:
            self._send_file("index.html", "text/html; charset=utf-8")
            return
        if self.path == "/app.css":
            self._send_file("app.css", "text/css; charset=utf-8")
            return
        if self.path == "/app.js":
            self._send_file("app.js", "application/javascript; charset=utf-8")
            return
        if self.path in {"/api", "/api/", "/info", "/info/"}:
            self._send_json(
                {
                    "service": "grid07-cognitive-combat",
                    "status": "ok",
                    "message": "Grid07 API is live.",
                    "endpoints": {
                        "health": "/health",
                        "route": "POST /route",
                        "generate_post": "POST /generate-post",
                        "reply": "POST /reply",
                    },
                }
            )
            return
        if self.path in {"/health", "/health/"}:
            self._send_json({"status": "ok"})
            return
        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        try:
            payload = self._read_json()
            if self.path == "/route":
                post = payload.get("post", "")
                matches = [match.__dict__ for match in self.router.route(post)]
                self._send_json({"matches": matches})
                return
            if self.path == "/generate-post":
                bot_id = payload.get("bot_id", "bot_a")
                self._send_json(self.content_engine.generate_post(bot_id))
                return
            if self.path == "/reply":
                bot_id = payload.get("bot_id", "bot_a")
                message = payload.get("message", "")
                self._send_json(self.combat_engine.generate_reply(bot_id, message))
                return
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
        except Exception as exc:  # pragma: no cover
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)


def serve(host: str = "127.0.0.1", port: int = 8080) -> None:
    server = ThreadingHTTPServer((host, port), Grid07RequestHandler)
    print(f"Grid07 API running on http://{host}:{port}")
    server.serve_forever()
