# villager_lite_agent/services/mcp_client.py
import requests
from config import service_config

class McpClient:
    """Multi-Component Protocol Client
    Handles communication with external driver services like Kali, Browser, etc.
    """
    def send_kali_command(self, command: str) -> str:
        """Sends a command to the Kali Driver service."""
        try:
            response = requests.post(
                service_config.KALI_DRIVER_URL,
                json={"prompt": command},
                timeout=1800
            )
            response.raise_for_status()
            return response.json().get("result", "No result field in response.")
        except requests.exceptions.RequestException as e:
            error_message = f"ERROR: Failed to connect to Kali Driver at {service_config.KALI_DRIVER_URL}. Details: {e}"
            print(error_message)
            return error_message