# dawnyawn/agent/thought_engine.py
from pydantic import BaseModel
from config import get_llm_client, LLM_MODEL_NAME
from tools.tool_manager import ToolManager
from models.task_node import TaskNode


class ToolSelection(BaseModel):
    tool_name: str
    tool_input: str


class ThoughtEngine:
    """AI Reasoning component. Decides which tool to use for a given task."""

    def __init__(self, tool_manager: ToolManager):
        self.client = get_llm_client()
        self.tool_manager = tool_manager
        self.system_prompt = f"""
You are the reasoning core of an autonomous agent. Select the best tool and formulate the precise input for it.
Your response MUST BE ONLY a single, valid JSON object with two keys: "tool_name" and "tool_input".

{self.tool_manager.get_tool_manifest()}
"""

    def choose_tool(self, task: TaskNode, context: str) -> ToolSelection:
        """Chooses the appropriate tool and input for a task."""
        print(f"🤔 Thinking about task: '{task.description}'...")
        user_prompt = f"Previous Context:\n{context}\n\nCurrent Task: {task.description}"

        response = self.client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        selection = ToolSelection.model_validate_json(response.choices[0].message.content)
        print(f"  > Thought: Use tool '{selection.tool_name}' with input '{selection.tool_input}'")
        return selection