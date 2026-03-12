#!/usr/bin/env python3
"""
End-to-End Test for Agentic Research AI Orchestration System
=============================================================

This test verifies the complete flow of the AI orchestration system:
1. Backend health check on port 8000
2. Create research goal via POST /goals API
3. Monitor goal execution by polling GET /goals/{id}
4. Check database directly for agent_states records
5. Test WebSocket connection to /ws/{goal_id}
6. Verify if multiple agents execute in sequence
7. Report what actually works vs what's broken

Usage:
    python test_e2e_orchestration.py

Requirements:
    - Backend running on http://localhost:8000
    - Python 3.10+
    - httpx, websockets, aiosqlite
"""

import asyncio
import json
import sqlite3
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from contextlib import closing

import httpx
import websockets


# =============================================================================
# Configuration
# =============================================================================

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"
# Database path - will be resolved at runtime
DB_PATH_DEFAULT = Path("files (6)/AGENTIC-AI-VERIFIED-FIXES/agentic-research-ai-FIXED/backend/data/agentic_research.db")

# Test goal description
TEST_GOAL = """
Research the market for a new AI-powered fitness tracking app targeting 
professional athletes. Analyze competitor landscape including Whoop, Garmin, 
and Apple Watch fitness features. Gather data on pricing models and user 
satisfaction. Create a comprehensive PRD with feature recommendations and 
initial UI/UX wireframes for the mobile app.
"""

# Polling configuration
POLL_INTERVAL = 2  # seconds
MAX_POLL_TIME = 120  # seconds


# =============================================================================
# Data Classes for Test Results
# =============================================================================

