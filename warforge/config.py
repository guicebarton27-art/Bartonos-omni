from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


CONFIG_DIR = Path(".warforge")
CONFIG_PATH = CONFIG_DIR / "config.json"


@dataclass
class WarforgeConfig:
    fast_mode: bool = True
    safe_mode: bool = True
    dry_run: bool = False


def load_config() -> WarforgeConfig:
    if not CONFIG_PATH.exists():
        return WarforgeConfig()
    payload = json.loads(CONFIG_PATH.read_text())
    return WarforgeConfig(
        fast_mode=payload.get("fast_mode", True),
        safe_mode=payload.get("safe_mode", True),
        dry_run=payload.get("dry_run", False),
    )


def save_config(config: WarforgeConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(
            {
                "fast_mode": config.fast_mode,
                "safe_mode": config.safe_mode,
                "dry_run": config.dry_run,
            },
            indent=2,
        )
    )
