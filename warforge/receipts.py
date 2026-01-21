from __future__ import annotations

from pathlib import Path
from typing import List

from warforge.core import write_text


def render_receipt(
    run_id: str,
    task_title: str,
    files_touched: List[str],
    commands: List[str],
    tests: List[str],
    test_outputs: List[str],
    evals: List[dict],
    risks: List[str],
) -> str:
    risk_text = "\n".join(f"- {risk}" for risk in risks) or "- None"
    command_text = "\n".join(f"- `{cmd}`" for cmd in commands) or "- None"
    test_text = "\n".join(f"- `{test}`" for test in tests) or "- None"
    output_text = "\n".join(f"```\n{output}\n```" for output in test_outputs) or "```\nNone\n```"
    eval_text = "\n".join(f"- {item}" for item in evals) or "- None"
    files_text = "\n".join(f"- {file}" for file in files_touched) or "- None"
    return (
        f"# Warforge Speed Receipt ({run_id})\n\n"
        f"## Task\n- {task_title}\n\n"
        "## What Changed\n- Orchestrator run executed with multi-agent pipeline.\n\n"
        "## Why It Changed\n- To fulfill the requested task with a gated plan, verification, and receipt.\n\n"
        f"## Files Touched\n{files_text}\n\n"
        f"## Commands\n{command_text}\n\n"
        f"## Tests\n{test_text}\n\n"
        f"## Test Outputs\n{output_text}\n\n"
        f"## Evals\n{eval_text}\n\n"
        f"## Risks + Mitigations\n{risk_text}\n\n"
        "## Rollback\n- Revert the git commit for this run.\n\n"
        "## Not Done\n- Deployment not performed.\n"
    )


def write_receipt(run_dir: Path, receipt: str) -> None:
    write_text(run_dir / "receipt.md", receipt)
