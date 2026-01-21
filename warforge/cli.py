from __future__ import annotations

import json
import subprocess
import sys
from shutil import which
from pathlib import Path
from typing import Optional

import typer

from warforge.config import load_config, save_config
from warforge.core import RunContext, Task, ensure_dir, now_iso, write_json, build_repo_map
from warforge.orchestrator import Orchestrator
from warforge.policy import evaluate_policy
from warforge.receipts import render_receipt, write_receipt
from warforge.storage import add_task, get_task, pop_next_task
from warforge.verification import detect_verification_commands, run_commands

app = typer.Typer(add_completion=False)
queue_app = typer.Typer()
bot_app = typer.Typer()
agent_app = typer.Typer()
workflow_app = typer.Typer()

app.add_typer(queue_app, name="queue")
app.add_typer(bot_app, name="bot")
app.add_typer(agent_app, name="agent")
app.add_typer(workflow_app, name="workflow")

RUNS_DIR = Path("runs")


@app.command()
def doctor() -> None:
    """Verify environment and dependencies."""
    missing = []
    if sys.version_info < (3, 10):
        missing.append("python>=3.10")
    if which("git") is None:
        missing.append("git")
    if missing:
        typer.echo(f"Missing dependencies: {', '.join(missing)}")
        raise typer.Exit(code=1)
    typer.echo("Warforge Speed doctor: ok")


@app.command()
def ingest(repo: Optional[str] = None) -> None:
    """Create a repo index."""
    root = Path(repo) if repo else Path.cwd()
    stack = "unknown"
    if (root / "pyproject.toml").exists():
        stack = "python"
    if (root / "package.json").exists():
        stack = "node"
    repo_map = build_repo_map(root)
    commands = [" ".join(command) for command in detect_verification_commands(root)]
    index = {
        "repo_root": str(root),
        "indexed_at": now_iso(),
        "stack": stack,
        "verification_commands": commands,
    }
    write_json(Path(".warforge") / "repo_index.json", index)
    write_json(Path(".warforge") / "repo_map.json", repo_map)
    typer.echo("Repo ingested")


@queue_app.command("add")
def queue_add(task: str) -> None:
    """Add a task to the queue."""
    new_task = add_task(task, task)
    typer.echo(f"Queued {new_task.task_id}")


