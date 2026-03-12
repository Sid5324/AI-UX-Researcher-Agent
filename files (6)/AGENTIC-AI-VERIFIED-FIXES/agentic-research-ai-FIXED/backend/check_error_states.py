import sqlite3
import json

try:
    conn = sqlite3.connect('d:/ai/AI UX Researcher Agent/files (6)/AGENTIC-AI-VERIFIED-FIXES/agentic-research-ai-FIXED/backend/data/agentic_research.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get latest failed goal
    c.execute("SELECT id, description, error_message FROM research_goals WHERE status='failed' ORDER BY created_at DESC LIMIT 1")
    goal = c.fetchone()
    
    if goal:
        print(f"Goal ID: {goal['id']}")
        print(f"Goal Error: {goal['error_message']}")
        
        c.execute("SELECT agent_name, status, error_message FROM agent_states WHERE goal_id=? AND status='failed'", (goal['id'],))
        agents = c.fetchall()
        for a in agents:
            print(f"Agent '{a['agent_name']}' Error: {a['error_message']}")
    else:
        print("No failed goals found.")
except Exception as e:
    print(f"DB Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()
