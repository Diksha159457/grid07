from __future__ import annotations

import json

from grid07.router import demo


if __name__ == "__main__":
    print(json.dumps({post: [match.__dict__ for match in matches] for post, matches in demo()}, indent=2))
