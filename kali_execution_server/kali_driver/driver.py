# kali_execution_server/kali_server.py
import uvicorn
import traceback
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
# --- THIS IS THE CORRECT IMPORT ---
# It points to the local folder, not a package.
from kali_driver.driver import KaliManager, KaliContainer

app = FastAPI(title="DawnYawn Execution Server")
print("Initializing Kali Docker Manager...")
kali_manager = KaliManager()
print("Kali Docker Manager initialized.")

class TaskRequest(BaseModel):
    prompt: str

@app.post("/execute")
def execute_task(request: TaskRequest):
    container: KaliContainer = None
    command_to_run = request.prompt.strip()
    print(f"\n--- [1/2] Received command: '{command_to_run}' ---")

    try:
        container = kali_manager.create_container()
        raw_tool_output = container.send_command_and_get_output(command_to_run)
        print("--- ✅ [2/2] Execution Complete ---")
        return {"result": raw_tool_output}

    except Exception as e:
        print(f"!!! An error occurred: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if container:
            container.destroy()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=1611)