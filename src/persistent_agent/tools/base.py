from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel


class Tool(ABC):
    name: str
    description: str
    args_schema: type[BaseModel]

    @abstractmethod
    def run(self, args: BaseModel, *, memory) -> str:
        raise NotImplementedError

    def catalog_entry(self) -> str:
        fields = ", ".join(self.args_schema.model_fields)
        return f"- {self.name}({fields}): {self.description}"


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def catalog_text(self) -> str:
        return "Available tools:\n" + "\n".join(tool.catalog_entry() for tool in self._tools.values())

    def execute(self, name: str, arguments: dict, *, memory) -> str:
        tool = self._tools[name]
        return tool.run(tool.args_schema.model_validate(arguments), memory=memory)

