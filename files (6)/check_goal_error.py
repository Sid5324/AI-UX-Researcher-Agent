import sqlite3
import os

db_path = r"d:\ai\AI UX Researcher Agent\files (6)\AGENTIC-AI-VERIFIED-FIXES\agentic-research-ai-FIXED\backend\data\agentic_research.db"

def check_error():
    print(f"Checking database: {db_path}")
    if not os.path.exists(db_path):
        print("Database not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT status, error_message, current_agent FROM research_goals")
        goals = cursor.fetchall()
        print("Goals info:")
        for goal in goals:
            print(f"  Status: {goal[0]}")
            print(f"  Error: {goal[1]}")
            print(f"  Current Agent: {goal[2]}")
            
        cursor.execute("SELECT agent_name, status, error_message FROM agent_states")
        states = cursor.fetchall()
        print("\nAgent States:")
        for state in states:
            print(f"  Agent: {state[0]} | Status: {state[1]} | Error: {state[2]}")
            
    finally:
        conn.close()

if __name__ == "__main__":
    check_error()
