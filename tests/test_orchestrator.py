from pathlib import Path

from warforge.core import RunContext, Task
from warforge.orchestrator import Orchestrator


def test_orchestrator_runs(tmp_path: Path):
    task = Task(task_id="task-1", title="demo", description="run", created_at="now")
    context = RunContext(
        run_id="run-task-1",
        task=task,
        repo_root=Path.cwd(),
        run_dir=tmp_path,
        mode="fast",
        safe_mode=True,
        fast_mode=True,
        dry_run=True,
    )
    orchestrator = Orchestrator(context)
    payload = orchestrator.run()
    assert "plan" in payload
    assert "verification" in payload
    assert "repo_map" in payload["plan"]["repo_analyst"]
    assert "restricted_zones" in payload["plan"]["repo_analyst"]
