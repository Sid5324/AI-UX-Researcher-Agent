import sqlite3
import os

db_path = r"d:\ai\AI UX Researcher Agent\files (6)\AGENTIC-AI-VERIFIED-FIXES\agentic-research-ai-FIXED\backend\data\agentic_research.db"

def migrate():
    print(f"Migrating database: {db_path}")
    if not os.path.exists(db_path):
        print("Database not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check for agent_reasoning
        cursor.execute("PRAGMA table_info(checkpoints)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "agent_reasoning" not in columns:
            cursor.execute("ALTER TABLE checkpoints ADD COLUMN agent_reasoning TEXT")
            print("Added 'agent_reasoning' to checkpoints table")
        else:
            print("'agent_reasoning' already exists in checkpoints table")

        conn.commit()
        print("Migration successful")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
