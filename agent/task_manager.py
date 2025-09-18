# dawnyawn/agent/task_manager.py (Hybrid Version)
from openai import APITimeoutError
from config import get_llm_client, LLM_MODEL_NAME, LLM_REQUEST_TIMEOUT, MAX_SUMMARY_INPUT_LENGTH
from models.task_node import TaskNode
# Import the new scheduler
from agent.agent_scheduler import AgentScheduler
from agent.thought_engine import ThoughtEngine
from tools.tool_manager import ToolManager
from services.event_manager import EventManager
from services.mcp_client import McpClient


class TaskManager:
    """Orchestrates the Plan -> Approve -> Execute loop."""

    def __init__(self, goal: str):
        self.goal = goal
        self.mission_history = []
        # Re-introduce the scheduler
        self.scheduler = AgentScheduler()
        self.thought_engine = ThoughtEngine(ToolManager())
        self.event_manager = EventManager()
        self.mcp_client = McpClient()
        self.summarizer_client = get_llm_client()

    def run(self):
        self.event_manager.log_event("INFO", f"Starting new hybrid mission for goal: {self.goal}")

        # --- PHASE 1: PLANNING & APPROVAL ---
        try:
            plan = self.scheduler.create_plan(self.goal)
            print("\n📝 High-Level Plan Created:")
            for task in plan:
                print(f"  - {task.description}")

            confirm = input("\nProceed with this plan? (y/n): ")
            if confirm.lower() != 'y':
                print("Mission aborted by user.")
                return
        except (APITimeoutError, KeyboardInterrupt) as e:
            print(f"\nMission aborted during planning: {e}")
            return

        # --- PHASE 2: INTERACTIVE EXECUTION ---
        session_id = self.mcp_client.start_session()
        if not session_id: return

        try:
            while True:
                # THINK: Decide the next action based on the plan and history
                action = self.thought_engine.choose_next_action(self.goal, plan, self.mission_history)

                # ACT: Check for finish condition or execute
                if action.tool_name == "finish_mission":
                    self.event_manager.log_event("SUCCESS", "AI has decided the mission is complete.")
                    self.mission_history.append({"command": "finish_mission", "summary": action.tool_input})
                    break

                raw_output = self.mcp_client.execute_command(session_id, action.tool_input)

                # OBSERVE: Summarize and record
                summary = self._summarize_result(action.tool_input, raw_output)
                self.mission_history.append({"command": action.tool_input, "summary": summary})

                # Check if we have run too many steps (a safety break)
                if len(self.mission_history) >= 10:
                    self.event_manager.log_event("WARN", "Maximum step limit (10) reached. Ending mission.")
                    break

        except (APITimeoutError, KeyboardInterrupt) as e:
            print(f"\nMission aborted during execution: {e}")
        finally:
            self.mcp_client.end_session(session_id)
            self._generate_final_report()

    def _summarize_result(self, command: str, raw_output: str) -> str:
        # ... (This method is unchanged, but I'll include it for completeness)
        if len(raw_output) > MAX_SUMMARY_INPUT_LENGTH:
            truncated_output = raw_output[:MAX_SUMMARY_INPUT_LENGTH]
        else:
            truncated_output = raw_output
        prompt = f"Summarize findings from this output. The command was: '{command}'.\n\nOutput:\n{truncated_output}"
        try:
            response = self.summarizer_client.chat.completions.create(
                model=LLM_MODEL_NAME,
                messages=[{"role": "system", "content": "You are a concise analysis assistant."},
                          {"role": "user", "content": prompt}],
                timeout=LLM_REQUEST_TIMEOUT
            )
            return response.choices[0].message.content.strip()
        except APITimeoutError:
            print("   > ❌ Summarization timed out.")
            return "Observation failed: The AI model took too long to summarize the result."

    def _generate_final_report(self):
        # ... (This method is unchanged)
        print("\n\n--- DAWNYAWN HYBRID MISSION REPORT ---")
        print(f"Goal: {self.goal}\n")
        for i, item in enumerate(self.mission_history):
            print(f"Step {i + 1}:")
            print(f"  - Action: `{item['command']}`")
            print(f"  - Summary: {item['summary']}\n")