import sqlite3
import os

db_path = r"d:\ai\AI UX Researcher Agent\files (6)\AGENTIC-AI-VERIFIED-FIXES\agentic-research-ai-FIXED\backend\data\agentic_research.db"

def reset():
    print(f"Resetting database: {db_path}")
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM research_goals")
        cursor.execute("DELETE FROM agent_states")
        cursor.execute("DELETE FROM checkpoints")
        cursor.execute("DELETE FROM memory_entries")
        cursor.execute("DELETE FROM tool_executions")
        conn.commit()
        print("All tables cleared successfully")
    finally:
        conn.close()

if __name__ == "__main__":
    reset()
