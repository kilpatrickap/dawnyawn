# villager_lite_agent/tools/base_tool.py
from abc import ABC, abstractmethod


class BaseTool(ABC):
    """Abstract base class for all tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A description of what the tool does."""
        pass

    @abstractmethod
    def execute(self, tool_input: str) -> str:
        """Executes the tool with the given input and returns the raw result."""
        pass