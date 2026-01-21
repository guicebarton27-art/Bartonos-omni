from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class CommandResult:
    command: List[str]
    returncode: int
    duration_ms: float
    output: str


def detect_verification_commands(repo_root: Path) -> List[List[str]]:
    commands: List[List[str]] = []
    if (repo_root / "pyproject.toml").exists():
        commands.append(["pytest"])
    if (repo_root / "package.json").exists():
        commands.append(["npm", "test"])
    return commands


def run_commands(commands: List[List[str]], parallel: bool) -> List[CommandResult]:
    results: List[CommandResult] = []
    if parallel and len(commands) > 1:
        processes = []
        for command in commands:
            start = time.perf_counter()
            proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            processes.append((command, proc, start))
        for command, proc, start in processes:
            output, _ = proc.communicate()
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            results.append(CommandResult(command, proc.returncode, duration_ms, output))
        return results

    for command in commands:
        start = time.perf_counter()
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        output = (completed.stdout or "") + (completed.stderr or "")
        results.append(CommandResult(command, completed.returncode, duration_ms, output))
    return results
