# Task Automation API

FastAPI backend with async background task processing and JWT authentication.

## Project Structure

```
task-automation-api/
├── app/
│   ├── __init__.py
│   ├── models.py      # Pydantic models + TaskStatus enum
│   ├── auth.py        # JWT auth (hash, verify, create_token, get_current_user)
│   ├── storage.py     # In-memory users_db + tasks_db
│   ├── tasks.py       # Async background task runners
│   └── main.py        # FastAPI routes
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt

# Optional env vars (defaults shown)
export SECRET_KEY="change-me-in-production"
export ALGORITHM="HS256"
export ACCESS_TOKEN_EXPIRE_MINUTES=60
```

## Run

```bash
uvicorn app.main:app --reload
```

Interactive docs available at: http://localhost:8000/docs

## Endpoints

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/token` | Login → JWT |

### Tasks (all require Bearer token)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/tasks/send-report` | Queue a report email task |
| POST | `/tasks/process-data` | Queue a data processing task |
| POST | `/tasks/sync-integration` | Queue an integration sync task |
| GET | `/tasks` | List your tasks (filter by status/type) |
| GET | `/tasks/{task_id}` | Get a single task |
| DELETE | `/tasks/{task_id}` | Cancel a queued task |

### Other
| Method | Path | Description |
|--------|------|-------------|
| GET | `/stats` | Your task statistics |
| GET | `/health` | System health check |

## Quick Example

```bash
# 1. Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"fuad","email":"fuad@example.com","password":"secret123"}'

# 2. Login
curl -X POST http://localhost:8000/auth/token \
  -d "username=fuad&password=secret123"

# 3. Queue a task (use token from step 2)
curl -X POST http://localhost:8000/tasks/send-report \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "sales",
    "recipient_email": "boss@company.com",
    "date_from": "2025-01-01",
    "date_to": "2025-03-31",
    "include_charts": true
  }'

# 4. Poll for status
curl http://localhost:8000/tasks/<task_id> \
  -H "Authorization: Bearer <token>"
```

## Task Lifecycle

```
queued → processing → complete
                    ↘ failed
queued → cancelled
```

Tasks run in the background via FastAPI's `BackgroundTasks`. Progress updates
from 0 → 100 as the task executes. Poll `GET /tasks/{task_id}` to track progress.

## Deployment (Railway / Render)

```bash
# Procfile
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set `SECRET_KEY` as an environment variable in production.