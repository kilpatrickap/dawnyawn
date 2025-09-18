# dawnyawn/agent/agent_scheduler.py
from typing import List
from pydantic import BaseModel, Field
from config import get_llm_client, LLM_MODEL_NAME
from models.task_node import TaskNode

class Plan(BaseModel):
    tasks: List[str] = Field(..., description="A list of task descriptions that logically sequence to solve the goal.")

class AgentScheduler:
    """LLM Orchestrator. Creates the high-level plan."""
    def __init__(self):
        self.client = get_llm_client()
        self.system_prompt = """
You are a master planner. Decompose the user's goal into a sequence of simple, actionable steps.
Your response MUST BE ONLY a single, valid JSON object that conforms to the following Pydantic model:
{"tasks": ["list of task descriptions..."]}
Do not include any other text, preambles, or explanations.
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
        plan_data = Plan.model_validate_json(response.choices[0].message.content)
        return [TaskNode(task_id=i+1, description=desc) for i, desc in enumerate(plan_data.tasks)]