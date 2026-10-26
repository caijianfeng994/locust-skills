#!/usr/bin/env python3
"""从 locust-skills-ui.yaml 读取点分键，例如 ops.gateway_base_url。缺失时打印空行。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_config() -> dict:
    path = Path(os.environ.get("LOCUST_SKILLS_UI_CONFIG", REPO_ROOT / "locust-skills-ui.yaml"))
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def lookup(data: dict, key: str) -> str:
    current: object = data
    for part in key.split("."):
        if not isinstance(current, dict) or part not in current:
            return ""
        current = current[part]
    if current is None:
        return ""
    return str(current)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: read_config_value.py <dotted.key>", file=sys.stderr)
        return 2
    print(lookup(load_config(), sys.argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
