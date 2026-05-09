from __future__ import annotations

import argparse
import json
import os

from grid07.api import serve
from grid07.combat_engine import CombatEngine, demo as combat_demo
from grid07.content_engine import ContentEngine, demo as content_demo
from grid07.router import PersonaRouter, demo as router_demo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Grid07 cognitive combat platform")
    subparsers = parser.add_subparsers(dest="command", required=True)

    route_parser = subparsers.add_parser("route", help="Route a post to matching personas")
    route_parser.add_argument("--post", required=True)

    post_parser = subparsers.add_parser("post", help="Generate a post for a bot")
    post_parser.add_argument("--bot", default="bot_a")

    reply_parser = subparsers.add_parser("reply", help="Generate a defended reply")
    reply_parser.add_argument("--bot", default="bot_a")
    reply_parser.add_argument("--message", required=True)

    serve_parser = subparsers.add_parser("serve", help="Run the local HTTP API")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=None)

    subparsers.add_parser("demo", help="Run all demos")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "route":
        router = PersonaRouter()
        print(json.dumps([match.__dict__ for match in router.route(args.post)], indent=2))
        return

    if args.command == "post":
        engine = ContentEngine()
        print(json.dumps(engine.generate_post(args.bot), indent=2))
        return

    if args.command == "reply":
        engine = CombatEngine()
        print(json.dumps(engine.generate_reply(args.bot, args.message), indent=2))
        return

    if args.command == "serve":
        port = args.port if args.port is not None else int(os.getenv("PORT", "8080"))
        serve(args.host, port)
        return

    if args.command == "demo":
        snapshot = {
            "router": {
                post: [match.__dict__ for match in matches]
                for post, matches in router_demo()
            },
            "content": content_demo(),
            "combat": combat_demo(),
        }
        print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
