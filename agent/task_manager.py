# dawnyawn/agent/task_manager.py (Interactive Loop Version)
from config import get_llm_client, LLM_MODEL_NAME, LLM_REQUEST_TIMEOUT, MAX_SUMMARY_INPUT_LENGTH
from agent.thought_engine import ThoughtEngine
from tools.tool_manager import ToolManager
from services.event_manager import EventManager
from services.mcp_client import McpClient

class TaskManager:
    """Orchestrates the interactive Think->Act->Observe loop."""
    def __init__(self, goal: str):
        self.goal = goal
        self.mission_history = []
        self.thought_engine = ThoughtEngine(ToolManager())
        self.event_manager = EventManager()
        self.mcp_client = McpClient()
        self.summarizer_client = get_llm_client()

    def run(self):
        self.event_manager.log_event("INFO", f"Starting new interactive mission for goal: {self.goal}")
        session_id = self.mcp_client.start_session()
        if not session_id: return

        try:
            while True:
                # 1. THINK: Decide the next action
                action = self.thought_engine.choose_next_action(self.goal, self.mission_history)

                # 2. ACT: Check for finish condition or execute the command
                if action.tool_name == "finish_mission":
                    self.event_manager.log_event("SUCCESS", "AI has decided the mission is complete.")
                    # Add the final summary from the AI to the report
                    self.mission_history.append({
                        "command": "finish_mission",
                        "raw_output": "Mission complete.",
                        "summary": action.tool_input # The AI's final summary
                    })
                    break

                # Execute the command in the persistent session
                raw_output = self.mcp_client.execute_command(session_id, action.tool_input)

                # 3. OBSERVE: Summarize the result and add to history
                summary = self._summarize_result(action.tool_input, raw_output)
                self.mission_history.append({
                    "command": action.tool_input,
                    "raw_output": raw_output,
                    "summary": summary
                })

        except KeyboardInterrupt:
            print("\nMission aborted by user.")
        finally:
            # 4. CLEANUP: Always end the session
            self.mcp_client.end_session(session_id)
            self._generate_final_report()

    def _summarize_result(self, command: str, raw_output: str) -> str:
        if len(raw_output) > MAX_SUMMARY_INPUT_LENGTH:
            truncated_output = raw_output[:MAX_SUMMARY_INPUT_LENGTH]
        else:
            truncated_output = raw_output
        prompt = f"Summarize findings from this output. The command run was: '{command}'.\n\nOutput:\n{truncated_output}"
        response = self.summarizer_client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=[{"role": "system", "content": "You are a concise analysis assistant."}, {"role": "user", "content": prompt}],
            timeout=LLM_REQUEST_TIMEOUT
        )
        return response.choices[0].message.content.strip()

    def _generate_final_report(self):
        print("\n\n--- DAWNYAWN INTERACTIVE MISSION REPORT ---")
        print(f"Goal: {self.goal}\n")
        for i, item in enumerate(self.mission_history):
            print(f"Step {i+1}:")
            print(f"  - Action: `{item['command']}`")
            print(f"  - Summary: {item['summary']}\n")