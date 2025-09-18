# dawnyawn/agent/thought_engine.py (Plan-Aware Version)
import re
from pydantic import BaseModel
from config import get_llm_client, LLM_MODEL_NAME, LLM_REQUEST_TIMEOUT
from tools.tool_manager import ToolManager
from models.task_node import TaskNode  # Import TaskNode
from typing import List, Dict


class ToolSelection(BaseModel):
    tool_name: str
    tool_input: str


def _clean_json_response(response_str: str) -> str:
    match = re.search(r'\{.*\}', response_str, re.DOTALL)
    if match: return match.group(0)
    return response_str


class ThoughtEngine:
    """AI Reasoning component. Decides the single next action based on a plan."""

    def __init__(self, tool_manager: ToolManager):
        self.client = get_llm_client()
        self.tool_manager = tool_manager
        self.system_prompt = f"""
You are an expert penetration tester AI working to execute a strategic plan.

**Your Goal:** Follow the strategic plan step-by-step.
**Your Process:**
1. You will receive the main goal, the overall plan, and your execution history.
2. Based on this, determine the single best command to execute for the **current step** of the plan.
3. If you complete the plan or achieve the goal, you MUST use the `finish_mission` tool.

**Rules:**
- The container is stateful. `cd` and file creation will persist.
- Call tools directly (e.g., `nmap -sV target.com`).

{self.tool_manager.get_tool_manifest()}

Your response MUST BE ONLY a single, valid JSON object.
"""

    def choose_next_action(self, goal: str, plan: List[TaskNode], history: List[Dict]) -> ToolSelection:
        print(f"\n🤔 Thinking about the next step...")

        # Format the plan and history for the prompt
        formatted_plan = "\n".join([f"  - {step.description}" for step in plan])

        formatted_history = "No actions taken yet."
        if history:
            formatted_history = ""
            for i, item in enumerate(history):
                formatted_history += f"Action {i + 1}: Ran command `{item['command']}` -> Observation: {item['summary']}\n"

        user_prompt = (
            f"Main Goal: {goal}\n\n"
            f"Strategic Plan:\n{formatted_plan}\n\n"
            f"Execution History:\n{formatted_history}\n\n"
            "Based on the plan and history, what is the single best command for your next action?"
        )

        response = self.client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            timeout=LLM_REQUEST_TIMEOUT
        )
        raw_response = response.choices[0].message.content
        cleaned_response = _clean_json_response(raw_response)
        selection = ToolSelection.model_validate_json(cleaned_response)
        print(f"  > AI's Next Action: {selection.tool_input}")
        return selection