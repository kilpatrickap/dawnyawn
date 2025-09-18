# dawnyawn/agent/task_manager.py
from typing import List
from config import get_llm_client, LLM_MODEL_NAME
from models.task_node import TaskNode, TaskStatus
from agent.agent_scheduler import AgentScheduler
from agent.thought_engine import ThoughtEngine
from tools.tool_manager import ToolManager
from services.event_manager import EventManager


class TaskManager:
    """Manages the global state and orchestrates the execution of the plan."""

    def __init__(self, goal: str):
        self.goal = goal
        self.plan: List[TaskNode] = []
        self.tool_manager = ToolManager()
        self.scheduler = AgentScheduler()
        self.thought_engine = ThoughtEngine(self.tool_manager)
        self.event_manager = EventManager()
        self.summarizer_client = get_llm_client()
        self.global_context = f"The user's overall goal is: {goal}"

    def run(self):
        self.event_manager.log_event("INFO", f"Starting new DawnYawn mission for goal: {self.goal}")
        self.plan = self.scheduler.create_plan(self.goal)

        print("\n📝 Plan Created:")
        for task in self.plan: print(f"  - Step {task.task_id}: {task.description}")

        confirm = input("\nProceed with execution? (y/n): ")
        if confirm.lower() != 'y': print("Mission aborted."); return

        for task in self.plan:
            task.status = TaskStatus.RUNNING
            self.event_manager.log_task_status(task)
            try:
                tool_selection = self.thought_engine.choose_tool(task, self.global_context)
                task.tool_used = tool_selection.tool_name
                task.tool_input = tool_selection.tool_input

                tool = self.tool_manager.get_tool(tool_selection.tool_name)
                task.raw_result = tool.execute(tool_selection.tool_input)

                task.summary = self._summarize_result(task)
                self.global_context += f"\n\nStep {task.task_id} ({task.description}):\n{task.summary}"
                task.status = TaskStatus.COMPLETED
            except Exception as e:
                error_message = f"Task failed: {e}"
                print(f"  > {error_message}")
                task.status, task.raw_result, task.summary = TaskStatus.FAILED, error_message, "Task failed due to an error."
            self.event_manager.log_task_status(task)

        self.event_manager.log_event("SUCCESS", "All tasks completed. Mission accomplished.")
        self._generate_final_report()

    def _summarize_result(self, task: TaskNode) -> str:
        prompt = f"Summarize the key findings from this command output in one or two sentences. Task was: '{task.description}'.\n\nOutput:\n{task.raw_result}"
        response = self.summarizer_client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=[{"role": "system", "content": "You are a concise analysis assistant."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()

    def _generate_final_report(self):
        print("\n\n--- DAWNYAWN MISSION REPORT ---")
        print(f"Goal: {self.goal}\n")
        for task in self.plan:
            print(f"Step {task.task_id}: {task.description} [{task.status}]")
            print(f"  - Tool: {task.tool_used}")
            print(f"  - Input: `{task.tool_input}`")
            print(f"  - Summary: {task.summary}\n")