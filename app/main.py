from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

import app.storage as storage
from app.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.models import (
    ProcessDataRequest,
    SendReportRequest,
    SyncIntegrationRequest,
    TaskResponse,
    TaskStats,
)
from app.tasks import run_process_data, run_send_report, run_sync_integration

app = FastAPI(
    title="Task Automation API",
    description="Async background task runner with JWT auth.",
    version="1.0.0",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _task_to_response(task: dict) -> TaskResponse:
    return TaskResponse(**task)


# ── Auth ───────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    if storage.get_user_by_username(body.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    if storage.get_user_by_email(body.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = storage.create_user(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    return {"id": user["id"], "username": user["username"], "email": user["email"]}


@app.post("/auth/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = storage.get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}


# ── Task Creation Helpers ──────────────────────────────────────────────────────

def _create_task(task_type: str, estimated_seconds: int, params: dict, owner_id: int) -> dict:
    task_id = str(uuid4())[:12]
    task = {
        "task_id": task_id,
        "task_type": task_type,
        "status": "queued",
        "owner_id": owner_id,
        "created_at": _now(),
        "started_at": None,
        "completed_at": None,
        "estimated_seconds": estimated_seconds,
        "progress": 0,
        "result": None,
        "error": None,
        "params": params,
    }
    storage.tasks_db[task_id] = task
    return task


# ── Task Endpoints ─────────────────────────────────────────────────────────────

@app.post("/tasks/send-report", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_report(
    request: SendReportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    task = _create_task(
        task_type="send_report",
        estimated_seconds=8,
        params=request.model_dump(),
        owner_id=current_user["id"],
    )
    background_tasks.add_task(run_send_report, task["task_id"], request.model_dump())
    return _task_to_response(task)


@app.post("/tasks/process-data", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def process_data(
    request: ProcessDataRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    task = _create_task(
        task_type="process_data",
        estimated_seconds=4,
        params=request.model_dump(),
        owner_id=current_user["id"],
    )
    background_tasks.add_task(run_process_data, task["task_id"], request.model_dump())
    return _task_to_response(task)


@app.post("/tasks/sync-integration", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def sync_integration(
    request: SyncIntegrationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    task = _create_task(
        task_type="sync_integration",
        estimated_seconds=10,
        params=request.model_dump(),
        owner_id=current_user["id"],
    )
    background_tasks.add_task(run_sync_integration, task["task_id"], request.model_dump())
    return _task_to_response(task)


# ── Task Retrieval ─────────────────────────────────────────────────────────────

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, current_user: dict = Depends(get_current_user)):
    task = storage.tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["owner_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return _task_to_response(task)


@app.get("/tasks", response_model=list[TaskResponse])
async def list_tasks(
    task_status: Optional[str] = Query(None, alias="status"),
    task_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    tasks = storage.get_tasks_by_owner(current_user["id"])

    if task_status:
        tasks = [t for t in tasks if t["status"] == task_status]
    if task_type:
        tasks = [t for t in tasks if t["task_type"] == task_type]

    tasks.sort(key=lambda t: t["created_at"], reverse=True)
    return [_task_to_response(t) for t in tasks[skip: skip + limit]]


# ── Task Cancellation ──────────────────────────────────────────────────────────

@app.delete("/tasks/{task_id}")
async def cancel_task(task_id: str, current_user: dict = Depends(get_current_user)):
    task = storage.tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["owner_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    if task["status"] in ("complete", "failed"):
        raise HTTPException(status_code=400, detail="Cannot cancel a finished task")
    if task["status"] == "processing":
        raise HTTPException(status_code=400, detail="Cannot cancel a running task")

    storage.update_task(task_id, {"status": "cancelled", "completed_at": _now()})
    return {"cancelled": True, "task_id": task_id}


# ── Stats ──────────────────────────────────────────────────────────────────────

@app.get("/stats", response_model=TaskStats)
async def get_stats(current_user: dict = Depends(get_current_user)):
    tasks = storage.get_tasks_by_owner(current_user["id"])

    by_status: dict[str, int] = {}
    by_type: dict[str, int] = {}
    completion_seconds: list[float] = []

    for t in tasks:
        by_status[t["status"]] = by_status.get(t["status"], 0) + 1
        by_type[t["task_type"]] = by_type.get(t["task_type"], 0) + 1

        if t["status"] == "complete" and t["started_at"] and t["completed_at"]:
            start = datetime.fromisoformat(t["started_at"])
            end = datetime.fromisoformat(t["completed_at"])
            completion_seconds.append((end - start).total_seconds())

    complete_count = by_status.get("complete", 0)
    failed_count = by_status.get("failed", 0)
    finished = complete_count + failed_count
    success_rate = (complete_count / finished * 100) if finished > 0 else 0.0
    avg_seconds = (sum(completion_seconds) / len(completion_seconds)) if completion_seconds else 0.0

    recent = sorted(tasks, key=lambda t: t["created_at"], reverse=True)[:5]

    return TaskStats(
        total_tasks=len(tasks),
        by_status=by_status,
        by_type=by_type,
        success_rate=round(success_rate, 2),
        avg_completion_seconds=round(avg_seconds, 2),
        recent_tasks=recent,
    )


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    active_statuses = {"processing", "queued"}
    active_count = sum(
        1 for t in storage.tasks_db.values() if t["status"] in active_statuses
    )
    return {
        "status": "ok",
        "timestamp": _now(),
        "total_tasks_in_system": len(storage.tasks_db),
        "active_tasks": active_count,
    }