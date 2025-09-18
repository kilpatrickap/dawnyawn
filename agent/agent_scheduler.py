# dawnyawn/agent/agent_scheduler.py (CORRECTED)
import re
from typing import List
from pydantic import BaseModel, Field
from config import get_llm_client, LLM_MODEL_NAME, LLM_REQUEST_TIMEOUT
from models.task_node import TaskNode


class Plan(BaseModel):
    tasks: List[str] = Field(..., description="A list of task descriptions that logically sequence to solve the goal.")


def _clean_json_response(response_str: str) -> str:
    match = re.search(r'\{.*\}', response_str, re.DOTALL)
    if match: return match.group(0)
    return response_str


class AgentScheduler:
    """LLM Orchestrator. Creates the high-level plan."""

    def __init__(self):
        self.client = get_llm_client()
        # --- THIS IS THE FINAL, IMPROVED PROMPT ---
        self.system_prompt = """
You are a master planner. Your job is to convert a user's goal into a direct, simple, and effective command-line plan.

**Crucial Rules for Planning:**
1.  **Think in high-level tools, not low-level concepts.** Do not break actions down into abstract steps like "send a packet."
2.  **Create a plan that directly reflects the user's request.** If the user asks to "ping a host," the plan should have one step: "Ping the host to check connectivity."
3.  **The agent is stateless.** Do not plan steps that rely on previous state (like 'cd' or saving files).
4.  Keep the plan as short and direct as possible.

Example:
User Goal: "Perform a brief ping on www.google.com."
Correct Plan: {"tasks": ["Ping www.google.com to check for connectivity."]}

Your response MUST BE ONLY a single, valid JSON object that conforms to the Pydantic model.
"""

    def create_plan(self, goal: str) -> List[TaskNode]:
        print(f"🗓️  Scheduling plan for goal: '{goal}'")
        response = self.client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Goal: {goal}"}
            ],
            timeout=LLM_REQUEST_TIMEOUT
        )
        raw_response = response.choices[0].message.content
        cleaned_response = _clean_json_response(raw_response)

        plan_data = Plan.model_validate_json(cleaned_response)
        return [TaskNode(task_id=i + 1, description=desc) for i, desc in enumerate(plan_data.tasks)]