@dataclass
class TestStep:
    name: str
    status: str  # "PASS", "FAIL", "SKIP"
    duration_ms: float
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestReport:
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    steps: List[TestStep] = field(default_factory=list)
    goal_id: Optional[str] = None
    final_goal_status: Optional[str] = None
    agents_executed: List[str] = field(default_factory=list)
    checkpoints_found: List[Dict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def add_step(self, step: TestStep):
        self.steps.append(step)
        self.total_tests += 1
        if step.status == "PASS":
            self.passed += 1
        elif step.status == "FAIL":
            self.failed += 1
        else:
            self.skipped += 1


# =============================================================================
# Test Runner
# =============================================================================

class E2ETestRunner:
    def __init__(self):
        self.report = TestReport()
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
        self.goal_id: Optional[str] = None
        self.ws_messages: List[Dict] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def run_all_tests(self):
        """Execute all E2E tests in sequence"""
        print("=" * 80)
        print("AGENTIC RESEARCH AI - END-TO-END ORCHESTRATION TEST")
        print("=" * 80)
        print()

        start_time = datetime.now(UTC)

        # Test 1: Health Check
        await self.test_health_endpoint()

        # Test 2: System Info
        await self.test_system_info()

        # Test 3: Create Goal
        await self.test_create_goal()

        # Test 4: Poll Goal Status (if goal created)
        if self.goal_id:
            await self.test_poll_goal_status()

        # Test 5: Database Check
        await self.test_database_records()

        # Test 6: WebSocket Connection
        if self.goal_id:
            await self.test_websocket_connection()

        # Test 7: List Goals
        await self.test_list_goals()

        end_time = datetime.now(UTC)
        duration = (end_time - start_time).total_seconds()

        # Print final report
        self.print_report(duration)

    # ==========================================================================
    # Test 1: Health Check
    # ==========================================================================
    async def test_health_endpoint(self):
        step_name = "1. Backend Health Check"
        start = datetime.now(UTC)
        
        try:
            response = await self.client.get("/health")
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            
            if response.status_code == 200:
                data = response.json()
                step = TestStep(
                    name=step_name,
                    status="PASS",
                    duration_ms=duration,
                    message=f"Backend is healthy (DB: {data.get('database')}, AI: {data.get('ai')})",
                    details=data
                )
            else:
                step = TestStep(
                    name=step_name,
                    status="FAIL",
                    duration_ms=duration,
                    message=f"Health check failed with status {response.status_code}",
                    details={"status_code": response.status_code, "response": response.text}
                )
        except Exception as e:
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            step = TestStep(
                name=step_name,
                status="FAIL",
                duration_ms=duration,
                message=f"Health check exception: {str(e)}",
                details={"error": str(e)}
            )
        
        self.report.add_step(step)
        self.print_step(step)

    # ==========================================================================
    # Test 2: System Info
    # ==========================================================================
    async def test_system_info(self):
        step_name = "2. System Info Endpoint"
        start = datetime.now(UTC)
        
        try:
            response = await self.client.get("/info")
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            
            if response.status_code == 200:
                data = response.json()
                step = TestStep(
                    name=step_name,
                    status="PASS",
                    duration_ms=duration,
                    message=f"App: {data.get('app_name')}, Mode: {data.get('mode')}, Tools: {data.get('tools_available')}",
                    details=data
                )
            else:
                step = TestStep(
                    name=step_name,
                    status="FAIL",
                    duration_ms=duration,
                    message=f"Info endpoint failed with status {response.status_code}",
                    details={}
                )
        except Exception as e:
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            step = TestStep(
                name=step_name,
                status="FAIL",
                duration_ms=duration,
                message=f"Info endpoint exception: {str(e)}",
                details={}
            )
        
        self.report.add_step(step)
        self.print_step(step)

    # ==========================================================================
    # Test 3: Create Research Goal
    # ==========================================================================
    async def test_create_goal(self):
        step_name = "3. Create Research Goal"
        start = datetime.now(UTC)
        
        try:
            payload = {
                "description": TEST_GOAL,
                "budget_usd": 5000.0,
                "timeline_days": 14,
                "metadata": {
                    "industry": "Fitness Tech",
                    "target_audience": "Professional Athletes",
                    "test_run": True
                }
            }
            
            response = await self.client.post("/goals", json=payload)
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            
            if response.status_code == 201:
                data = response.json()
                self.goal_id = data.get("id")
                self.report.goal_id = self.goal_id
                
                step = TestStep(
                    name=step_name,
                    status="PASS",
                    duration_ms=duration,
                    message=f"Goal created successfully (ID: {self.goal_id[:8]}..., Status: {data.get('status')})",
                    details=data
                )
            else:
                step = TestStep(
                    name=step_name,
                    status="FAIL",
                    duration_ms=duration,
                    message=f"Create goal failed with status {response.status_code}: {response.text}",
                    details={"status_code": response.status_code}
                )
        except Exception as e:
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            step = TestStep(
                name=step_name,
                status="FAIL",
                duration_ms=duration,
                message=f"Create goal exception: {str(e)}",
                details={}
            )
        
        self.report.add_step(step)
        self.print_step(step)

    # ==========================================================================
    # Test 4: Poll Goal Status
    # ==========================================================================
    async def test_poll_goal_status(self):
        step_name = "4. Poll Goal Execution"
        start = datetime.now(UTC)
        
        if not self.goal_id:
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            step = TestStep(
                name=step_name,
                status="SKIP",
                duration_ms=duration,
                message="Skipped - no goal ID available",
                details={}
            )
            self.report.add_step(step)
            self.print_step(step)
            return
        
        poll_data = []
        last_status = None
        status_changes = []
        agents_seen = set()
        
        try:
            elapsed = 0
            while elapsed < MAX_POLL_TIME:
                response = await self.client.get(f"/goals/{self.goal_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    goal = data.get("goal", {})
                    current_status = goal.get("status")
                    current_agent = goal.get("current_agent")
                    progress = goal.get("progress_percent", 0)
                    
                    # Track status changes
                    if current_status != last_status:
                        status_changes.append({
                            "time": elapsed,
                            "status": current_status,
                            "agent": current_agent,
                            "progress": progress
                        })
                        last_status = current_status
                    
                    # Track agents
                    if current_agent:
                        agents_seen.add(current_agent)
                    
                    # Track agents from agent states
                    for agent in data.get("agents", []):
                        agents_seen.add(agent.get("name"))
                    
                    poll_data.append({
                        "elapsed": elapsed,
                        "status": current_status,
                        "agent": current_agent,
                        "progress": progress
                    })
                    
                    # Stop if goal is complete or failed
                    if current_status in ["completed", "failed", "error"]:
                        break
                
                await asyncio.sleep(POLL_INTERVAL)
                elapsed += POLL_INTERVAL
            
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            self.report.agents_executed = list(agents_seen)
            self.report.final_goal_status = last_status
            
            step = TestStep(
                name=step_name,
                status="PASS",
                duration_ms=duration,
                message=f"Polled for {elapsed}s, final status: {last_status}, agents seen: {len(agents_seen)}",
                details={
                    "poll_count": len(poll_data),
                    "status_changes": status_changes,
                    "agents_seen": list(agents_seen),
                    "final_progress": poll_data[-1].get("progress") if poll_data else 0
                }
            )
            
        except Exception as e:
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            step = TestStep(
                name=step_name,
                status="FAIL",
                duration_ms=duration,
                message=f"Poll status exception: {str(e)}",
                details={}
            )
        
        self.report.add_step(step)
        self.print_step(step)

    # ==========================================================================
    # Test 5: Database Records
    # ==========================================================================
    async def test_database_records(self):
        step_name = "5. Database Records Check"
        start = datetime.now(UTC)
        
        db_results = {
            "goal_found": False,
            "agent_states": [],
            "checkpoints": [],
            "errors": []
        }
        
        try:
            # Check if database file exists
            db_path = DB_PATH_DEFAULT
            if not db_path.exists():
                # Try alternative paths
                alt_paths = [
                    Path("backend/data/agentic_research.db"),
                    Path("data/agentic_research.db"),
                    Path("agentic_research.db"),
                ]
                for alt in alt_paths:
                    if alt.exists():
                        db_path = alt
                        break
            
            if not db_path.exists():
                duration = (datetime.now(UTC) - start).total_seconds() * 1000
                step = TestStep(
                    name=step_name,
                    status="FAIL",
                    duration_ms=duration,
                    message=f"Database file not found at {DB_PATH}",
                    details={"searched_paths": [str(DB_PATH)] + [str(p) for p in alt_paths]}
                )
                self.report.add_step(step)
                self.print_step(step)
                return
            
            # Query database using synchronous sqlite3 in executor
            def query_db():
                results = {"goal": None, "agents": [], "checkpoints": []}
                
                with closing(sqlite3.connect(str(db_path))) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    # Check tables exist
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    results["tables"] = tables
                    
                    if "research_goals" not in tables:
                        results["error"] = "research_goals table not found"
                        return results
                    
                    # Query goal
                    if self.goal_id:
                        cursor.execute(
                            "SELECT * FROM research_goals WHERE id = ?",
                            (self.goal_id,)
                        )
                        row = cursor.fetchone()
                        if row:
                            results["goal"] = dict(row)
                    
                    # Query all goals if no specific goal
                    cursor.execute("SELECT id, status, current_agent, progress_percent FROM research_goals ORDER BY created_at DESC LIMIT 5")
                    results["recent_goals"] = [dict(row) for row in cursor.fetchall()]
                    
                    # Query agent states
                    if "agent_states" in tables:
                        if self.goal_id:
                            cursor.execute(
                                "SELECT * FROM agent_states WHERE goal_id = ? ORDER BY created_at",
                                (self.goal_id,)
                            )
                        else:
                            cursor.execute("SELECT * FROM agent_states ORDER BY created_at DESC LIMIT 10")
                        results["agents"] = [dict(row) for row in cursor.fetchall()]
                    
                    # Query checkpoints
                    if "checkpoints" in tables:
                        if self.goal_id:
                            cursor.execute(
                                "SELECT * FROM checkpoints WHERE goal_id = ? ORDER BY created_at",
                                (self.goal_id,)
                            )
                        else:
                            cursor.execute("SELECT * FROM checkpoints ORDER BY created_at DESC LIMIT 10")
                        results["checkpoints"] = [dict(row) for row in cursor.fetchall()]
                    
                    return results
            
            loop = asyncio.get_event_loop()
            db_data = await loop.run_in_executor(None, query_db)
            
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            
            db_results["tables_found"] = db_data.get("tables", [])
            db_results["recent_goals"] = db_data.get("recent_goals", [])
            db_results["agent_states"] = db_data.get("agents", [])
            db_results["checkpoints"] = db_data.get("checkpoints", [])
            
            self.report.checkpoints_found = db_data.get("checkpoints", [])
            
            agent_count = len(db_results["agent_states"])
            checkpoint_count = len(db_results["checkpoints"])
            goal_count = len(db_results.get("recent_goals", []))
            
            message = f"DB: {goal_count} goals, {agent_count} agent states, {checkpoint_count} checkpoints"
            
            step = TestStep(
                name=step_name,
                status="PASS",
                duration_ms=duration,
                message=message,
                details=db_results
            )
            
        except Exception as e:
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            step = TestStep(
                name=step_name,
                status="FAIL",
                duration_ms=duration,
                message=f"Database check exception: {str(e)}",
                details={"error": str(e)}
            )
        
        self.report.add_step(step)
        self.print_step(step)

    # ==========================================================================
    # Test 6: WebSocket Connection
    # ==========================================================================
    async def test_websocket_connection(self):
        step_name = "6. WebSocket Connection"
        start = datetime.now(UTC)
        
        if not self.goal_id:
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            step = TestStep(
                name=step_name,
                status="SKIP",
                duration_ms=duration,
                message="Skipped - no goal ID available",
                details={}
            )
            self.report.add_step(step)
            self.print_step(step)
            return
        
        ws_messages = []
        ws_connected = False
        
        try:
            # Connect with timeout
            ws_url = f"{WS_URL}/ws/{self.goal_id}"
            
            async with websockets.connect(ws_url, open_timeout=10) as ws:
                ws_connected = True
                
                # Wait for initial connection message
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    ws_messages.append(json.loads(msg))
                except asyncio.TimeoutError:
                    pass
                
                # Send a ping
                await ws.send("ping")
                
                # Wait for response
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    ws_messages.append(json.loads(msg))
                except asyncio.TimeoutError:
                    pass
                
                # Keep connection open briefly to receive any updates
                await asyncio.sleep(2)
                
                # Try to receive any pending messages
                try:
                    while True:
                        msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                        ws_messages.append(json.loads(msg))
                except asyncio.TimeoutError:
                    pass
            
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            
            if ws_connected:
                step = TestStep(
                    name=step_name,
                    status="PASS",
                    duration_ms=duration,
                    message=f"WebSocket connected, received {len(ws_messages)} messages",
                    details={
                        "messages": ws_messages,
                        "url": ws_url
                    }
                )
            else:
                step = TestStep(
                    name=step_name,
                    status="FAIL",
                    duration_ms=duration,
                    message="WebSocket failed to connect",
                    details={}
                )
                
        except Exception as e:
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            step = TestStep(
                name=step_name,
                status="FAIL",
                duration_ms=duration,
                message=f"WebSocket exception: {str(e)}",
                details={"error": str(e)}
            )
        
        self.report.add_step(step)
        self.print_step(step)

    # ==========================================================================
    # Test 7: List Goals
    # ==========================================================================
    async def test_list_goals(self):
        step_name = "7. List Goals Endpoint"
        start = datetime.now(UTC)
        
        try:
            response = await self.client.get("/goals?limit=5")
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            
            if response.status_code == 200:
                data = response.json()
                goal_count = len(data)
                
                step = TestStep(
                    name=step_name,
                    status="PASS",
                    duration_ms=duration,
                    message=f"Retrieved {goal_count} goals",
                    details={"count": goal_count, "goals": data[:3]}
                )
            else:
                step = TestStep(
                    name=step_name,
                    status="FAIL",
                    duration_ms=duration,
                    message=f"List goals failed with status {response.status_code}",
                    details={}
                )
        except Exception as e:
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            step = TestStep(
                name=step_name,
                status="FAIL",
                duration_ms=duration,
                message=f"List goals exception: {str(e)}",
                details={}
            )
        
        self.report.add_step(step)
        self.print_step(step)

    # ==========================================================================
    # Reporting
    # ==========================================================================
    def print_step(self, step: TestStep):
        status_icon = "[PASS]" if step.status == "PASS" else "[FAIL]" if step.status == "FAIL" else "[SKIP]"
        print(f"{status_icon} {step.name}")
        print(f"  Status: {step.status} | Duration: {step.duration_ms:.1f}ms")
        print(f"  {step.message}")
        print()

    def print_report(self, total_duration: float):
        print("=" * 80)
        print("TEST EXECUTION SUMMARY")
        print("=" * 80)
        print()
        print(f"Total Tests:    {self.report.total_tests}")
        print(f"Passed:         {self.report.passed}")
        print(f"Failed:         {self.report.failed}")
        print(f"Skipped:        {self.report.skipped}")
        print(f"Total Duration: {total_duration:.2f}s")
        print()
        
        print("-" * 80)
        print("DETAILED FINDINGS")
        print("-" * 80)
        print()
        
        # Goal Execution Summary
        if self.report.goal_id:
            print(f"Goal ID: {self.report.goal_id}")
            print(f"   Final Status: {self.report.final_goal_status or 'Unknown'}")
            print()
        
        # Agent Execution
        if self.report.agents_executed:
            print(f"Agents Executed ({len(self.report.agents_executed)}):")
            for agent in self.report.agents_executed:
                print(f"   - {agent}")
            print()
        
        # Checkpoints
        if self.report.checkpoints_found:
            print(f"Checkpoints Found ({len(self.report.checkpoints_found)}):")
            for cp in self.report.checkpoints_found[:5]:  # Limit output
                print(f"   - {cp.get('title', 'Untitled')} ({cp.get('status', 'unknown')})")
            print()
        
        # Step-by-step results
        print("-" * 80)
        print("STEP-BY-STEP RESULTS")
        print("-" * 80)
        print()
        
        for i, step in enumerate(self.report.steps, 1):
            status = "[PASS]" if step.status == "PASS" else "[FAIL]" if step.status == "FAIL" else "[SKIP]"
            print(f"{i}. {step.name}")
            print(f"   {status} ({step.duration_ms:.1f}ms)")
            
            # Print key details based on step
            if step.details:
                if "database" in step.name.lower() and "agent_states" in step.details:
                    agents = step.details.get("agent_states", [])
                    if agents:
                        print(f"   Agent States in DB:")
                        for agent in agents:
                            print(f"     - {agent.get('agent_name', 'unknown')}: {agent.get('status', 'unknown')}")
                
                if "poll" in step.name.lower() and "status_changes" in step.details:
                    changes = step.details.get("status_changes", [])
                    if changes:
                        print(f"   Status Changes:")
                        for change in changes:
                            print(f"     [{change.get('time', 0)}s] {change.get('status')} (Agent: {change.get('agent')}, Progress: {change.get('progress')}%)")
                
                if "websocket" in step.name.lower() and "messages" in step.details:
                    messages = step.details.get("messages", [])
                    if messages:
                        print(f"   WebSocket Messages:")
                        for msg in messages:
                            print(f"     - {msg.get('type', 'unknown')}: {msg.get('message', '')[:50]}...")
            
            print()
        
        # What's Working vs Broken
        print("-" * 80)
        print("WORKING vs BROKEN ANALYSIS")
        print("-" * 80)
        print()
        
        working = []
        broken = []
        
        for step in self.report.steps:
            if step.status == "PASS":
                working.append(step.name)
            elif step.status == "FAIL":
                broken.append(f"{step.name}: {step.message}")
        
        print("WORKING:")
        for item in working:
            print(f"   [OK] {item}")
        print()
        
        if broken:
            print("BROKEN/ISSUES:")
            for item in broken:
                print(f"   [ERROR] {item}")
        else:
            print("BROKEN/ISSUES: None - All tests passed!")
        print()
        
        # Multi-Agent Orchestration Assessment
        print("-" * 80)
        print("MULTI-AGENT ORCHESTRATION ASSESSMENT")
        print("-" * 80)
        print()
        
        if len(self.report.agents_executed) >= 2:
            print("[SUCCESS] Multiple agents are executing - Orchestration is working!")
            print(f"   Agents: {', '.join(self.report.agents_executed)}")
        elif len(self.report.agents_executed) == 1:
            print("[WARNING] Only one agent executed - May be sequential or still running")
            print(f"   Agent: {self.report.agents_executed[0]}")
        else:
            print("[ERROR] No agents recorded - Orchestration may not be functioning")
        
        if self.report.final_goal_status == "completed":
            print("[SUCCESS] Goal completed successfully")
        elif self.report.final_goal_status == "failed":
            print("[ERROR] Goal failed")
        elif self.report.final_goal_status == "running":
            print("[INFO] Goal is still running (may need more time)")
        else:
            print(f"[WARNING] Goal status: {self.report.final_goal_status or 'Unknown'}")
        
        print()
        print("=" * 80)


# =============================================================================
# Main Entry Point
# =============================================================================

async def main():
    print("Starting E2E Test...")
    print(f"Target: {BASE_URL}")
    print(f"Database: {DB_PATH_DEFAULT}")
    print()
    
    async with E2ETestRunner() as runner:
        await runner.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        sys.exit(1)
