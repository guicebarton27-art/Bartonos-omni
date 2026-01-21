from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from pathlib import Path

from warforge.storage import add_task, get_task

app = FastAPI(title="Warforge Speed API")


class TaskRequest(BaseModel):
    title: str
    description: str


@app.post("/tasks")
def create_task(request: TaskRequest):
    task = add_task(request.title, request.description)
    return {"task_id": task.task_id}


@app.get("/tasks/{task_id}")
def fetch_task(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task.task_id, "title": task.title, "description": task.description}


class ApprovalRequest(BaseModel):
    run_id: str
    approved_by: str
    reason: str


@app.post("/approvals")
def create_approval(request: ApprovalRequest):
    return {"status": "recorded", "run_id": request.run_id, "approved_by": request.approved_by}


@app.get("/runs/{run_id}/artifacts")
def list_artifacts(run_id: str):
    run_dir = Path("runs") / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")
    return {"artifacts": [path.name for path in run_dir.iterdir() if path.is_file()]}


@app.get("/runs/{run_id}/receipt")
def get_receipt(run_id: str):
    run_dir = Path("runs") / run_id
    receipt_path = run_dir / "receipt.md"
    if not receipt_path.exists():
        raise HTTPException(status_code=404, detail="Receipt not found")
    return {"receipt": receipt_path.read_text()}
