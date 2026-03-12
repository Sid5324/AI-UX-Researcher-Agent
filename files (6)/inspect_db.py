import sqlite3
import os

db_path = r"d:\ai\AI UX Researcher Agent\files (6)\AGENTIC-AI-VERIFIED-FIXES\agentic-research-ai-FIXED\backend\data\agentic_research.db"

def inspect():
    print(f"Inspecting database: {db_path}")
    if not os.path.exists(db_path):
        print("Database not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n--- research_goals ---")
        cursor.execute("PRAGMA table_info(research_goals)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")

        print("\n--- checkpoints ---")
        cursor.execute("PRAGMA table_info(checkpoints)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
            
    finally:
        conn.close()

if __name__ == "__main__":
    inspect()
