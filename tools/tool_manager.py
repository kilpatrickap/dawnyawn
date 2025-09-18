# villager_lite_agent/tools/tool_manager.py
from tools.base_tool import BaseTool
from tools.os_command_tool import OsCommandTool


class ToolManager:
    """Function Registry that holds and provides access to all available tools."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        # Manually register tools for simplicity
        self._register_tool(OsCommandTool())

    def _register_tool(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found.")
        return self._tools[name]

    def get_tool_manifest(self) -> str:
        """Returns a formatted string of all available tools for the LLM."""
        manifest = "Available Tools:\n"
        for tool in self._tools.values():
            manifest += f"- Tool Name: {tool.name}\n  Description: {tool.description}\n"
        return manifest