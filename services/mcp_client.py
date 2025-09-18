# dawnyawn/services/mcp_client.py (Session Version)
import requests
from config import service_config

class McpClient:
    """Handles session-based communication with the Kali execution server."""

    def start_session(self) -> str:
        """Requests the server to start a new session and returns the session ID."""
        try:
            response = requests.post(f"{service_config.KALI_DRIVER_URL}/session/start", timeout=60)
            response.raise_for_status()
            return response.json()["session_id"]
        except requests.exceptions.RequestException as e:
            print(f"FATAL: Could not start a new session on the server. {e}")
            raise

    def execute_command(self, session_id: str, command: str) -> str:
        """Executes a command within a given session."""
        try:
            response = requests.post(
                f"{service_config.KALI_DRIVER_URL}/session/execute",
                json={"session_id": session_id, "command": command},
                timeout=1800 # 30 min timeout for long commands
            )
            response.raise_for_status()
            return response.json().get("output", "No output received.")
        except requests.exceptions.RequestException as e:
            return f"ERROR: Failed to execute command. {e}"

    def end_session(self, session_id: str):
        """Tells the server to end the session and clean up the container."""
        try:
            requests.post(f"{service_config.KALI_DRIVER_URL}/session/end", json={"session_id": session_id}, timeout=60)
            print("✅ Session terminated successfully on the server.")
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Warning: Failed to terminate session on the server. {e}")