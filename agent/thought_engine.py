# dawnyawn/agent/thought_engine.py (Interactive Version)
import re
from pydantic import BaseModel
from config import get_llm_client, LLM_MODEL_NAME, LLM_REQUEST_TIMEOUT
from tools.tool_manager import ToolManager
from typing import List, Dict


class ToolSelection(BaseModel):
    tool_name: str
    tool_input: str


def _clean_json_response(response_str: str) -> str:
    match = re.search(r'\{.*\}', response_str, re.DOTALL)
    if match: return match.group(0)
    return response_str


class ThoughtEngine:
    """AI Reasoning component. Decides the single next action to take."""

    def __init__(self, tool_manager: ToolManager):
        self.client = get_llm_client()
        self.tool_manager = tool_manager
        self.system_prompt = f"""
You are an expert penetration tester AI operating in a persistent Kali Linux container. You work in an interactive loop.

**Your Goal:** To achieve the user's overall mission.
**Your Process:**
1. You will be given the main goal and a history of your previous actions and their results.
2. Based on this information, you must decide the single best **next action** to take.
3. Your action is to choose one of the available tools and provide the input for it.
4. When you have gathered all the necessary information and fully completed the mission, you MUST use the `finish_mission` tool.

**Rules:**
- Think step-by-step.
- The container is stateful. `cd` and file creation will persist between your commands.
- All tools like nmap are in the system PATH. Call them directly (e.g., `nmap -sV target.com`).

{self.tool_manager.get_tool_manifest()}

Your response MUST BE ONLY a single, valid JSON object with "tool_name" and "tool_input".
"""

    def choose_next_action(self, goal: str, history: List[Dict]) -> ToolSelection:
        print(f"\n🤔 Thinking about the next step...")

        # Format the history for the prompt
        formatted_history = "No actions taken yet."
        if history:
            formatted_history = ""
            for i, item in enumerate(history):
                formatted_history += f"Step {i + 1}:\n"
                formatted_history += f"  - Action: Ran command `{item['command']}`\n"
                formatted_history += f"  - Observation: {item['summary']}\n"

        user_prompt = f"Main Goal: {goal}\n\nExecution History:\n{formatted_history}\n\nWhat is your next single action to get closer to the main goal?"

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
        print(f"  > AI's Next Action: Use tool '{selection.tool_name}' with input '{selection.tool_input}'")
        return selection