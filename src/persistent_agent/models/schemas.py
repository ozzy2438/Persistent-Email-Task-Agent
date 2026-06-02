from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ToolCall(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    reasoning: str


class FinalAnswer(BaseModel):
    response: str
    referenced_tasks: list[str] = Field(default_factory=list)


class AgentStep(BaseModel):
    step_type: Literal["tool_call", "final_answer"]
    tool_call: ToolCall | None = None
    final_answer: FinalAnswer | None = None

    @model_validator(mode="after")
    def validate_payload(self) -> AgentStep:
        if self.step_type == "tool_call" and self.tool_call is None:
            raise ValueError("tool_call is required when step_type=tool_call")
        if self.step_type == "final_answer" and self.final_answer is None:
            raise ValueError("final_answer is required when step_type=final_answer")
        return self


class TaskStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskItem(BaseModel):
    id: str
    title: str
    source: str
    deadline: str | None = None
    status: TaskStatus = TaskStatus.OPEN
    notes: list[str] = Field(default_factory=list)


class StepTrace(BaseModel):
    index: int
    raw_model_output: str
    parsed_step: AgentStep
    repair_attempts: int = 0
    tool_result: str | None = None
    latency_ms: float = 0.0


class AgentTrace(BaseModel):
    user_message: str
    steps: list[StepTrace] = Field(default_factory=list)
    final_response: str = ""
    total_latency_ms: float = 0.0
    cost_usd: float = 0.0

    @property
    def tool_calls(self) -> list[str]:
        return [
            step.parsed_step.tool_call.tool_name
            for step in self.steps
            if step.parsed_step.tool_call is not None
        ]

