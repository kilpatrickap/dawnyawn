# villager_lite_agent/config.py
from pydantic import BaseModel

class LLMConfig(BaseModel):
    PLANNER_MODEL: str = "gpt-4o-mini"
    THOUGHT_MODEL: str = "gpt-4o-mini"
    SUMMARIZER_MODEL: str = "gpt-4o-mini"

class ServiceConfig(BaseModel):
    KALI_DRIVER_URL: str = "http://127.0.0.1:1611/execute" # Port from diagram

# Global config objects
llm_config = LLMConfig()
service_config = ServiceConfig()