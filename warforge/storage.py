from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Optional

from warforge.core import Task, ensure_dir, now_iso


DB_PATH = Path(".warforge") / "warforge.db"
QUEUE_DIR = Path(".warforge") / "queue"


def init_db() -> None:
    ensure_dir(DB_PATH.parent)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def add_task(title: str, description: str) -> Task:
    init_db()
    task_id = f"task-{int(time.time_ns())}"
    task = Task(task_id=task_id, title=title, description=description, created_at=now_iso())
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO tasks (task_id, title, description, created_at) VALUES (?, ?, ?, ?)",
            (task.task_id, task.title, task.description, task.created_at),
        )
        conn.commit()
    ensure_dir(QUEUE_DIR)
    queue_path = QUEUE_DIR / f"{task.task_id}.json"
    queue_path.write_text(json.dumps(asdict(task), indent=2))
    return task


def list_queue() -> Iterable[Path]:
    ensure_dir(QUEUE_DIR)
    return sorted(QUEUE_DIR.glob("*.json"))


def pop_next_task() -> Optional[Task]:
    queue = list_queue()
    if not queue:
        return None
    task_path = queue[0]
    payload = json.loads(task_path.read_text())
    task_path.unlink()
    return Task(**payload)


def get_task(task_id: str) -> Optional[Task]:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT task_id, title, description, created_at FROM tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
    if not row:
        return None
    return Task(*row)
