import requests
import time
import json
import sys

BASE_URL = "http://localhost:8000"

def verify_full_stack():
    print("🚀 Starting RIGOROUS Multi-Agent Flow Verification...")
    
    # 1. Create Goal
    goal_data = {
        "description": "END-TO-END TEST: Analyze competitor landscape for AI researcher agents and design a better UI for the signup flow with a validation experiment.",
        "mode": "demo"
    }
    
    print(f"\n1. Creating goal: {goal_data['description'][:50]}...")
    resp = requests.post(f"{BASE_URL}/goals", json=goal_data)
    if resp.status_code not in [200, 201]:
        print(f"❌ Failed to create goal: {resp.status_code} - {resp.text}")
        sys.exit(1)
    
    goal_id = resp.json()["id"]
    print(f"✅ Goal created! ID: {goal_id}")
    
    # 2. Monitor with timeout
    print("\n2. Monitoring agent execution (Max 10 minutes)...")
    start_time = time.time()
    last_status = None
    last_agent = None
    
    expected_agents = ["data_agent", "competitor_agent", "prd_agent", "validation_agent", "uiux_agent"]
    completed_agents = []
    
    while time.time() - start_time < 600: # 10 mins
        resp = requests.get(f"{BASE_URL}/goals/{goal_id}")
        if resp.status_code != 200:
            print(f"❌ Error fetching goal: {resp.text}")
            sys.exit(1)
            
        data = resp.json()["goal"]
        status = data["status"]
        current_agent = data.get("current_agent")
        
        if status != last_status or current_agent != last_agent:
            print(f"🔄 Status: {status} | Current Agent: {current_agent} | Progress: {data.get('progress_percent', 0)}%")
            last_status = status
            last_agent = current_agent
            
        # Track completed agents
        for agent in resp.json().get("agents", []):
            if agent["status"] == "completed" and agent["name"] not in completed_agents:
                completed_agents.append(agent["name"])
                print(f"✅ Agent {agent['name']} successfully completed!")
        
        if status == "completed":
            print(f"\n✨ Goal COMPLETED in {round(time.time() - start_time, 1)}s!")
            break
        elif status == "failed":
            print(f"\n❌ Goal FAILED: {data.get('error_message')}")
            sys.exit(1)
            
        time.sleep(5)
    
    if last_status != "completed":
        print("\n❌ Timeout reached without completion.")
        sys.exit(1)
        
    # 3. Verify Deliverables
    print("\n3. Verifying Deliverables...")
    final_output = data.get("final_output", {})
    
    required_keys = ["data_findings", "product_strategy", "design_specs", "competitor_analysis", "validation_results"]
    missing_keys = [k for k in required_keys if not final_output.get(k)]
    
    if missing_keys:
        print(f"❌ Missing deliverables in final_output: {', '.join(missing_keys)}")
        sys.exit(1)
    else:
        print(f"✅ All {len(required_keys)} deliverables found in final_output!")
        
    # Verify individual agent status in DB
    agent_states = resp.json().get("agents", [])
    for agent_name in expected_agents:
        state = next((a for a in agent_states if a["name"] == agent_name), None)
        if not state or state["status"] != "completed":
            print(f"❌ Agent {agent_name} state is NOT completed (found: {state['status'] if state else 'None'})")
            sys.exit(1)
    
    print("\n🌟 RIGOROUS VERIFICATION SUCCESSFUL: Full 5-agent stack completed with all deliverables.")

if __name__ == "__main__":
    verify_full_stack()
