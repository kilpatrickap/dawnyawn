# villager_lite_agent/services/event_manager.py
from models.task_node import TaskNode


class EventManager:
    """A simple alert and logging system. In a real system, this would
    connect to DingTalk, Slack, or a logging service."""

    def log_event(self, level: str, message: str):
        print(f"[{level}] {message}")

    def log_task_status(self, task: TaskNode):
        print(f"[{task.status}] Task {task.task_id}: {task.description}")

    # In a real system, you might have:
    # def send_dingtalk_alert(self, message: str):
    #     # Code to send a message to a DingTalk bot
    #     pass