from __future__ import annotations

import time

from persistent_agent.models.repair import parse_with_repair
from persistent_agent.models.schemas import AgentTrace, StepTrace


class Agent:
    def __init__(self, model_client, tools, memory, system_prompt: str, max_steps: int = 6):
        self.model = model_client
        self.tools = tools
        self.memory = memory
        self.system_prompt = system_prompt
        self.max_steps = max_steps

    def _build_messages(self, user_message: str, trace: AgentTrace) -> list[dict[str, str]]:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": self.tools.catalog_text()},
            {"role": "user", "content": user_message},
        ]
        for step in trace.steps:
            messages.append({"role": "assistant", "content": step.raw_model_output})
            if step.tool_result is not None:
                tool_name = step.parsed_step.tool_call.tool_name
                messages.append(
                    {"role": "user", "content": f"[tool_result:{tool_name}] {step.tool_result}"}
                )
        return messages

    def run(self, user_message: str) -> AgentTrace:
        trace = AgentTrace(user_message=user_message)
        started = time.perf_counter()
        for index in range(self.max_steps):
            messages = self._build_messages(user_message, trace)
            step_started = time.perf_counter()
            outcome = parse_with_repair(self.model.generate(messages), self.model, messages)
            step_trace = StepTrace(
                index=index,
                raw_model_output=outcome.raw,
                parsed_step=outcome.step,
                repair_attempts=outcome.attempts,
                latency_ms=(time.perf_counter() - step_started) * 1000,
            )
            if outcome.step.step_type == "final_answer":
                trace.final_response = outcome.step.final_answer.response
                trace.steps.append(step_trace)
                break
            tool_call = outcome.step.tool_call
            try:
                step_trace.tool_result = self.tools.execute(
                    tool_call.tool_name, tool_call.arguments, memory=self.memory
                )
            except Exception as exc:  # Return tool failures as observations for the next model step.
                step_trace.tool_result = f"ERROR: {exc}"
            trace.steps.append(step_trace)
        else:
            trace.final_response = "I could not complete the task within the step limit."
        trace.total_latency_ms = (time.perf_counter() - started) * 1000
        trace.cost_usd = self.model.last_run_cost()
        return trace

