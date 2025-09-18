# villager_lite_agent/agent/thought_engine.py
import os
import json
from openai import OpenAI
from pydantic import BaseModel
from config import llm_config
from tools.tool_manager import ToolManager
from models.task_node import TaskNode


class ToolSelection(BaseModel):
    tool_name: str
    tool_input: str


class ThoughtEngine:
    """AI Reasoning component. Decides which tool to use for a given task."""

    def __init__(self, tool_manager: ToolManager):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.tool_manager = tool_manager
        self.system_prompt = f"""
You are the reasoning core of an autonomous agent. Your task is to select the best tool to accomplish a given task and formulate the precise input for that tool.

You must respond with a JSON object containing two keys: "tool_name" and "tool_input".

{self.tool_manager.get_tool_manifest()}
"""

    def choose_tool(self, task: TaskNode, context: str) -> ToolSelection:
        """Chooses the appropriate tool and input for a task."""
        print(f"🤔 Thinking about task: '{task.description}'...")
        user_prompt = f"Previous Context:\n{context}\n\nCurrent Task: {task.description}"

        response = self.client.chat.completions.create(
            model=llm_config.THOUGHT_MODEL,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        response_json = response.choices[0].message.content
        selection = ToolSelection.model_validate_json(response_json)
        print(f"  > Thought: Use tool '{selection.tool_name}' with input '{selection.tool_input}'")
        return selection