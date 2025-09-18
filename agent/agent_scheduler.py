# dawnyawn/agent/agent_scheduler.py (CORRECTED)
import re
from typing import List
from pydantic import BaseModel, Field
from config import get_llm_client, LLM_MODEL_NAME
from models.task_node import TaskNode


class Plan(BaseModel):
    tasks: List[str] = Field(..., description="A list of task descriptions that logically sequence to solve the goal.")


def _clean_json_response(response_str: str) -> str:
    """Finds and extracts the JSON object from a string."""
    match = re.search(r'\{.*\}', response_str, re.DOTALL)
    if match:
        return match.group(0)
    return response_str


class AgentScheduler:
    """LLM Orchestrator. Creates the high-level plan."""

    def __init__(self):
        self.client = get_llm_client()
        # --- THIS IS THE MODIFIED PROMPT ---
        self.system_prompt = """
You are a master planner for an autonomous agent. Decompose the user's goal into a sequence of simple, actionable steps.

**Crucial Rules for Planning:**
1. The agent is in a **stateless environment**. Each step/command runs in a brand new, clean container.
2. **DO NOT** plan steps that rely on previous state (e.g., 'cd', 'git clone', installing software, saving files).
3. Keep the plan as short and direct as possible. If the goal can be done in one step, create a one-step plan.

Your response MUST BE ONLY a single, valid JSON object that conforms to the following Pydantic model:
{"tasks": ["list of task descriptions..."]}
"""

    def create_plan(self, goal: str) -> List[TaskNode]:
        print(f"🗓️  Scheduling plan for goal: '{goal}'")
        response = self.client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Goal: {goal}"}
            ]
        )
        raw_response = response.choices[0].message.content
        cleaned_response = _clean_json_response(raw_response)

        plan_data = Plan.model_validate_json(cleaned_response)
        return [TaskNode(task_id=i + 1, description=desc) for i, desc in enumerate(plan_data.tasks)]