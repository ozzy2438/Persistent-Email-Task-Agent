from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from pydantic import BaseModel

from persistent_agent.agent.bootstrap import build_agent


class ChatRequest(BaseModel):
    message: str


class EmailRequest(BaseModel):
    sender: str
    subject: str
    body: str
    task_title: str | None = None
    deadline: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = os.getenv("MEMORY_DB_PATH", "memory.db")
    app.state.agent = build_agent(db_path=db_path)
    yield


app = FastAPI(title="Persistent Email Task Agent", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tasks")
def tasks(request: Request) -> list[dict]:
    return [task.model_dump(mode="json") for task in request.app.state.agent.memory.list_tasks()]


@app.post("/emails")
def ingest_email(payload: EmailRequest, request: Request) -> dict:
    memory = request.app.state.agent.memory
    memory_id = memory.remember(
        f"Email from {payload.sender}. Subject: {payload.subject}. Body: {payload.body}",
        {"type": "email", "sender": payload.sender, "subject": payload.subject},
    )
    task = None
    if payload.task_title:
        task = memory.save_task(payload.task_title, payload.subject, payload.deadline)
    return {"memory_id": memory_id, "task": task.model_dump(mode="json") if task else None}


@app.post("/chat")
def chat(payload: ChatRequest, request: Request) -> dict:
    trace = request.app.state.agent.run(payload.message)
    return trace.model_dump(mode="json")

