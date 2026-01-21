# Warforge Speed

Warforge Speed is a production-grade AI coder and multi-agent orchestration engine designed for ultra-fast, reliable iteration. It ships PRs end-to-end with receipts, policy gating, and agent-level artifacts.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
warforge doctor
warforge ingest
warforge queue add "Ship a demo run"
warforge run next
```

## Architecture

- **CLI (Typer)**: `warforge/cli.py` exposes all required commands.
- **Orchestrator**: `warforge/orchestrator.py` coordinates real agents with gated stages and artifacts.
- **Policy Engine**: `warforge/policy.py` enforces restricted-zone detection and safe mode.
- **Receipts**: `warforge/receipts.py` writes run receipts to `runs/<run-id>`.
- **API**: `warforge/api.py` provides task CRUD.

## API Endpoints

- `POST /tasks` (create task)
- `GET /tasks/{task_id}` (fetch task)
- `POST /approvals` (policy approvals)
- `GET /runs/{run_id}/artifacts` (list artifacts)
- `GET /runs/{run_id}/receipt` (fetch receipt)

## Demo

```bash
warforge run-demo
warforge receipt run-task-<id>
```

Or use the Makefile:

```bash
make doctor
make test
make run-demo
```

## Safety

Safe mode is enabled by default. Restricted zones are detected and recorded in `risk_report.json`.
If a run touches restricted zones, create `runs/<run-id>/approval.json` to acknowledge approvals.
An `approval_request.json` will be generated when approval is required.
Use `warforge dry-run on` to plan without executing verification commands.

## Fast Mode

Fast mode enables parallel agent execution and cached repo indexing. Toggle with:

```bash
warforge speed on
```

## CLI Commands

- `warforge doctor`
- `warforge ingest <repo-path>`
- `warforge queue add "<task>"`
- `warforge run next`
- `warforge run <task-id>`
- `warforge verify <repo-path>`
- `warforge speed on|off`
- `warforge safe on|off`
- `warforge dry-run on|off`
- `warforge receipt <run-id>`
- `warforge pr <run-id>`
- `warforge bot new <template>`
- `warforge agent new <template>`
- `warforge workflow new <pattern>`

## Run Artifacts

Each run writes artifacts to `runs/<run-id>/`:

- `task.json`
- `repo_map.json`
- `plan.json`
- `workflow.json`
- `risk_report.json`
- `patch_summary.json`
- `commands.log`
- `test_report.json`
- `eval_report.json`
- `review_report.json`
- `receipt.md`
- `metrics.json`

## Troubleshooting

- Ensure `python>=3.10` is installed.
- Delete `.warforge/` if you need to reset local state.
