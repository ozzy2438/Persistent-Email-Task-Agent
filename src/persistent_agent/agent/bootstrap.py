from __future__ import annotations

from persistent_agent.agent.loop import Agent
from persistent_agent.memory.store import MemoryStore
from persistent_agent.models.factory import build_model_client
from persistent_agent.tools.base import ToolRegistry
from persistent_agent.tools.memory_tools import ListOpenTasks, SearchMemory

SYSTEM_PROMPT = """You are a proactive email and task assistant.
Check structured open tasks and relevant prior context before answering.
Never invent missing details. Return only JSON matching the AgentStep schema.
"""


def build_agent(model_client=None, db_path: str = ":memory:") -> Agent:
    tools = ToolRegistry()
    tools.register(ListOpenTasks())
    tools.register(SearchMemory())
    return Agent(
        model_client=model_client or build_model_client(),
        tools=tools,
        memory=MemoryStore(db_path),
        system_prompt=SYSTEM_PROMPT,
    )


def seed_acme_scenario(agent: Agent) -> None:
    agent.memory.remember(
        "Tuesday email from manager@company.com: Send the Acme proposal by Friday.",
        {"type": "email", "day": "tuesday"},
    )
    agent.memory.save_task(
        title="Prepare and send the Acme proposal",
        source="manager@company.com / Acme proposal",
        deadline="Friday",
    )
