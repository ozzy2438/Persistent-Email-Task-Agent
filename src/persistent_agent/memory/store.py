from __future__ import annotations

import json
import re
import sqlite3
import uuid
from pathlib import Path

from persistent_agent.models.schemas import TaskItem, TaskStatus


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


class MemoryStore:
    """SQLite store with separate semantic-memory and task-state tables."""

    def __init__(self, db_path: str | Path = ":memory:"):
        self.db = sqlite3.connect(str(db_path), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                metadata TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                deadline TEXT,
                status TEXT NOT NULL,
                notes TEXT NOT NULL
            );
            """
        )
        self.db.commit()

    def remember(self, text: str, metadata: dict | None = None) -> str:
        memory_id = str(uuid.uuid4())[:8]
        self.db.execute(
            "INSERT INTO memories VALUES (?, ?, ?)",
            (memory_id, text, json.dumps(metadata or {})),
        )
        self.db.commit()
        return memory_id

    def semantic_search(self, query: str, k: int = 3) -> list[str]:
        query_tokens = _tokens(query)
        rows = self.db.execute("SELECT text FROM memories").fetchall()
        ranked = sorted(
            ((len(query_tokens & _tokens(row["text"])), row["text"]) for row in rows),
            reverse=True,
        )
        return [text for score, text in ranked if score > 0][:k]

    def save_task(self, title: str, source: str, deadline: str | None = None) -> TaskItem:
        task = TaskItem(id=str(uuid.uuid4())[:8], title=title, source=source, deadline=deadline)
        self.db.execute(
            "INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?)",
            (task.id, task.title, task.source, task.deadline, task.status.value, "[]"),
        )
        self.db.commit()
        self.remember(
            f"Task: {task.title}. Source: {task.source}. Deadline: {task.deadline or 'none'}.",
            {"type": "task", "task_id": task.id},
        )
        return task

    def list_tasks(self, status: str = "open", keyword: str | None = None) -> list[TaskItem]:
        query = "SELECT * FROM tasks WHERE status = ?"
        parameters: list[str] = [status]
        if keyword:
            query += " AND lower(title) LIKE ?"
            parameters.append(f"%{keyword.lower()}%")
        rows = self.db.execute(query, parameters).fetchall()
        return [
            TaskItem(
                id=row["id"],
                title=row["title"],
                source=row["source"],
                deadline=row["deadline"],
                status=TaskStatus(row["status"]),
                notes=json.loads(row["notes"]),
            )
            for row in rows
        ]

    def close_task(self, task_id: str) -> None:
        self.db.execute("UPDATE tasks SET status = ? WHERE id = ?", (TaskStatus.DONE.value, task_id))
        self.db.commit()

