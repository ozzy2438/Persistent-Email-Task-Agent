from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any


class ModelClient(ABC):
    @abstractmethod
    def generate(self, messages: list[dict[str, str]]) -> str:
        raise NotImplementedError

    def last_run_cost(self) -> float:
        return 0.0


class DemoModelClient(ModelClient):
    """Deterministic backend for a reproducible, API-key-free walkthrough."""

    def generate(self, messages: list[dict[str, str]]) -> str:
        transcript = "\n".join(message["content"] for message in messages)
        tool_results = [
            message["content"]
            for message in messages
            if message["content"].startswith("[tool_result:")
        ]
        keyword = "Acme" if "acme" in transcript.lower() else None

        if not tool_results:
            return self._tool_call(
                "list_open_tasks",
                {"keyword": keyword},
                "Check structured task state before answering.",
            )
        if len(tool_results) == 1:
            return self._tool_call(
                "search_memory",
                {"query": keyword or "open task"},
                "Retrieve the original context for the open task.",
            )

        task_id = self._extract_task_id(tool_results[0])
        return json.dumps(
            {
                "step_type": "final_answer",
                "final_answer": {
                    "response": (
                        "The Acme proposal is still open. It came from your manager on "
                        "Tuesday and is due Friday. I can help draft the reply next."
                    ),
                    "referenced_tasks": [task_id] if task_id else [],
                },
            }
        )

    @staticmethod
    def _tool_call(name: str, arguments: dict[str, Any], reasoning: str) -> str:
        return json.dumps(
            {
                "step_type": "tool_call",
                "tool_call": {
                    "tool_name": name,
                    "arguments": arguments,
                    "reasoning": reasoning,
                },
            }
        )

    @staticmethod
    def _extract_task_id(tool_result: str) -> str | None:
        match = re.search(r"\[tool_result:[^\]]+\]\s+\[([^\]]+)\]", tool_result)
        return match.group(1) if match else None


class OpenAIStyleClient(ModelClient):
    """Client for OpenAI and OpenAI-compatible endpoints such as vLLM."""

    def __init__(self, client: Any, model: str, price_in: float = 0.0, price_out: float = 0.0):
        self.client = client
        self.model = model
        self.price_in = price_in
        self.price_out = price_out
        self._cost = 0.0

    def generate(self, messages: list[dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        usage = response.usage
        self._cost += (
            usage.prompt_tokens * self.price_in + usage.completion_tokens * self.price_out
        ) / 1_000_000
        return response.choices[0].message.content

    def last_run_cost(self) -> float:
        return self._cost
