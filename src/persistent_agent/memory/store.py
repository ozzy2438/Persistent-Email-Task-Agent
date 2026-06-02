from __future__ import annotations

import json
import re
import sqlite3
import uuid
from pathlib import Path

from persistent_agent.models.schemas import EmailItem, TaskItem, TaskStatus


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
            CREATE TABLE IF NOT EXISTS emails (
                id TEXT PRIMARY KEY,
                sender TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                received_at TEXT,
                metadata TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                source_email_id TEXT,
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

    def save_email(
        self,
        sender: str,
        subject: str,
        body: str,
        received_at: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> EmailItem:
        email = EmailItem(
            id=str(uuid.uuid4())[:8],
            sender=sender,
            subject=subject,
            body=body,
            received_at=received_at,
            metadata=metadata or {},
        )
        self.db.execute(
            "INSERT INTO emails VALUES (?, ?, ?, ?, ?, ?)",
            (
                email.id,
                email.sender,
                email.subject,
                email.body,
                email.received_at,
                json.dumps(email.metadata),
            ),
        )
        self.db.commit()
        return email

    def get_email(self, email_id: str) -> EmailItem | None:
        row = self.db.execute("SELECT * FROM emails WHERE id = ?", (email_id,)).fetchone()
        return self._email_from_row(row) if row else None

    def list_emails(
        self,
        sender: str | None = None,
        subject_keyword: str | None = None,
        limit: int = 20,
    ) -> list[EmailItem]:
        query = "SELECT * FROM emails WHERE 1 = 1"
        parameters: list[str | int] = []
        if sender:
            query += " AND lower(sender) LIKE ?"
            parameters.append(f"%{sender.lower()}%")
        if subject_keyword:
            query += " AND lower(subject) LIKE ?"
            parameters.append(f"%{subject_keyword.lower()}%")
        query += " ORDER BY rowid DESC LIMIT ?"
        parameters.append(limit)
        rows = self.db.execute(query, parameters).fetchall()
        return [self._email_from_row(row) for row in rows]

    def search_email_text(self, query: str, k: int = 3) -> list[EmailItem]:
        query_tokens = _tokens(query)
        rows = self.db.execute("SELECT * FROM emails").fetchall()
        scored_rows = [
            (
                len(query_tokens & _tokens(f"{row['sender']} {row['subject']} {row['body']}")),
                index,
                row,
            )
            for index, row in enumerate(rows)
        ]
        ranked = sorted(scored_rows, key=lambda item: (item[0], -item[1]), reverse=True)
        return [self._email_from_row(row) for score, _, row in ranked if score > 0][:k]

    def save_task(
        self,
        title: str,
        source: str,
        deadline: str | None = None,
        source_email_id: str | None = None,
    ) -> TaskItem:
        task = TaskItem(
            id=str(uuid.uuid4())[:8],
            title=title,
            source=source,
            source_email_id=source_email_id,
            deadline=deadline,
        )
        self.db.execute(
            "INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                task.id,
                task.title,
                task.source,
                task.source_email_id,
                task.deadline,
                task.status.value,
                "[]",
            ),
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
                source_email_id=row["source_email_id"],
                deadline=row["deadline"],
                status=TaskStatus(row["status"]),
                notes=json.loads(row["notes"]),
            )
            for row in rows
        ]

    def close_task(self, task_id: str) -> None:
        self.db.execute("UPDATE tasks SET status = ? WHERE id = ?", (TaskStatus.DONE.value, task_id))
        self.db.commit()

    @staticmethod
    def _email_from_row(row: sqlite3.Row) -> EmailItem:
        return EmailItem(
            id=row["id"],
            sender=row["sender"],
            subject=row["subject"],
            body=row["body"],
            received_at=row["received_at"],
            metadata=json.loads(row["metadata"]),
        )
