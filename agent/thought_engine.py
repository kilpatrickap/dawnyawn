# dawnyawn/agent/thought_engine.py (Final, Strongest Prompt)
import re
from pydantic import BaseModel
from pydantic_core import ValidationError
from config import get_llm_client, LLM_MODEL_NAME, LLM_REQUEST_TIMEOUT
from tools.tool_manager import ToolManager
from models.task_node import TaskNode
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
        # --- THIS IS THE NEW, STRONGEST PROMPT ---
        self.system_prompt = f"""
You are an expert penetration tester AI. Your job is to select the next command to execute based on a strategic plan.

**Crucial Rules for Your Response:**
1.  Your output MUST be a JSON object with EXACTLY TWO keys: "tool_name" and "tool_input".
2.  The value of "tool_name" MUST be one of the tools listed below.
3.  The value of "tool_input" MUST be the complete shell command to run.

**Example of a PERFECT response:**
User's Plan: "Scan example.com for open ports."
Your Response:
{{
  "tool_name": "os_command",
  "tool_input": "nmap -sV example.com"
}}

**Available Tools:**
{self.tool_manager.get_tool_manifest()}

Your final output MUST BE ONLY the single, valid JSON object and nothing else.
"""

    def choose_next_action(self, goal: str, plan: List[TaskNode], history: List[Dict]) -> ToolSelection:
        print(f"\n🤔 Thinking about the next step...")

        formatted_plan = "\n".join([f"  - {step.description}" for step in plan])
        formatted_history = "No actions taken yet."
        if history:
            formatted_history = "\n".join(
                [f"Action {i + 1}: Ran `{item['command']}` -> Observation: {item.get('observation_json', 'N/A')}" for
                 i, item in enumerate(history)])

        user_prompt = (
            f"Main Goal: {goal}\n\nStrategic Plan:\n{formatted_plan}\n\n"
            f"Execution History:\n{formatted_history}\n\n"
            "Based on the plan and history, what is your single best command for your next action? Respond with a JSON object."
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

        try:
            selection = ToolSelection.model_validate_json(cleaned_response)
            print(f"  > AI's Next Action: {selection.tool_input}")
            return selection
        except ValidationError:
            print("\n❌ Critical Error: The AI model returned an invalid action that did not match the required schema.")
            print(f"   Model's raw response: \"{raw_response}\"")
            return ToolSelection(tool_name="finish_mission",
                                 tool_input="Mission failed: The AI returned an invalid action.")