from __future__ import annotations

import json
from dataclasses import dataclass

from pydantic import ValidationError

from persistent_agent.models.schemas import AgentStep, FinalAnswer


@dataclass
class ParseOutcome:
    step: AgentStep
    attempts: int
    raw: str


def try_parse_step(raw: str) -> AgentStep | None:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```")
        cleaned = cleaned.removesuffix("```").strip()
    try:
        return AgentStep.model_validate(json.loads(cleaned))
    except (json.JSONDecodeError, ValidationError, ValueError):
        return None


def parse_with_repair(raw: str, model_client, messages: list[dict[str, str]]) -> ParseOutcome:
    step = try_parse_step(raw)
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
    step = try_parse_step(retry_raw)
    if step is not None:
        return ParseOutcome(step=step, attempts=1, raw=retry_raw)

    fallback = AgentStep(
        step_type="final_answer",
        final_answer=FinalAnswer(
            response="I could not safely interpret the request. Please clarify the task."
        ),
    )
    return ParseOutcome(step=fallback, attempts=2, raw=retry_raw)

