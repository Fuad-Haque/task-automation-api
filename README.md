# Task Automation API

<div align="center">

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Sora&weight=700&size=22&duration=2800&pause=1000&color=6C63FF&center=true&vCenter=true&width=700&lines=Queue+Tasks.+Track+Progress.+Stay+Async.;Send+Reports+%C2%B7+Process+Data+%C2%B7+Sync+Integrations;FastAPI+%C2%B7+BackgroundTasks+%C2%B7+JWT+Auth;Built+for+developers+who+ship+fast.)](https://git.io/typing-svg)

</div>

<div align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)

</div>

---

## Overview

**Task Automation API** is a production-grade async background task processing service with JWT authentication. Register an account, submit long-running jobs — report generation, data processing, or integration syncs — and poll their progress in real time without blocking your client. Tasks move through a defined lifecycle (`queued → processing → complete / failed`) and every state transition is tracked. All task management routes are ownership-isolated: you can only see and cancel your own tasks.

**Live API** → [task-automation-api-i90w.onrender.com](https://task-automation-api-i90w.onrender.com)  
**Swagger Docs** → [task-automation-api-i90w.onrender.com/docs](https://task-automation-api-i90w.onrender.com/docs)

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Stack](#stack)
- [API Reference](#api-reference)
- [Auth Flow](#auth-flow)
- [Task Lifecycle](#task-lifecycle)
- [Task Types](#task-types)
- [Environment Variables](#environment-variables)
- [Quick Start](#quick-start)
- [Docker](#docker)
- [Project Structure](#project-structure)
- [Error Handling](#error-handling)
- [Author](#author)

---

## Features

| Feature | Detail |
|---------|--------|
| JWT Authentication | Secure register and login flow — all task routes are protected behind Bearer token auth |
| Async Background Tasks | Tasks are dispatched immediately and run in the background via FastAPI's `BackgroundTasks` — the POST endpoint returns instantly |
| Real-Time Progress Polling | Task progress tracked from 0 → 100 — poll `GET /tasks/{task_id}` at any interval to watch execution advance |
| Three Task Types | Report email dispatch, data processing pipelines, and external integration syncs — each with its own configurable payload |
| Task Filtering | List your tasks filtered by status (`queued`, `processing`, `complete`, `failed`) or type (`send-report`, `process-data`, `sync-integration`) |
| Task Cancellation | Cancel any queued task before it begins processing — running tasks cannot be interrupted mid-flight |
| Per-User Isolation | All task reads and mutations are scoped to the authenticated user — cross-user access is rejected at the service layer |
| Task Statistics | `GET /stats` returns aggregate counts per status and type for the authenticated user's task history |
| Health Endpoint | `/health` for uptime monitoring and deployment readiness checks |
| Swagger / OpenAPI Docs | Full interactive API documentation auto-generated at `/docs` |

---

## Architecture

```
Browser / API Client
    │
    └── HTTP (REST) ──────────── FastAPI (Render)
                                      │
                                 In-Memory Store ──── users_db  (credentials, JWT issuance)
                                      │
                                      └──────────────  tasks_db  (task state, progress, results)
                                           │
                                      BackgroundTasks ── Async task runners
                                                         (send-report / process-data / sync-integration)
```

### Task Submission Flow

```
POST /tasks/{task_type}  (Bearer token required)
    │
    ├── Validate JWT → resolve user_id
    ├── Validate task payload (Pydantic schema per task type)
    ├── Create task record → status: queued, progress: 0
    ├── Register async runner with FastAPI BackgroundTasks
    └── Return task_id immediately (non-blocking)
         │
         └── [Background] Runner executes → progress 0 → 100
                                          → status: complete or failed
```

### Poll Flow

```
GET /tasks/{task_id}  (Bearer token required)
    │
    ├── Lookup task_id in tasks_db
    ├── If not found → 404 Not Found
    ├── If task.user_id ≠ current user → 403 Forbidden
    └── Return current task state (status, progress, result, error)
```

---

## Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, asyncio |
| Authentication | JWT (python-jose), bcrypt password hashing (passlib) |
| Task Execution | FastAPI `BackgroundTasks` — async runners per task type |
| Storage | In-memory Python dicts (`users_db`, `tasks_db`) — stateless, resets on restart |
| Validation | Pydantic v2 |
| Deployment | Render |
| API Documentation | Swagger UI — auto-generated via FastAPI |

---

## API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/auth/register` | No | Create a new user account |
| `POST` | `/auth/token` | No | Login with credentials — returns JWT access token |
| `POST` | `/tasks/send-report` | Yes | Queue a report email task |
| `POST` | `/tasks/process-data` | Yes | Queue a data processing task |
| `POST` | `/tasks/sync-integration` | Yes | Queue an integration sync task |
| `GET` | `/tasks` | Yes | List your tasks — filterable by status and type |
| `GET` | `/tasks/{task_id}` | Yes | Retrieve a single task's current state and progress |
| `DELETE` | `/tasks/{task_id}` | Yes | Cancel a queued task |
| `GET` | `/stats` | Yes | Aggregate task statistics for the authenticated user |
| `GET` | `/health` | No | Health check — returns service status |

### Request / Response Examples

**Register**

```http
POST /auth/register
Content-Type: application/json

{
  "username": "fuad",
  "email": "fuad@example.com",
  "password": "secret123"
}
```

```json
{
  "id": "a1b2...",
  "username": "fuad",
  "email": "fuad@example.com",
  "created_at": "2025-05-01T10:00:00Z"
}
```

**Login**

```http
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=fuad&password=secret123
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Queue a report task**

```http
POST /tasks/send-report
Authorization: Bearer <token>
Content-Type: application/json

{
  "report_type": "sales",
  "recipient_email": "boss@company.com",
  "date_from": "2025-01-01",
  "date_to": "2025-03-31",
  "include_charts": true
}
```

```json
{
  "task_id": "c3d4...",
  "task_type": "send-report",
  "status": "queued",
  "progress": 0,
  "created_at": "2025-05-01T10:00:00Z"
}
```

**Poll task progress**

```http
GET /tasks/c3d4...
Authorization: Bearer <token>
```

```json
{
  "task_id": "c3d4...",
  "task_type": "send-report",
  "status": "processing",
  "progress": 62,
  "result": null,
  "error": null,
  "created_at": "2025-05-01T10:00:00Z",
  "updated_at": "2025-05-01T10:00:04Z"
}
```

**List tasks with filter**

```http
GET /tasks?status=complete&type=process-data
Authorization: Bearer <token>
```

```json
[
  {
    "task_id": "e5f6...",
    "task_type": "process-data",
    "status": "complete",
    "progress": 100,
    "created_at": "2025-05-01T09:00:00Z",
    "updated_at": "2025-05-01T09:00:07Z"
  }
]
```

**Get task statistics**

```http
GET /stats
Authorization: Bearer <token>
```

```json
{
  "total": 14,
  "by_status": {
    "queued": 1,
    "processing": 2,
    "complete": 10,
    "failed": 1
  },
  "by_type": {
    "send-report": 6,
    "process-data": 5,
    "sync-integration": 3
  }
}
```

---

## Auth Flow

JWT authentication is implemented using `python-jose` for token signing and `passlib[bcrypt]` for password hashing. Passwords are never stored in plaintext.

```
Registration → hash password (bcrypt) → store in users_db
Login        → verify password hash → issue signed JWT (HS256, 60-min expiry)
Protected routes → extract Bearer token → decode + validate → resolve user_id
```

All protected endpoints reject requests with expired, malformed, or missing tokens with `401 Unauthorized`. Task ownership is verified on every read and mutation — mismatched `user_id` returns `403 Forbidden`.

---

## Task Lifecycle

Tasks transition through the following states after submission:

```
queued → processing → complete
                    ↘ failed

queued → cancelled
```

| Status | Description |
|--------|-------------|
| `queued` | Task accepted — waiting for the background runner to pick it up |
| `processing` | Runner is actively executing — `progress` increments from 0 → 100 |
| `complete` | Execution finished successfully — `result` field is populated |
| `failed` | Execution encountered an error — `error` field contains the reason |
| `cancelled` | Task was cancelled via `DELETE /tasks/{task_id}` before processing began |

Poll `GET /tasks/{task_id}` at your preferred interval to track state transitions. Only `queued` tasks can be cancelled — tasks already in `processing` run to completion.

---

## Task Types

### `send-report`

Simulates generating and emailing a report for a specified date range.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `report_type` | string | Yes | Report category (e.g. `"sales"`, `"inventory"`, `"finance"`) |
| `recipient_email` | string | Yes | Destination email address |
| `date_from` | string (ISO date) | Yes | Report period start — `YYYY-MM-DD` |
| `date_to` | string (ISO date) | Yes | Report period end — `YYYY-MM-DD` |
| `include_charts` | boolean | No | Whether to attach chart visualizations (default: `false`) |

### `process-data`

Simulates running a data transformation or analysis pipeline.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `dataset_id` | string | Yes | Identifier of the dataset to process |
| `operations` | array[string] | Yes | Ordered list of operations to apply (e.g. `["normalize", "aggregate"]`) |
| `output_format` | string | No | Output format — `"json"`, `"csv"`, or `"parquet"` (default: `"json"`) |

### `sync-integration`

Simulates syncing data with an external third-party service.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `integration` | string | Yes | Target integration name (e.g. `"salesforce"`, `"hubspot"`, `"stripe"`) |
| `sync_direction` | string | Yes | `"pull"` (inbound) or `"push"` (outbound) |
| `entity_types` | array[string] | No | Entity types to sync — omit to sync all (e.g. `["contacts", "deals"]`) |

---

## Environment Variables

### Backend (`.env`)

```env
# JWT
SECRET_KEY=change-me-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

A fully documented `.env.example` file is included in the repository.

> **Note:** This service uses in-memory storage — no database connection string is required. All data resets on server restart. Persistent storage (PostgreSQL) is planned for a future version.

---

## Quick Start

```bash
git clone https://github.com/Fuad-Haque/task-automation-api
cd task-automation-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set a secure SECRET_KEY
uvicorn app.main:app --reload
```

API runs at `http://localhost:8000` — Swagger docs at `http://localhost:8000/docs`.

---

## Docker

```bash
git clone https://github.com/Fuad-Haque/task-automation-api
cd task-automation-api
cp .env.example .env
docker compose up -d
```

Services started:

| Service | Port | Notes |
|---------|------|-------|
| `api` | `8000` | FastAPI application — in-memory storage, no external DB required |

For a fully containerized local setup with auto-reload:

```bash
docker compose --profile full up --build
```

---

## Project Structure

```
task-automation-api/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application entry point — routes, CORS, lifespan hooks
│   ├── models.py        # Pydantic request/response schemas + TaskStatus enum definition
│   ├── auth.py          # Password hashing, JWT creation, token validation, get_current_user dependency
│   ├── storage.py       # In-memory stores — users_db and tasks_db (dict-based, resets on restart)
│   └── tasks.py         # Async background runners — send_report_task, process_data_task, sync_integration_task
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── Procfile
└── requirements.txt
```

---

## Error Handling

| Status Code | Scenario |
|-------------|----------|
| `200 OK` | Request processed successfully |
| `400 Bad Request` | Invalid payload, unsupported operation, or malformed request field |
| `401 Unauthorized` | Missing, expired, or malformed JWT token |
| `403 Forbidden` | Authenticated user attempting to read or cancel another user's task |
| `404 Not Found` | Task ID does not exist |
| `409 Conflict` | Username already registered |
| `422 Unprocessable Entity` | Request validation error (Pydantic) |
| `500 Internal Server Error` | Unhandled error during task runner execution |

---

## Author

Built by [Fuad Haque](https://fuadhaque.com)

[fuadhaque.dev@gmail.com](mailto:fuadhaque.dev@gmail.com) · [Book a Call](https://cal.com/fuad-haque) · [GitHub](https://github.com/Fuad-Haque)
