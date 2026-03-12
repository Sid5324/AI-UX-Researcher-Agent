import requests
import time
import json
import sys

BASE_URL = "http://localhost:8000"

def verify_uber_goal():
    print("🚀 Starting Uber Onboarding Improvement Verification...")
    
    # 1. Create Goal
    goal_data = {
        "description": "Improve the onboarding screen of Uber by analyzing user friction, competitor flows, and designing a streamlined PRD and UI mockup.",
        "mode": "demo"
    }
    
    print(f"\n1. Creating goal: {goal_data['description']}...")
    resp = requests.post(f"{BASE_URL}/goals", json=goal_data)
    if resp.status_code not in [200, 201]:
        print(f"❌ Failed to create goal: {resp.status_code} - {resp.text}")
        sys.exit(1)
    
    goal_id = resp.json()["id"]
    print(f"✅ Goal created! ID: {goal_id}")
    
    # 2. Monitor execution
    print("\n2. Monitoring agent execution...")
    start_time = time.time()
    last_status = None
    last_agent = None
    
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
            
        if status == "completed":
            print(f"\n✨ Goal COMPLETED in {round(time.time() - start_time, 1)}s!")
            break
        elif status == "failed":
            print(f"\n❌ Goal FAILED: {data.get('error_message')}")
            sys.exit(1)
            
        time.sleep(5)
    
    if last_status != "completed":
        print("\n❌ Timeout reached.")
        sys.exit(1)
        
    # 3. Print Deliverables
    print("\n3. Verifying Deliverables in Final Output:")
    final_output = data.get("final_output", {})
    findings = data.get("findings", {})
    
    deliverables = {
        "Data Findings": "data_findings" in final_output,
        "Competitor Analysis": "competitor_analysis" in final_output,
        "Product Strategy (PRD)": "product_strategy" in final_output,
        "Design Specs (UI/UX)": "design_specs" in final_output,
        "Validation Results": "validation_results" in final_output
    }
    
    all_present = True
    for name, present in deliverables.items():
        status_icon = "✅" if present else "❌"
        print(f"{status_icon} {name}")
        if not present:
            all_present = False
            
    if all_present:
        print("\n🌟 SUCCESS: All deliverables captured for Uber onboarding goal!")
        print("\n--- PRODUCT STRATEGY PREVIEW ---")
        strategy = final_output.get("product_strategy", {})
        print(json.dumps(strategy, indent=2)[:500] + "...")
    else:
        print("\n❌ FAILED: Some deliverables are missing.")
        sys.exit(1)

if __name__ == "__main__":
    verify_uber_goal()
