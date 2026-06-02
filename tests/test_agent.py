import json

from persistent_agent.agent.bootstrap import build_agent, seed_acme_scenario
from persistent_agent.models.client import DemoModelClient


class InvalidTaskReferenceClient:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, messages):
        self.calls += 1
        if self.calls == 1:
            return json.dumps(
                {
                    "step_type": "tool_call",
                    "tool_call": {
                        "tool_name": "list_open_tasks",
                        "arguments": {"keyword": "Acme"},
                        "reasoning": "Find the matching open task.",
                    },
                }
            )
        if self.calls == 2:
            return json.dumps(
                {
                    "step_type": "final_answer",
                    "final_answer": {
                        "response": "The Acme proposal is still open.",
                        "referenced_tasks": ["bogus-task"],
                    },
                }
            )
        task_result = next(
            message["content"]
            for message in messages
            if message["content"].startswith("[tool_result:list_open_tasks]")
        )
        task_id = task_result.split("] ", 1)[1].split("]", 1)[0].removeprefix("[")
        return json.dumps(
            {
                "step_type": "final_answer",
                "final_answer": {
                    "response": "The Acme proposal is still open.",
                    "referenced_tasks": [task_id],
                },
            }
        )

    def last_run_cost(self) -> float:
        return 0.0


def test_agent_carries_acme_task_forward() -> None:
    agent = build_agent()
    seed_acme_scenario(agent)

    trace = agent.run("Where did that Acme thing land?")

    assert trace.tool_calls == ["list_open_tasks", "search_memory"]
    assert "Acme proposal is still open" in trace.final_response
    assert "Friday" in trace.final_response
    task_id = agent.memory.list_tasks(keyword="acme")[0].id
    assert trace.steps[-1].parsed_step.final_answer.referenced_tasks == [task_id]


def test_demo_model_client_extracts_task_id_from_tool_result_prefix() -> None:
    task_id = DemoModelClient._extract_task_id(
        "[tool_result:list_open_tasks] [task-123] Prepare Acme proposal - deadline: Friday"
    )
    assert task_id == "task-123"


def test_agent_rejects_invalid_task_reference_before_accepting_final_answer() -> None:
    agent = build_agent(model_client=InvalidTaskReferenceClient())
    seed_acme_scenario(agent)

    trace = agent.run("Where did that Acme thing land?")

    task_id = agent.memory.list_tasks(keyword="acme")[0].id
    assert trace.final_response == "The Acme proposal is still open."
    assert trace.steps[-1].repair_attempts == 1
    assert trace.steps[-1].parsed_step.final_answer.referenced_tasks == [task_id]


def test_build_agent_registers_local_email_tools() -> None:
    agent = build_agent()

    catalog = agent.tools.catalog_text()

    assert "read_emails(query, limit)" in catalog
    assert "summarize_thread(query, limit)" in catalog
    assert "draft_reply(query, recipient, guidance)" in catalog
    assert agent.memory.list_emails(limit=1) == []
