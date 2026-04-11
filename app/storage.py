from typing import Optional

# ── In-Memory Stores ───────────────────────────────────────────────────────────
users_db: dict[int, dict] = {}      # user_id → user dict
tasks_db: dict[str, dict] = {}      # task_id → task dict
_next_user_id: int = 1              # auto-increment counter


# ── User Helpers ───────────────────────────────────────────────────────────────
def _next_id() -> int:
    global _next_user_id
    uid = _next_user_id
    _next_user_id += 1
    return uid


def create_user(username: str, email: str, hashed_password: str) -> dict:
    user_id = _next_id()
    user = {
        "id": user_id,
        "username": username,
        "email": email,
        "hashed_password": hashed_password,
    }
    users_db[user_id] = user
    return user


def get_user_by_username(username: str) -> Optional[dict]:
    for user in users_db.values():
        if user["username"] == username:
            return user
    return None


def get_user_by_email(email: str) -> Optional[dict]:
    for user in users_db.values():
        if user["email"] == email:
            return user
    return None


# ── Task Helpers ───────────────────────────────────────────────────────────────
def get_tasks_by_owner(owner_id: int) -> list[dict]:
    return [task for task in tasks_db.values() if task["owner_id"] == owner_id]


def update_task(task_id: str, updates: dict) -> Optional[dict]:
    if task_id not in tasks_db:
        return None
    tasks_db[task_id].update(updates)
    return tasks_db[task_id]