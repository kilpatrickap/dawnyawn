# dawnyawn/agent/agent_scheduler.py
import re
from typing import List
from pydantic import BaseModel, Field
from config import get_llm_client, LLM_MODEL_NAME, LLM_REQUEST_TIMEOUT
from models.task_node import TaskNode


class Plan(BaseModel):
    tasks: List[str] = Field(...,
                             description="A list of high-level task descriptions that logically sequence to solve the goal.")


def _clean_json_response(response_str: str) -> str:
    match = re.search(r'\{.*\}', response_str, re.DOTALL)
    if match: return match.group(0)
    return response_str


class AgentScheduler:
    """LLM Orchestrator. Creates the high-level strategic plan for user review."""

    def __init__(self):
        self.client = get_llm_client()
        self.system_prompt = """
You are a master strategist. Your job is to convert a user's goal into a high-level, human-readable plan.

**Crucial Rules for Planning:**
1.  The plan should be a logical sequence of strategic steps.
2.  Do not include specific commands, only the description of the step (e.g., "Scan the target for open ports").
3.  The agent is stateless between missions but stateful during a mission. Do not plan steps like 'install software'.
4.  Keep the plan concise and focused on achieving the main goal.

Example:
User Goal: "Find the web server on example.com and see its homepage."
Correct Plan: {"tasks": ["Scan example.com for open web ports.", "If a web server is found, retrieve the homepage content."]}

Your response MUST BE ONLY a single, valid JSON object.
"""

    def create_plan(self, goal: str) -> List[TaskNode]:
        print(f"🗓️  Generating strategic plan for goal: '{goal}'")
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
        # Create TaskNode objects from the descriptions
        return [TaskNode(task_id=i + 1, description=desc) for i, desc in enumerate(plan_data.tasks)]