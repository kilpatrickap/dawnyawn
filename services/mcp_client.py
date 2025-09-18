# dawnyawn/services/mcp_client.py
import requests
from config import service_config

class McpClient:
    """Multi-Component Protocol Client
    Handles communication with external driver services like the Kali server.
    """
    def send_kali_command(self, command: str) -> str:
        """Sends a command to the Kali Driver service."""
        try:
            response = requests.post(
                service_config.KALI_DRIVER_URL,
                json={"prompt": command},
                timeout=1800  # 30-minute timeout for long scans
            )
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            return response.json().get("result", "No result field in response.")
        except requests.exceptions.RequestException as e:
            error_message = f"ERROR: Failed to connect to Kali Driver at {service_config.KALI_DRIVER_URL}. Ensure the server is running. Details: {e}"
            print(error_message)
            return error_message