@app.command("run")
def run_task(
    task_id: str = typer.Argument("next"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Plan only, no verification commands."),
) -> None:
    """Run a task by id or run the next task in queue."""
    config = load_config()
    if task_id == "next":
        task = pop_next_task()
    else:
        task = get_task(task_id) if task_id else None
    if not task:
        typer.echo("No task found")
        raise typer.Exit(code=1)
    run_id = f"run-{task.task_id}"
    run_dir = RUNS_DIR / run_id
    ensure_dir(run_dir)
    write_json(run_dir / "task.json", {
        "task_id": task.task_id,
        "title": task.title,
        "description": task.description,
        "created_at": task.created_at,
    })

    context = RunContext(
        run_id=run_id,
        task=Task(task_id=task.task_id, title=task.title, description=task.description, created_at=task.created_at),
        repo_root=Path.cwd(),
        run_dir=run_dir,
        mode="fast" if config.fast_mode else "safe",
        safe_mode=config.safe_mode,
        fast_mode=config.fast_mode,
        dry_run=dry_run or config.dry_run,
    )
    orchestrator = Orchestrator(context)
    payload = orchestrator.run()
    orchestrator.write_artifacts(payload)

    verification_commands = detect_verification_commands(context.repo_root)
    test_results = []
    if context.dry_run:
        test_results = []
    else:
        test_results = run_commands(verification_commands, parallel=context.fast_mode)

    diff_paths = []
    diff_text = ""
    git_root = context.repo_root
    if (git_root / ".git").exists():
        diff_paths = (
            subprocess.run(["git", "diff", "--name-only"], capture_output=True, text=True, check=False)
            .stdout.strip()
            .splitlines()
        )
        diff_text = subprocess.run(["git", "diff"], capture_output=True, text=True, check=False).stdout
    policy = evaluate_policy([Path(path) for path in diff_paths], diff_text, context.safe_mode)
    payload["policy"] = {
        "restricted_zones": policy.restricted_zones,
        "requires_approval": policy.requires_approval,
    }
    write_json(run_dir / "risk_report.json", payload["policy"])

    if context.dry_run:
        test_summary = [f\"dry-run: {' '.join(command)}\" for command in verification_commands]
    else:
        test_summary = [f\"{' '.join(result.command)} => {result.returncode}\" for result in test_results]

    receipt = render_receipt(
        run_id=run_id,
        task_title=task.title,
        files_touched=[],
        commands=["warforge run"],
        tests=test_summary,
        test_outputs=[result.output for result in test_results] if test_results else [],
        evals=[payload["verification"]["eval_quality"]],
        risks=payload["policy"]["restricted_zones"],
    )
    write_receipt(run_dir, receipt)
    commands_log = ["warforge run"]
    for result in test_results:
        commands_log.append(f"$ {' '.join(result.command)}")
        commands_log.append(result.output)
    (run_dir / "commands.log").write_text("\n".join(commands_log))
    write_json(run_dir / "patch_summary.json", {"files": diff_paths})
    failed = any(result.returncode != 0 for result in test_results)
    write_json(
        run_dir / "test_report.json",
        {
            "commands": [" ".join(command) for command in verification_commands],
            "results": [
                {"command": " ".join(result.command), "returncode": result.returncode, "duration_ms": result.duration_ms}
                for result in test_results
            ],
            "status": "failed" if failed else "passed",
        },
    )

    if failed and not context.dry_run:
        typer.echo(f"Verification failed for run: {run_id}")
        raise typer.Exit(code=1)

    if payload["policy"]["requires_approval"] and not (run_dir / "approval.json").exists():
        write_json(
            run_dir / "approval_request.json",
            {
                "run_id": run_id,
                "restricted_zones": payload["policy"]["restricted_zones"],
                "status": "required",
                "message": "Approval required before proceeding with restricted changes.",
            },
        )
        typer.echo(f"Approval required for run: {run_id}")
        raise typer.Exit(code=2)

    typer.echo(f"Run complete: {run_id}")


@app.command()
def verify(repo: Optional[str] = None) -> None:
    """Run verification suite."""
    root = Path(repo) if repo else Path.cwd()
    commands = detect_verification_commands(root)
    if not commands:
        typer.echo("No verification commands detected")
        raise typer.Exit(code=1)
    results = run_commands(commands, parallel=False)
    for result in results:
        typer.echo(f"{' '.join(result.command)} => {result.returncode}")
    if any(result.returncode != 0 for result in results):
        raise typer.Exit(code=1)


@app.command()
def speed(state: str = typer.Argument(..., help="on|off")) -> None:
    """Toggle fast mode."""
    config = load_config()
    config.fast_mode = state == "on"
    save_config(config)
    typer.echo(f"Fast mode {'enabled' if config.fast_mode else 'disabled'}")


@app.command()
def safe(state: str = typer.Argument(..., help="on|off")) -> None:
    """Toggle safe mode."""
    config = load_config()
    config.safe_mode = state == "on"
    save_config(config)
    typer.echo(f"Safe mode {'enabled' if config.safe_mode else 'disabled'}")


@app.command("dry-run")
def dry_run(state: str = typer.Argument(..., help="on|off")) -> None:
    """Toggle dry-run mode."""
    config = load_config()
    config.dry_run = state == "on"
    save_config(config)
    typer.echo(f"Dry-run {'enabled' if config.dry_run else 'disabled'}")


@app.command()
def receipt(run_id: str) -> None:
    """Print receipt for run."""
    receipt_path = RUNS_DIR / run_id / "receipt.md"
    typer.echo(receipt_path.read_text())


@app.command()
def pr(run_id: str) -> None:
    """Generate PR info for run."""
    run_dir = RUNS_DIR / run_id
    summary = {
        "title": f"Warforge run {run_id}",
        "body": (run_dir / "receipt.md").read_text() if (run_dir / "receipt.md").exists() else "",
    }
    typer.echo(json.dumps(summary, indent=2))


@bot_app.command("new")
def bot_new(template: str) -> None:
    """Scaffold a bot template."""
    template_dir = Path("bots") / template
    ensure_dir(template_dir)
    (template_dir / "README.md").write_text(f"# {template} bot\n")
    typer.echo(f"Bot scaffolded: {template}")


@agent_app.command("new")
def agent_new(template: str) -> None:
    """Scaffold an agent template."""
    template_dir = Path("agents") / template
    ensure_dir(template_dir)
    (template_dir / "README.md").write_text(f"# {template} agent\n")
    typer.echo(f"Agent scaffolded: {template}")


@workflow_app.command("new")
def workflow_new(pattern: str) -> None:
    """Scaffold a workflow pattern."""
    template_dir = Path("workflows") / pattern
    ensure_dir(template_dir)
    (template_dir / "README.md").write_text(f"# {pattern} workflow\n")
    typer.echo(f"Workflow scaffolded: {pattern}")


@app.command("run-demo")
def run_demo() -> None:
    """Run a demo pipeline."""
    ingest()
    demo_task = add_task("demo", "demo pipeline run")
    run_task(task_id=demo_task.task_id)
