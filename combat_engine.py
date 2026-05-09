from __future__ import annotations

import json

from grid07.combat_engine import demo


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2))
