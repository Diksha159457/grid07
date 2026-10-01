from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from grid07.combat_engine import CombatEngine
from grid07.content_engine import ContentEngine
from grid07.personas import PERSONAS
from grid07.router import PersonaRouter

STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_BODY_BYTES = 16_384
MAX_TEXT_CHARS = 4_000


class BadRequest(ValueError):
    pass


class Grid07RequestHandler(BaseHTTPRequestHandler):
    router = PersonaRouter()
    content_engine = ContentEngine()
    combat_engine = CombatEngine()

    def _read_json(self) -> dict:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise BadRequest("Invalid Content-Length") from exc
        if content_length > MAX_BODY_BYTES:
            raise BadRequest(f"Body exceeds {MAX_BODY_BYTES} bytes")
        if not content_length:
            return {}
        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BadRequest("Body must be valid JSON") from exc
        if not isinstance(payload, dict):
            raise BadRequest("Body must be a JSON object")
        return payload

    @staticmethod
    def _text_field(payload: dict, key: str) -> str:
        value = payload.get(key, "")
        if not isinstance(value, str) or not value.strip():
            raise BadRequest(f"Field '{key}' must be a non-empty string")
        if len(value) > MAX_TEXT_CHARS:
            raise BadRequest(f"Field '{key}' exceeds {MAX_TEXT_CHARS} characters")
        return value

    @staticmethod
    def _bot_id(payload: dict) -> str:
        bot_id = payload.get("bot_id", "bot_a")
        if bot_id not in PERSONAS:
            raise BadRequest(f"Unknown bot_id; expected one of {sorted(PERSONAS)}")
        return bot_id

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
                post = self._text_field(payload, "post")
                matches = [match.__dict__ for match in self.router.route(post)]
                self._send_json({"matches": matches})
                return
            if self.path == "/generate-post":
                bot_id = self._bot_id(payload)
                self._send_json(self.content_engine.generate_post(bot_id))
                return
            if self.path == "/reply":
                bot_id = self._bot_id(payload)
                message = self._text_field(payload, "message")
                self._send_json(self.combat_engine.generate_reply(bot_id, message))
                return
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
        except BadRequest as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception:  # pragma: no cover - never leak internals to clients
            self._send_json({"error": "Internal error"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        if self.server and getattr(self.server, "quiet", False):
            return
        super().log_message(format, *args)


def serve(host: str = "127.0.0.1", port: int = 8080) -> None:
    server = ThreadingHTTPServer((host, port), Grid07RequestHandler)
    print(f"Grid07 API running on http://{host}:{port}")
    server.serve_forever()
