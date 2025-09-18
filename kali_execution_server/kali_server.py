# kali_execution_server/kali_server.py (Interactive Session Version)
import uvicorn
import traceback
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict

from kali_driver.driver import KaliManager, KaliContainer

app = FastAPI(title="DawnYawn Interactive Execution Server")
print("Initializing Kali Docker Manager...")
kali_manager = KaliManager()
# This dictionary will hold our active sessions
active_sessions: Dict[str, KaliContainer] = {}
print("Kali Docker Manager initialized.")


class SessionRequest(BaseModel):
    session_id: str


class ExecuteRequest(SessionRequest):
    command: str


@app.post("/session/start")
def start_session():
    """Creates a new persistent Kali container and returns a session ID."""
    session_id = str(uuid.uuid4())
    print(f"\n--- [START] Received request to start new session ---")
    try:
        container = kali_manager.create_container()
        active_sessions[session_id] = container
        print(f"--- ✅ New session '{session_id}' started successfully ---")
        return {"session_id": session_id}
    except Exception as e:
        print(f"!!! FAILED to start session: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create container: {e}")


@app.post("/session/execute")
def execute_in_session(request: ExecuteRequest):
    """Executes a command in an existing session's container."""
    container = active_sessions.get(request.session_id)
    if not container:
        raise HTTPException(status_code=404, detail="Session not found.")

    print(f"\n--- [EXECUTE] Running command in session '{request.session_id}': '{request.command}' ---")
    try:
        output = container.send_command_and_get_output(request.command)
        print("--- ✅ Command executed ---")
        return {"output": output}
    except Exception as e:
        print(f"!!! FAILED to execute command: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Command execution failed: {e}")


@app.post("/session/end")
def end_session(request: SessionRequest):
    """Destroys the container associated with the session ID."""
    container = active_sessions.pop(request.session_id, None)
    if not container:
        raise HTTPException(status_code=404, detail="Session not found.")

    print(f"\n--- [END] Received request to end session '{request.session_id}' ---")
    try:
        container.destroy()
        print(f"--- ✅ Session ended successfully ---")
        return {"message": "Session ended and container destroyed."}
    except Exception as e:
        print(f"!!! FAILED to end session: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to destroy container: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=1611)