import sqlite3
import os
import json

db_path = r"d:\ai\AI UX Researcher Agent\files (6)\AGENTIC-AI-VERIFIED-FIXES\agentic-research-ai-FIXED\backend\data\agentic_research.db"

def check_outputs():
    print(f"Checking database: {db_path}")
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, status, findings, final_output FROM research_goals")
        goals = cursor.fetchall()
        for goal in goals:
            print(f"\nGoal ID: {goal[0]}")
            print(f"  Status: {goal[1]}")
            print(f"  Findings: {bool(goal[2])}")
            if goal[2]:
                print(f"    Sample: {str(goal[2])[:100]}...")
            print(f"  Final Output: {bool(goal[3])}")
            if goal[3]:
                print(f"    Sample: {str(goal[3])[:100]}...")
            
    finally:
        conn.close()

if __name__ == "__main__":
    check_outputs()
