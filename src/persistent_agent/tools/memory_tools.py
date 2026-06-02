from __future__ import annotations

from pydantic import BaseModel, Field

from persistent_agent.tools.base import Tool


class SearchMemoryArgs(BaseModel):
    query: str = Field(description="Topic or keyword to retrieve")


class SearchMemory(Tool):
    name = "search_memory"
    description = "Search prior conversations and notes."
    args_schema = SearchMemoryArgs

    def run(self, args: SearchMemoryArgs, *, memory) -> str:
        hits = memory.semantic_search(args.query, k=3)
        return "\n".join(f"- {hit}" for hit in hits) if hits else "No relevant memory found."


class ListOpenTasksArgs(BaseModel):
    keyword: str | None = Field(default=None, description="Optional title filter")


class ListOpenTasks(Tool):
    name = "list_open_tasks"
    description = "List unfinished tasks, optionally filtered by keyword."
    args_schema = ListOpenTasksArgs

    def run(self, args: ListOpenTasksArgs, *, memory) -> str:
        tasks = memory.list_tasks(status="open", keyword=args.keyword)
        if not tasks:
            return "No open tasks found."
        return "\n".join(f"[{task.id}] {task.title} - deadline: {task.deadline or 'none'}" for task in tasks)

