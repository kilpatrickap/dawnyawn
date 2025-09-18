# dawnyawn/tools/tool_manager.py
from tools.base_tool import BaseTool
from tools.os_command_tool import OsCommandTool


class ToolManager:
    """Function Registry that holds and provides access to all available tools."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

        # Manually register all available tools for simplicity.
        # In a more advanced system, this could be done via dynamic plugin loading.
        self._register_tool(OsCommandTool())

    def _register_tool(self, tool: BaseTool):
        if tool.name in self._tools:
            raise ValueError(f"Tool with name '{tool.name}' is already registered.")
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseTool:
        """Retrieves an instantiated tool by its name."""
        if name not in self._tools:
            # This helps the Thought Engine recover if it hallucinates a tool name.
            raise ValueError(f"Tool '{name}' not found. Available tools are: {list(self._tools.keys())}")
        return self._tools[name]

    def get_tool_manifest(self) -> str:
        """
        Returns a formatted string of all available tools.
        This manifest is injected into the Thought Engine's prompt so the LLM knows what it can do.
        """
        manifest = "Your response must select one of the following available tools:\n"
        for tool in self._tools.values():
            manifest += f"- Tool Name: `{tool.name}`\n  Description: {tool.description}\n"
        return manifest