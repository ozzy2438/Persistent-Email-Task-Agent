from __future__ import annotations

import json
import re
from dataclasses import dataclass

from pydantic import ValidationError

from persistent_agent.models.schemas import AgentStep, FinalAnswer


@dataclass
class ParseOutcome:
    step: AgentStep
    attempts: int
    raw: str


def _allowed_tool_names(messages: list[dict[str, str]]) -> set[str]:
    for message in messages:
        content = message.get("content", "")
        if message.get("role") == "system" and content.startswith("Available tools:\n"):
            return set(re.findall(r"^- ([a-zA-Z0-9_]+)\(", content, re.MULTILINE))
    return set()


def _known_task_ids(messages: list[dict[str, str]]) -> set[str]:
    task_ids: set[str] = set()
    for message in messages:
        if message.get("role") != "user":
            continue
        content = message.get("content", "")
        if content.startswith("[tool_result:list_open_tasks] "):
            task_ids.update(re.findall(r"\[([a-zA-Z0-9_-]+)\]", content.split("] ", 1)[-1]))
    return task_ids


def _validate_step_against_messages(step: AgentStep, messages: list[dict[str, str]]) -> None:
    if step.step_type == "tool_call":
        allowed_tool_names = _allowed_tool_names(messages)
        if allowed_tool_names and step.tool_call.tool_name not in allowed_tool_names:
            raise ValueError(f"Unknown tool: {step.tool_call.tool_name}")
        return

    known_task_ids = _known_task_ids(messages)
    if known_task_ids and any(
        task_id not in known_task_ids for task_id in step.final_answer.referenced_tasks
    ):
        raise ValueError("final_answer referenced unknown task ids")


def try_parse_step(raw: str, messages: list[dict[str, str]] | None = None) -> AgentStep | None:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```")
        cleaned = cleaned.removesuffix("```").strip()
    try:
        step = AgentStep.model_validate(json.loads(cleaned))
        if messages is not None:
            _validate_step_against_messages(step, messages)
        return step
    except (json.JSONDecodeError, ValidationError, ValueError):
        return None


def parse_with_repair(raw: str, model_client, messages: list[dict[str, str]]) -> ParseOutcome:
    step = try_parse_step(raw, messages)
    if step is not None:
        return ParseOutcome(step=step, attempts=0, raw=raw)

    retry_messages = messages + [
        {"role": "assistant", "content": raw},
        {
            "role": "user",
            "content": (
                "Your previous output was invalid. Return only valid JSON matching "
                "the AgentStep schema. Do not include markdown."
            ),
        },
    ]
    retry_raw = model_client.generate(retry_messages)
    step = try_parse_step(retry_raw, messages)
    if step is not None:
        return ParseOutcome(step=step, attempts=1, raw=retry_raw)

    fallback = AgentStep(
        step_type="final_answer",
        final_answer=FinalAnswer(
            response="I could not safely interpret the request. Please clarify the task."
        ),
    )
    return ParseOutcome(step=fallback, attempts=2, raw=retry_raw)
