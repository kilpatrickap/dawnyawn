# villager_lite_agent/agent/agent_scheduler.py
import os
import json
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List
from config import llm_config
from models.task_node import TaskNode

class Plan(BaseModel):
    tasks: List[str] = Field(..., description="A list of task descriptions that logically sequence to solve the goal.")

class AgentScheduler:
    """LLM Orchestrator. Creates the high-level plan."""
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.system_prompt = """
You are a master planner for an autonomous agent. Decompose the user's goal into a sequence of simple, actionable steps.
Each step should be a clear instruction for the agent. Respond with a JSON object containing a "tasks" key, which is a list of strings.
"""
    def create_plan(self, goal: str) -> List[TaskNode]:
        print(f"🗓️  Scheduling plan for goal: '{goal}'")
        response = self.client.chat.completions.create(
            model=llm_config.PLANNER_MODEL,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Goal: {goal}"}
            ],
            response_format={"type": "json_object"}
        )
        plan_data = Plan.model_validate_json(response.choices[0].message.content)
        return [TaskNode(task_id=i+1, description=desc) for i, desc in enumerate(plan_data.tasks)]