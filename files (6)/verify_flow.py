import asyncio
import httpx
import json
import socket
import sys
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
EXAMPLE_GOAL = {
    "description": "Analyze the competitor landscape for AI researcher agents, collect user feedback on current pain points, and design a superior PRD and UI/UX for a new agentic platform. Validate the strategy with statistical projections.",
    "budget_usd": 5000,
    "timeline_days": 14,
    "mode": "demo"  # Use demo mode for faster verification without needing actual API keys
}

async def check_backend_running():
    """Check if the backend server is reachable on port 8000"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/")
            return response.status_code == 200
    except Exception:
        return False

async def verify_flow():
    print("🚀 Starting Multi-Agent Flow Verification...")
    
    if not await check_backend_running():
        print("❌ Error: Backend server not running on http://localhost:8000")
        print("Please start it using: python -m uvicorn src.api.main:app --reload")
        return

    async with httpx.AsyncClient(timeout=120.0) as client:
        # 1. Create Goal
        print(f"\n1. Creating goal: {EXAMPLE_GOAL['description'][:50]}...")
        resp = await client.post(f"{BASE_URL}/goals", json=EXAMPLE_GOAL)
        if resp.status_code != 201:
            print(f"❌ Failed to create goal: {resp.text}")
            return
        
        goal_data = resp.json()
        goal_id = goal_data["id"]
        print(f"✅ Goal created! ID: {goal_id}")

        # 2. Monitor Progress
        print("\n2. Monitoring agent execution (this may take a minute)...")
        last_agent = None
        start_time = time.time()
        
        while True:
            # Check status
            status_resp = await client.get(f"{BASE_URL}/goals/{goal_id}")
            if status_resp.status_code != 200:
                print(f"❌ Failed to get goal status: {status_resp.text}")
                break
            
            data = status_resp.json()
            status = data["goal"]["status"]
            progress = data["goal"]["progress_percent"]
            current_agent = data["goal"].get("current_agent")
            
            if current_agent != last_agent:
                print(f"🔄 Agent Switch: {last_agent} -> {current_agent} (Progress: {progress}%)")
                last_agent = current_agent
            
            if status == "completed":
                print(f"\n✅ Goal COMPLETED in {time.time() - start_time:.1f}s!")
                break
            elif status == "failed":
                print(f"\n❌ Goal FAILED: {data['goal'].get('error_message')}")
                break
            elif status == "checkpoint":
                print(f"⚠️ Agent reached a CHECKPOINT. Approving automatically for test...")
                # Find pending checkpoints
                checkpoints = data.get("checkpoints", [])
                for cp in checkpoints:
                    if cp["status"] == "pending":
                        approve_resp = await client.post(
                            f"{BASE_URL}/goals/{goal_id}/approve",
                            json={"decision": "approved", "feedback": "Proceed with the test."}
                        )
                        print(f"✅ Checkpoint {cp['id']} approved.")
            
            # Print agent states
            agents = data.get("agents", [])
            completed_agents = [a["name"] for a in agents if a["status"] == "completed"]
            if completed_agents:
                # Use a carriage return to keep it clean if many updates
                sys.stdout.write(f"\rDONE Agents: {', '.join(completed_agents)} | Total Progress: {progress}%")
                sys.stdout.flush()

            await asyncio.sleep(2)
            
            if time.time() - start_time > 300: # 5 min timeout
                print("\n❌ Timeout: Verification took too long.")
                break

        # 3. Verify Output
        print("\n\n3. Verifying Final Output...")
        # Check if goal reached a terminal state
        final_resp = await client.get(f"{BASE_URL}/goals/{goal_id}")
        if final_resp.status_code != 200:
            print(f"❌ Could not retrieve final goal state: {final_resp.text}")
            return
            
        final_data_container = final_resp.json()
        goal_record = final_data_container.get("goal", {})
        final_data = goal_record.get("final_output", {}) or goal_record.get("findings", {})
        
        if final_data:
            print("✅ Final Output Found!")
            # print(json.dumps(final_data, indent=2)[:500] + "...")
            
            # Check for keys from different agents
            expected_keys = ["data_findings", "product_strategy", "design_specs", "competitor_analysis"]
            found_keys = [k for k in expected_keys if k in final_data]
            print(f"📊 Captured Agent Outputs: {', '.join(found_keys)}")
            
            if len(found_keys) >= 3:
                print("\n🌟 VERIFICATION SUCCESSFUL: multi-agent data flow is working correctly.")
            else:
                print("\n⚠️ VERIFICATION INCOMPLETE: Some agent outputs were missing from final state.")
        else:
            print("❌ No final output found in goal record.")

if __name__ == "__main__":
    asyncio.run(verify_flow())
