from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable


@dataclass(frozen=True)
class Task:
    task_id: str
    title: str
    description: str
    created_at: str


@dataclass
class RunContext:
    run_id: str
    task: Task
    repo_root: Path
    run_dir: Path
    mode: str
    safe_mode: bool
    fast_mode: bool
    dry_run: bool


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content)


def hash_files(paths: Iterable[Path]) -> str:
    hasher = hashlib.sha256()
    for path in sorted(paths):
        if path.is_file():
            hasher.update(path.read_bytes())
    return hasher.hexdigest()


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def clock_ms() -> float:
    return time.perf_counter() * 1000


def human_duration_ms(start_ms: float, end_ms: float) -> float:
    return round(end_ms - start_ms, 2)


def repo_files(repo_root: Path) -> Iterable[Path]:
    for root, _, files in os.walk(repo_root):
        if "/.git/" in root:
            continue
        for file in files:
            yield Path(root) / file


def build_repo_map(repo_root: Path) -> Dict[str, Any]:
    files = [str(path.relative_to(repo_root)) for path in repo_files(repo_root)]
    entry_points = [path for path in files if path.endswith(("pyproject.toml", "package.json", "README.md"))]
    workflows = [path for path in files if path.startswith(".github/workflows/")]
    return {
        "repo_root": str(repo_root),
        "files": files[:200],
        "entry_points": entry_points,
        "workflows": workflows,
    }
