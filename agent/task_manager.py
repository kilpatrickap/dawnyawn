# dawnyawn/agent/task_manager.py (JSON Observation Version)
import json  # <-- Import json
from openai import APITimeoutError
from config import get_llm_client, LLM_MODEL_NAME, LLM_REQUEST_TIMEOUT, MAX_SUMMARY_INPUT_LENGTH
from models.task_node import TaskNode
from models.observation import Observation  # <-- Import our new model
from agent.agent_scheduler import AgentScheduler
from agent.thought_engine import ThoughtEngine
from tools.tool_manager import ToolManager
from services.event_manager import EventManager
from services.mcp_client import McpClient


class TaskManager:
    """Orchestrates the Plan -> Approve -> Execute loop with JSON observations."""

    def __init__(self, goal: str):
        self.goal = goal
        self.mission_history = []
        self.scheduler = AgentScheduler()
        self.thought_engine = ThoughtEngine(ToolManager())
        self.event_manager = EventManager()
        self.mcp_client = McpClient()
        self.formatter_client = get_llm_client()  # Renamed for clarity

    def run(self):
        # ... (This part is unchanged)
        self.event_manager.log_event("INFO", f"Starting new hybrid mission for goal: {self.goal}")
        try:
            plan = self.scheduler.create_plan(self.goal)
            if not plan:
                print("Mission aborted as no valid plan could be created.")
                return
            print("\n📝 High-Level Plan Created:")
            for task in plan: print(f"  - {task.description}")
            confirm = input("\nProceed with this plan? (y/n): ")
            if confirm.lower() != 'y':
                print("Mission aborted by user.");
                return
        except (APITimeoutError, KeyboardInterrupt) as e:
            print(f"\nMission aborted during planning: {e}");
            return

        session_id = self.mcp_client.start_session()
        if not session_id: return

        try:
            while True:
                action = self.thought_engine.choose_next_action(self.goal, plan, self.mission_history)
                if action.tool_name == "finish_mission":
                    self.event_manager.log_event("SUCCESS", "AI has decided the mission is complete.")
                    self.mission_history.append({"command": "finish_mission", "observation_json": action.tool_input})
                    break

                raw_output = self.mcp_client.execute_command(session_id, action.tool_input)

                # --- KEY CHANGE: Get a JSON observation, not a summary ---
                observation_json = self._format_result_as_json(action.tool_input, raw_output)
                self.mission_history.append({"command": action.tool_input, "observation_json": observation_json})

                if len(self.mission_history) >= 10:
                    self.event_manager.log_event("WARN", "Maximum step limit reached.");
                    break
        except (APITimeoutError, KeyboardInterrupt) as e:
            print(f"\nMission aborted during execution: {e}")
        finally:
            self.mcp_client.end_session(session_id)
            self._generate_final_report()

    # --- THIS IS THE NEW, UPGRADED METHOD ---
    def _format_result_as_json(self, command: str, raw_output: str) -> str:
        """
        Takes raw tool output and asks an LLM to format it into a structured
        JSON Observation object.
        """
        print("   ✍️  Formatting output into structured JSON...")
        is_truncated = False
        if len(raw_output) > MAX_SUMMARY_INPUT_LENGTH:
            truncated_output = raw_output[:MAX_SUMMARY_INPUT_LENGTH]
            is_truncated = True
        else:
            truncated_output = raw_output

        # The Pydantic model provides the JSON schema for the prompt
        json_schema = Observation.model_json_schema()

        prompt = (
            f"You are a data formatting expert. Your task is to convert the raw output from a command into a structured JSON object. "
            f"The command that was run was: `{command}`.\n\n"
            f"RAW OUTPUT:\n---\n{truncated_output}\n---\n\n"
            f"Please analyze the output and populate the following JSON schema. The `key_finding` should be a very brief, one-sentence summary.\n"
            f"JSON SCHEMA:\n{json.dumps(json_schema, indent=2)}\n\n"
            f"Your response MUST be ONLY the single, valid JSON object."
        )

        try:
            response = self.formatter_client.chat.completions.create(
                model=LLM_MODEL_NAME,
                messages=[{"role": "system", "content": "You are a JSON formatting assistant."},
                          {"role": "user", "content": prompt}],
                timeout=LLM_REQUEST_TIMEOUT
            )
            # We return the raw JSON string directly
            return response.choices[0].message.content.strip()
        except APITimeoutError:
            print("   > ❌ JSON formatting timed out.")
            # Return a valid JSON error object
            return Observation(
                status="FAILURE",
                key_finding="Observation failed: The AI model took too long to format the result.",
                full_output_truncated=is_truncated,
                full_output=truncated_output
            ).model_dump_json()

    def _generate_final_report(self):
        print("\n\n--- DAWNYAWN HYBRID MISSION REPORT ---")
        print(f"Goal: {self.goal}\n")
        for i, item in enumerate(self.mission_history):
            print(f"Step {i + 1}:")
            print(f"  - Action: `{item['command']}`")
            # We now print the JSON observation for clarity
            print(f"  - Observation: {item['observation_json']}\n")