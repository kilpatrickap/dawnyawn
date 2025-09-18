# villager_lite_agent/main.py
import os
import argparse
from dotenv import load_dotenv
from agent.task_manager import TaskManager


def main():
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("FATAL ERROR: OPENAI_API_KEY not found in .env file.")
        return

    parser = argparse.ArgumentParser(description="Villager-Lite Autonomous Agent")
    parser.add_argument("goal", type=str, help="The high-level goal for the agent.")
    args = parser.parse_args()

    print("--- Villager-Lite Agent Initializing ---")
    print("⚠️  SECURITY WARNING: This agent executes AI-generated commands on a remote server.")

    task_manager = TaskManager(goal=args.goal)
    task_manager.run()


if __name__ == "__main__":
    main()