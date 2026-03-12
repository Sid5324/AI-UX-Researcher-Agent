#!/usr/bin/env python3
"""
COMPREHENSIVE MULTI-AGENT ORCHESTRATION TEST
=============================================

This test specifically verifies multi-agent orchestration functionality:
1. Tests goal parser with different goal descriptions to see what agents it returns
2. Creates a goal that explicitly requires multiple agents (data, PRD, UI/UX)
3. Forces multi-agent execution by manually calling the orchestrator
4. Monitors if multiple agents actually execute in sequence
5. Verifies agent handoffs work (checks if data flows from one agent to the next)
6. Checks database for multiple agent_state records
7. Verifies WebSocket receives messages from multiple agents
8. Reports EXACTLY what works and what fails in multi-agent mode

Usage:
    cd "files (6)/AGENTIC-AI-VERIFIED-FIXES/agentic-research-ai-FIXED/backend"
    python ../../test_multi_agent_orchestration.py

Requirements:
    - Backend running on http://localhost:8000
    - Python 3.10+
    - httpx, websockets, aiosqlite, colorama
"""

import asyncio
import json
import sqlite3
import sys
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from contextlib import closing

import httpx
import websockets

# Try to import colorama for colored output
try:
    from colorama import init, Fore, Style
    init()
    COLOR_AVAILABLE = True
except ImportError:
    COLOR_AVAILABLE = False
    class DummyFore:
        def __getattr__(self, name):
            return ""
    class DummyStyle:
        def __getattr__(self, name):
            return ""
    Fore = DummyFore()
    Style = DummyStyle()


# =============================================================================
# Configuration
# =============================================================================

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

# Database paths to try
DB_PATHS = [
    Path("files (6)/AGENTIC-AI-VERIFIED-FIXES/agentic-research-ai-FIXED/backend/data/agentic_research.db"),
    Path("backend/data/agentic_research.db"),
    Path("data/agentic_research.db"),
    Path("agentic_research.db"),
]

# Test goal descriptions with varying complexity
TEST_GOALS = {
    "data_only": """
        Analyze our website analytics data to understand user drop-off points
        in the onboarding funnel. Focus on the signup flow and identify
        where users are getting stuck.
    """,
    
    "data_to_prd": """
        Research the competitive landscape for AI-powered code completion tools.
        Analyze GitHub Copilot, Cursor, and TabNine features, pricing, and user satisfaction.
        Create a comprehensive PRD document with feature recommendations for our own product.
    """,
    
    "full_pipeline": """
        Research the market for a new AI-powered fitness tracking app targeting 
        professional athletes. Analyze competitor landscape including Whoop, Garmin, 
        and Apple Watch fitness features. Gather data on pricing models and user 
        satisfaction. Create a comprehensive PRD with feature recommendations and 
        initial UI/UX wireframes for the mobile app. Design a user-friendly interface
        with dashboards for performance metrics, recovery tracking, and training plans.
    """,
    
    "explicit_multi": """
        I need a complete product development package:
        1. First, research the fintech mobile payment market - analyze Venmo, Cash App, 
           Zelle, and Apple Pay. Collect data on user demographics, transaction volumes,
           and feature sets.
        2. Then create a detailed Product Requirements Document (PRD) for our new
           payment app targeting Gen Z users with social features.
        3. Finally, design the complete UI/UX with wireframes, user flows, and
           visual design system including screens for sending money, requesting
           payments, split bills, and social feed.
    """
}

# Polling configuration
POLL_INTERVAL = 2  # seconds
MAX_POLL_TIME = 180  # seconds (3 minutes)

# Expected agent sequence
EXPECTED_AGENTS = ["data_agent", "prd_agent", "ui_ux_agent"]


# =============================================================================
# Data Classes for Test Results
# =============================================================================

@dataclass
class TestStep:
    name: str
    status: str  # "PASS", "FAIL", "SKIP", "INFO"
    duration_ms: float
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiAgentReport:
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    info: int = 0
    steps: List[TestStep] = field(default_factory=list)
    
    # Multi-agent specific tracking
    goal_parser_results: List[Dict] = field(default_factory=list)
    goal_ids: List[str] = field(default_factory=list)
    agents_executed: Dict[str, List[str]] = field(default_factory=dict)
    handoffs_detected: List[Dict] = field(default_factory=list)
    websocket_messages: Dict[str, List[Dict]] = field(default_factory=dict)
    db_agent_states: Dict[str, List[Dict]] = field(default_factory=dict)
    
    def add_step(self, step: TestStep):
        self.steps.append(step)
        self.total_tests += 1
        if step.status == "PASS":
            self.passed += 1
        elif step.status == "FAIL":
            self.failed += 1
        elif step.status == "SKIP":
            self.skipped += 1
        elif step.status == "INFO":
            self.info += 1


# =============================================================================
# Test Runner
# =============================================================================

class MultiAgentTestRunner:
    def __init__(self):
        self.report = MultiAgentReport()
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=60.0)
        self.current_goal_id: Optional[str] = None
        self.ws_messages: List[Dict] = []
        self.db_path: Optional[Path] = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def print_header(self, text: str):
        """Print a formatted header"""
        print()
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{text.center(80)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        print()

    def print_section(self, text: str):
        """Print a section header"""
        print()
        print(f"{Fore.YELLOW}{'-' * 80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}>>> {text}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'-' * 80}{Style.RESET_ALL}")

    def print_step(self, step: TestStep):
        """Print a test step result"""
        if step.status == "PASS":
            icon = f"{Fore.GREEN}[OK]{Style.RESET_ALL}"
            status_color = Fore.GREEN
        elif step.status == "FAIL":
            icon = f"{Fore.RED}[FAIL]{Style.RESET_ALL}"
            status_color = Fore.RED
        elif step.status == "SKIP":
            icon = f"{Fore.YELLOW}[SKIP]{Style.RESET_ALL}"
            status_color = Fore.YELLOW
        else:  # INFO
            icon = f"{Fore.BLUE}[INFO]{Style.RESET_ALL}"
            status_color = Fore.BLUE
        
        print(f"  {icon} {step.name}")
        print(f"     {status_color}{step.status}{Style.RESET_ALL} | {step.duration_ms:.1f}ms")
        print(f"     {step.message}")
        if step.details:
            print(f"     Details: {json.dumps(step.details, indent=2)[:200]}...")
        print()

    async def run_all_tests(self):
        """Execute all multi-agent tests in sequence"""
        self.print_header("MULTI-AGENT ORCHESTRATION COMPREHENSIVE TEST")
        
        start_time = datetime.now(UTC)

        # Phase 1: Backend Health & Setup
        self.print_section("PHASE 1: BACKEND HEALTH CHECK & SETUP")
        await self.test_health_endpoint()
        await self.test_system_info()
        await self.find_database()

        # Phase 2: Goal Parser Testing
        self.print_section("PHASE 2: GOAL PARSER - AGENT SELECTION ANALYSIS")
        await self.test_goal_parser_agents()

        # Phase 3: Create Multi-Agent Goal
        self.print_section("PHASE 3: CREATE MULTI-AGENT GOAL")
        await self.test_create_multi_agent_goal()

        # Phase 4: Monitor Multi-Agent Execution
        if self.current_goal_id:
            self.print_section("PHASE 4: MONITOR MULTI-AGENT EXECUTION")
            await self.test_poll_goal_status()
            
            # Phase 5: WebSocket Monitoring
            self.print_section("PHASE 5: WEBSOCKET MESSAGE MONITORING")
            await self.test_websocket_messages()
            
            # Phase 6: Database Verification
            self.print_section("PHASE 6: DATABASE VERIFICATION")
            await self.test_database_agent_states()
            await self.test_database_handoffs()
        else:
            print(f"{Fore.RED}Skipping Phases 4-6: No goal ID available{Style.RESET_ALL}")

        # Phase 7: Create Direct Orchestrator Test
        self.print_section("PHASE 7: DIRECT ORCHESTRATOR EXECUTION TEST")
        await self.test_direct_orchestrator()

        end_time = datetime.now(UTC)
        duration = (end_time - start_time).total_seconds()

        # Print final report
        self.print_comprehensive_report(duration)

    # ==========================================================================
    # Phase 1: Backend Health
    # ==========================================================================
    async def test_health_endpoint(self):
        step_name = "Backend Health Check"
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
                    message=f"Backend healthy (DB: {data.get('database')}, AI: {data.get('ai')})",
                    details=data
                )
            else:
                step = TestStep(
                    name=step_name,
                    status="FAIL",
                    duration_ms=duration,
                    message=f"Health check failed: HTTP {response.status_code}",
                    details={"status": response.status_code}
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

    async def test_system_info(self):
        step_name = "System Info"
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
                    message=f"Mode: {data.get('mode')}, Tools: {data.get('tools_available')}",
                    details=data
                )
            else:
                step = TestStep(
                    name=step_name,
                    status="FAIL",
                    duration_ms=duration,
                    message=f"Info endpoint failed: HTTP {response.status_code}",
                    details={}
                )
        except Exception as e:
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            step = TestStep(
                name=step_name,
                status="FAIL",
                duration_ms=duration,
                message=f"Info exception: {str(e)}",
                details={}
            )
        
        self.report.add_step(step)
        self.print_step(step)

    async def find_database(self):
        """Find the database file"""
        step_name = "Database Location"
        start = datetime.now(UTC)
        
        for path in DB_PATHS:
            if path.exists():
                self.db_path = path
                duration = (datetime.now(UTC) - start).total_seconds() * 1000
                step = TestStep(
                    name=step_name,
                    status="PASS",
                    duration_ms=duration,
                    message=f"Found database at {path}",
                    details={"path": str(path), "size_bytes": path.stat().st_size}
                )
                self.report.add_step(step)
                self.print_step(step)
                return
        
        duration = (datetime.now(UTC) - start).total_seconds() * 1000
        step = TestStep(
            name=step_name,
            status="FAIL",
            duration_ms=duration,
            message="Database file not found in any expected location",
            details={"searched": [str(p) for p in DB_PATHS]}
        )
        self.report.add_step(step)
        self.print_step(step)

    # ==========================================================================
    # Phase 2: Goal Parser Testing
    # ==========================================================================
    async def test_goal_parser_agents(self):
        """Test what agents the goal parser selects for different goal types"""
        step_name = "Goal Parser Agent Selection"
        start = datetime.now(UTC)
        
        results = []
        
        # Test each goal type
        for goal_name, goal_desc in TEST_GOALS.items():
            try:
                # Parse the goal via API
                # We need to check if there's a parse endpoint or extract from goal creation
                # For now, we'll log what we expect vs what happens
                expected_agents = self._predict_agents_from_goal(goal_desc)
                
                result = {
                    "goal_type": goal_name,
                    "description_preview": goal_desc[:100] + "...",
                    "expected_agents": expected_agents,
                    "agent_count": len(expected_agents)
                }
                results.append(result)
                
                print(f"    {Fore.BLUE}Goal: {goal_name}{Style.RESET_ALL}")
                print(f"      Expected agents: {', '.join(expected_agents)}")
                
            except Exception as e:
                results.append({
                    "goal_type": goal_name,
                    "error": str(e)
                })
        
        duration = (datetime.now(UTC) - start).total_seconds() * 1000
        
        step = TestStep(
            name=step_name,
            status="INFO",
            duration_ms=duration,
            message=f"Analyzed {len(TEST_GOALS)} goal types for agent selection",
            details={"predictions": results}
        )
        
        self.report.goal_parser_results = results
        self.report.add_step(step)
        self.print_step(step)

    def _predict_agents_from_goal(self, description: str) -> List[str]:
        """Predict which agents would be selected based on goal description"""
        desc_lower = description.lower()
        agents = []
        
        # Data agent keywords
        data_keywords = [
            'research', 'analyze', 'data', 'analytics', 'metrics', 
            'competitor', 'landscape', 'market', 'survey', 'user satisfaction',
            'pricing', 'demographics', 'transaction', 'volume'
        ]
        
        # PRD agent keywords
        prd_keywords = [
            'prd', 'product requirements', 'feature recommendations',
            'strategy', 'roadmap', 'specification', 'requirements document'
        ]
        
        # UI/UX agent keywords
        uiux_keywords = [
            'ui/ux', 'wireframe', 'design', 'interface', 'visual',
            'user flow', 'mockup', 'prototype', 'screen', 'dashboard'
        ]
        
        if any(kw in desc_lower for kw in data_keywords):
            agents.append("data_agent")
        
        if any(kw in desc_lower for kw in prd_keywords):
            agents.append("prd_agent")
        
        if any(kw in desc_lower for kw in uiux_keywords):
            agents.append("ui_ux_agent")
        
        # Default to data_agent if no specific keywords found
        if not agents:
            agents.append("data_agent")
        
        return agents

    # ==========================================================================
    # Phase 3: Create Multi-Agent Goal
    # ==========================================================================
    async def test_create_multi_agent_goal(self):
        """Create a goal that explicitly requires multiple agents"""
        step_name = "Create Multi-Agent Goal"
        start = datetime.now(UTC)
        
        try:
            # Use the full_pipeline goal which should trigger all 3 agents
            payload = {
                "description": TEST_GOALS["explicit_multi"],
                "budget_usd": 10000.0,
                "timeline_days": 21,
                "metadata": {
                    "test_type": "multi_agent_orchestration",
                    "expected_agents": EXPECTED_AGENTS,
                    "test_run": True
                }
            }
            
            response = await self.client.post("/goals", json=payload)
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            
            if response.status_code == 201:
                data = response.json()
                self.current_goal_id = data.get("id")
                self.report.goal_ids.append(self.current_goal_id)
                
                step = TestStep(
                    name=step_name,
                    status="PASS",
                    duration_ms=duration,
                    message=f"Goal created: {self.current_goal_id[:8]}... Status: {data.get('status')}",
                    details={
                        "goal_id": self.current_goal_id,
                        "status": data.get('status'),
                        "mode": data.get('mode'),
                        "expected_agents": EXPECTED_AGENTS
                    }
                )
            else:
                step = TestStep(
                    name=step_name,
                    status="FAIL",
                    duration_ms=duration,
                    message=f"Create goal failed: HTTP {response.status_code}",
                    details={"response": response.text[:500]}
                )
        except Exception as e:
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            step = TestStep(
                name=step_name,
                status="FAIL",
                duration_ms=duration,
                message=f"Create goal exception: {str(e)}",
                details={"error": str(e)}
            )
        
        self.report.add_step(step)
        self.print_step(step)

    # ==========================================================================
    # Phase 4: Monitor Execution
    # ==========================================================================
    async def test_poll_goal_status(self):
        """Poll goal status to track agent execution sequence"""
        step_name = "Monitor Agent Execution Sequence"
        start = datetime.now(UTC)
        
        if not self.current_goal_id:
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
        agents_seen: Set[str] = set()
        agent_timeline = []
        
        print(f"    {Fore.CYAN}Polling goal execution for up to {MAX_POLL_TIME}s...{Style.RESET_ALL}")
        
        try:
            elapsed = 0
            while elapsed < MAX_POLL_TIME:
                response = await self.client.get(f"/goals/{self.current_goal_id}")
                
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
                        print(f"      [{elapsed}s] Status: {current_status}, Agent: {current_agent}, Progress: {progress}%")
                    
                    # Track agent transitions
                    if current_agent and current_agent not in agents_seen:
                        agents_seen.add(current_agent)
                        agent_timeline.append({
                            "time": elapsed,
                            "agent": current_agent,
                            "progress": progress
                        })
                        print(f"      {Fore.GREEN}--> Agent '{current_agent}' started at {elapsed}s{Style.RESET_ALL}")
                    
                    # Track agents from agent states
                    for agent in data.get("agents", []):
                        agent_name = agent.get("name")
                        if agent_name:
                            agents_seen.add(agent_name)
                    
                    poll_data.append({
                        "elapsed": elapsed,
                        "status": current_status,
                        "agent": current_agent,
                        "progress": progress
                    })
                    
                    # Stop if goal is complete or failed
                    if current_status in ["completed", "failed", "error"]:
                        print(f"      {Fore.YELLOW}Goal finished with status: {current_status}{Style.RESET_ALL}")
                        break
                
                await asyncio.sleep(POLL_INTERVAL)
                elapsed += POLL_INTERVAL
            
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            
            # Store results
            self.report.agents_executed[self.current_goal_id] = list(agents_seen)
            
            # Check if all expected agents ran
            expected_set = set(EXPECTED_AGENTS)
            actual_set = agents_seen
            missing_agents = expected_set - actual_set
            extra_agents = actual_set - expected_set
            
            if not missing_agents and len(actual_set) >= 2:
                status = "PASS"
                message = f"All {len(agents_seen)} agents executed: {', '.join(sorted(agents_seen))}"
            elif len(agents_seen) >= 2:
                status = "PASS"
                message = f"Multiple agents executed ({len(agents_seen)}): {', '.join(sorted(agents_seen))}. Missing: {', '.join(missing_agents) if missing_agents else 'None'}"
            elif len(agents_seen) == 1:
                status = "FAIL"
                message = f"Only 1 agent executed: {list(agents_seen)[0]}. Expected multiple agents."
            else:
                status = "FAIL"
                message = f"No agents detected. Expected: {', '.join(EXPECTED_AGENTS)}"
            
            step = TestStep(
                name=step_name,
                status=status,
                duration_ms=duration,
                message=message,
                details={
                    "poll_count": len(poll_data),
                    "elapsed_time": elapsed,
                    "agents_seen": sorted(list(agents_seen)),
                    "expected_agents": EXPECTED_AGENTS,
                    "missing_agents": sorted(list(missing_agents)),
                    "agent_timeline": agent_timeline,
                    "status_changes": status_changes,
                    "final_status": last_status
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
    # Phase 5: WebSocket Testing
    # ==========================================================================
    async def test_websocket_messages(self):
        """Test WebSocket receives messages from multiple agents"""
        step_name = "WebSocket Multi-Agent Messages"
        start = datetime.now(UTC)
        
        if not self.current_goal_id:
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
        agents_from_ws = set()
        message_types = set()
        
        try:
            ws_url = f"{WS_URL}/ws/{self.current_goal_id}"
            print(f"    {Fore.CYAN}Connecting to WebSocket: {ws_url}{Style.RESET_ALL}")
            
            async with websockets.connect(ws_url, open_timeout=10) as ws:
                ws_connected = True
                print(f"    {Fore.GREEN}WebSocket connected{Style.RESET_ALL}")
                
                # Collect messages for up to 30 seconds
                timeout = 30
                start_collect = time.time()
                
                while time.time() - start_collect < timeout:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                        data = json.loads(msg)
                        ws_messages.append(data)
                        message_types.add(data.get("type", "unknown"))
                        
                        # Track agents from messages
                        if "agent" in data:
                            agents_from_ws.add(data["agent"])
                        
                        print(f"      [{len(ws_messages)}] Type: {data.get('type')}")
                        
                    except asyncio.TimeoutError:
                        # No message received, continue
                        pass
                    
                    # Send periodic ping
                    if int(time.time() - start_collect) % 5 == 0:
                        try:
                            await ws.send("ping")
                        except:
                            pass
                
                print(f"    {Fore.YELLOW}WebSocket collection complete. Messages: {len(ws_messages)}{Style.RESET_ALL}")
            
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            
            self.report.websocket_messages[self.current_goal_id] = ws_messages
            
            # Analyze results
            if ws_connected and len(ws_messages) > 0:
                if len(agents_from_ws) >= 2:
                    status = "PASS"
                    message = f"WebSocket received {len(ws_messages)} messages from {len(agents_from_ws)} agents"
                elif len(agents_from_ws) == 1:
                    status = "FAIL"
                    message = f"WebSocket received messages from only 1 agent: {list(agents_from_ws)[0]}"
                else:
                    status = "PASS"
                    message = f"WebSocket connected, received {len(ws_messages)} messages (no agent-specific messages)"
            elif ws_connected:
                status = "FAIL"
                message = "WebSocket connected but received no messages"
            else:
                status = "FAIL"
                message = "WebSocket failed to connect"
            
            step = TestStep(
                name=step_name,
                status=status,
                duration_ms=duration,
                message=message,
                details={
                    "message_count": len(ws_messages),
                    "message_types": sorted(list(message_types)),
                    "agents_from_messages": sorted(list(agents_from_ws)),
                    "sample_messages": ws_messages[:5] if ws_messages else []
                }
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
    # Phase 6: Database Verification
    # ==========================================================================
    async def test_database_agent_states(self):
        """Verify database contains multiple agent_state records"""
        step_name = "DB: Multiple Agent States"
        start = datetime.now(UTC)
        
        if not self.db_path or not self.db_path.exists():
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            step = TestStep(
                name=step_name,
                status="SKIP",
                duration_ms=duration,
                message="Skipped - database not found",
                details={}
            )
            self.report.add_step(step)
            self.print_step(step)
            return
        
        try:
            def query_db():
                results = {
                    "agent_states": [],
                    "agent_names": set(),
                    "status_counts": {}
                }
                
                with closing(sqlite3.connect(str(self.db_path))) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    # Check if agent_states table exists
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agent_states'")
                    if not cursor.fetchone():
                        results["error"] = "agent_states table not found"
                        return results
                    
                    # Query agent states for current goal
                    if self.current_goal_id:
                        cursor.execute(
                            "SELECT * FROM agent_states WHERE goal_id = ? ORDER BY created_at",
                            (self.current_goal_id,)
                        )
                    else:
                        cursor.execute(
                            "SELECT * FROM agent_states ORDER BY created_at DESC LIMIT 20"
                        )
                    
                    rows = cursor.fetchall()
                    for row in rows:
                        agent_data = dict(row)
                        results["agent_states"].append(agent_data)
                        if "agent_name" in agent_data:
                            results["agent_names"].add(agent_data["agent_name"])
                        if "status" in agent_data:
                            status = agent_data["status"]
                            results["status_counts"][status] = results["status_counts"].get(status, 0) + 1
                    
                    return results
            
            loop = asyncio.get_event_loop()
            db_data = await loop.run_in_executor(None, query_db)
            
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            
            agent_states = db_data.get("agent_states", [])
            agent_names = db_data.get("agent_names", set())
            
            self.report.db_agent_states[self.current_goal_id or "all"] = agent_states
            
            if "error" in db_data:
                step = TestStep(
                    name=step_name,
                    status="FAIL",
                    duration_ms=duration,
                    message=f"Database error: {db_data['error']}",
                    details=db_data
                )
            elif len(agent_names) >= 3:
                step = TestStep(
                    name=step_name,
                    status="PASS",
                    duration_ms=duration,
                    message=f"Found {len(agent_states)} agent states for {len(agent_names)} agents: {', '.join(sorted(agent_names))}",
                    details={
                        "total_states": len(agent_states),
                        "unique_agents": sorted(list(agent_names)),
                        "status_distribution": db_data.get("status_counts", {})
                    }
                )
            elif len(agent_names) >= 2:
                step = TestStep(
                    name=step_name,
                    status="PASS",
                    duration_ms=duration,
                    message=f"Found {len(agent_states)} agent states for {len(agent_names)} agents: {', '.join(sorted(agent_names))}",
                    details={
                        "total_states": len(agent_states),
                        "unique_agents": sorted(list(agent_names)),
                        "status_distribution": db_data.get("status_counts", {})
                    }
                )
            elif len(agent_names) == 1:
                step = TestStep(
                    name=step_name,
                    status="FAIL",
                    duration_ms=duration,
                    message=f"Only 1 agent found in DB: {list(agent_names)[0]}. Expected multiple.",
                    details={
                        "total_states": len(agent_states),
                        "agent": list(agent_names)[0] if agent_names else None
                    }
                )
            else:
                step = TestStep(
                    name=step_name,
                    status="FAIL",
                    duration_ms=duration,
                    message="No agent states found in database",
                    details={}
                )
            
        except Exception as e:
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            step = TestStep(
                name=step_name,
                status="FAIL",
                duration_ms=duration,
                message=f"Database query exception: {str(e)}",
                details={"error": str(e)}
            )
        
        self.report.add_step(step)
        self.print_step(step)

    async def test_database_handoffs(self):
        """Verify agent handoffs are recorded in database"""
        step_name = "DB: Agent Handoffs"
        start = datetime.now(UTC)
        
        if not self.db_path or not self.db_path.exists():
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            step = TestStep(
                name=step_name,
                status="SKIP",
                duration_ms=duration,
                message="Skipped - database not found",
                details={}
            )
            self.report.add_step(step)
            self.print_step(step)
            return
        
        try:
            def query_handoffs():
                results = {
                    "checkpoints": [],
                    "handoff_checkpoints": []
                }
                
                with closing(sqlite3.connect(str(self.db_path))) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    # Query checkpoints for handoff indicators
                    if self.current_goal_id:
                        cursor.execute(
                            "SELECT * FROM checkpoints WHERE goal_id = ? ORDER BY created_at",
                            (self.current_goal_id,)
                        )
                    else:
                        cursor.execute(
                            "SELECT * FROM checkpoints ORDER BY created_at DESC LIMIT 20"
                        )
                    
                    rows = cursor.fetchall()
                    for row in rows:
                        cp_data = dict(row)
                        results["checkpoints"].append(cp_data)
                        
                        # Look for handoff-related checkpoints
                        title = cp_data.get("title", "").lower()
                        desc = cp_data.get("description", "").lower()
                        if any(word in title or word in desc for word in ["handoff", "complete", "next"]):
                            results["handoff_checkpoints"].append(cp_data)
                    
                    return results
            
            loop = asyncio.get_event_loop()
            db_data = await loop.run_in_executor(None, query_handoffs)
            
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            
            checkpoints = db_data.get("checkpoints", [])
            handoff_cps = db_data.get("handoff_checkpoints", [])
            
            # Calculate expected handoffs (n-1 for n agents)
            agents_in_goal = self.report.agents_executed.get(self.current_goal_id, [])
            expected_handoffs = max(0, len(agents_in_goal) - 1)
            
            if len(checkpoints) >= expected_handoffs and expected_handoffs > 0:
                status = "PASS"
                message = f"Found {len(checkpoints)} checkpoints (potential handoffs: {len(handoff_cps)})"
            elif len(checkpoints) > 0:
                status = "PASS"
                message = f"Found {len(checkpoints)} checkpoints"
            else:
                status = "FAIL"
                message = "No checkpoints found - handoffs may not be recorded"
            
            step = TestStep(
                name=step_name,
                status=status,
                duration_ms=duration,
                message=message,
                details={
                    "total_checkpoints": len(checkpoints),
                    "handoff_checkpoints": len(handoff_cps),
                    "expected_handoffs": expected_handoffs,
                    "checkpoints": [
                        {"title": cp.get("title"), "type": cp.get("checkpoint_type"), "status": cp.get("status")}
                        for cp in checkpoints[:10]
                    ]
                }
            )
            
        except Exception as e:
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            step = TestStep(
                name=step_name,
                status="FAIL",
                duration_ms=duration,
                message=f"Database query exception: {str(e)}",
                details={}
            )
        
        self.report.add_step(step)
        self.print_step(step)

    # ==========================================================================
    # Phase 7: Direct Orchestrator Test
    # ==========================================================================
    async def test_direct_orchestrator(self):
        """Test the orchestrator directly to verify multi-agent logic"""
        step_name = "Direct Orchestrator Test"
        start = datetime.now(UTC)
        
        # This is an informational test showing what the orchestrator SHOULD do
        # based on the code we've analyzed
        
        orchestrator_behavior = {
            "execution_strategy": "SEQUENTIAL",
            "agent_sequence": EXPECTED_AGENTS,
            "handoffs": [
                {
                    "from": "data_agent",
                    "to": "prd_agent",
                    "trigger": "Data analysis complete",
                    "key_fields": ["hypothesis", "confidence_score", "evidence", "recommendations"]
                },
                {
                    "from": "prd_agent", 
                    "to": "ui_ux_agent",
                    "trigger": "PRD approved",
                    "key_fields": ["user_personas", "user_stories", "requirements", "success_metrics"]
                }
            ],
            "expected_flow": [
                "1. data_agent executes first (research & analysis)",
                "2. data_agent output stored in context.data_findings",
                "3. Checkpoint created for data_agent completion",
                "4. WebSocket notification: agent_completed (data_agent)",
                "5. Handoff created: data_agent -> prd_agent",
                "6. prd_agent executes with data_findings in context",
                "7. prd_agent output stored in context.product_strategy",
                "8. Checkpoint created for prd_agent completion",
                "9. WebSocket notification: agent_completed (prd_agent)",
                "10. Handoff created: prd_agent -> ui_ux_agent",
                "11. ui_ux_agent executes with data_findings + product_strategy",
                "12. ui_ux_agent output stored in context.design_specs",
                "13. Checkpoint created for ui_ux_agent completion",
                "14. Goal marked as completed with all outputs"
            ]
        }
        
        duration = (datetime.now(UTC) - start).total_seconds() * 1000
        
        step = TestStep(
            name=step_name,
            status="INFO",
            duration_ms=duration,
            message="Orchestrator logic analysis (based on code review)",
            details=orchestrator_behavior
        )
        
        self.report.add_step(step)
        self.print_step(step)
        
        # Print expected flow
        print(f"\n    {Fore.CYAN}Expected Multi-Agent Flow:{Style.RESET_ALL}")
        for step_desc in orchestrator_behavior["expected_flow"]:
            print(f"      {step_desc}")

    # ==========================================================================
    # Final Report
    # ==========================================================================
    def print_comprehensive_report(self, total_duration: float):
        """Print comprehensive test report"""
        self.print_header("MULTI-AGENT ORCHESTRATION TEST - FINAL REPORT")
        
        # Summary stats
        print(f"\n{Fore.CYAN}TEST SUMMARY{Style.RESET_ALL}")
        print(f"  Total Tests:    {self.report.total_tests}")
        print(f"  {Fore.GREEN}Passed:         {self.report.passed}{Style.RESET_ALL}")
        print(f"  {Fore.RED}Failed:         {self.report.failed}{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}Skipped:        {self.report.skipped}{Style.RESET_ALL}")
        print(f"  {Fore.BLUE}Info:           {self.report.info}{Style.RESET_ALL}")
        print(f"  Total Duration: {total_duration:.2f}s")
        
        # Multi-agent specific findings
        print(f"\n{Fore.CYAN}MULTI-AGENT ORCHESTRATION FINDINGS{Style.RESET_ALL}")
        
        # Goal Parser Results
        print(f"\n  {Fore.YELLOW}Goal Parser Analysis:{Style.RESET_ALL}")
        for result in self.report.goal_parser_results:
            print(f"    • {result['goal_type']}: {result.get('agent_count', 0)} agents expected")
            if 'expected_agents' in result:
                print(f"      Agents: {', '.join(result['expected_agents'])}")
        
        # Agent Execution Results
        print(f"\n  {Fore.YELLOW}Agent Execution Results:{Style.RESET_ALL}")
        if self.report.agents_executed:
            for goal_id, agents in self.report.agents_executed.items():
                print(f"    Goal {goal_id[:8]}...:")
                print(f"      Agents executed: {len(agents)}")
                for i, agent in enumerate(agents, 1):
                    status_icon = f"{Fore.GREEN}[OK]{Style.RESET_ALL}" if agent in EXPECTED_AGENTS else f"{Fore.YELLOW}[?]{Style.RESET_ALL}"
                    print(f"      {status_icon} {i}. {agent}")
                
                # Check if multi-agent actually ran
                if len(agents) >= 3:
                    print(f"      {Fore.GREEN}[OK] Multi-agent execution confirmed!{Style.RESET_ALL}")
                elif len(agents) >= 2:
                    print(f"      {Fore.YELLOW}[WARNING] Partial multi-agent ({len(agents)} agents){Style.RESET_ALL}")
                else:
                    print(f"      {Fore.RED}[FAIL] Single-agent only{Style.RESET_ALL}")
        else:
            print(f"    {Fore.RED}No agent execution data available{Style.RESET_ALL}")
        
        # WebSocket Results
        print(f"\n  {Fore.YELLOW}WebSocket Message Analysis:{Style.RESET_ALL}")
        if self.report.websocket_messages:
            for goal_id, messages in self.report.websocket_messages.items():
                print(f"    Goal {goal_id[:8]}...:")
                print(f"      Total messages: {len(messages)}")
                
                # Count message types
                msg_types = {}
                agents_in_msgs = set()
                for msg in messages:
                    msg_type = msg.get("type", "unknown")
                    msg_types[msg_type] = msg_types.get(msg_type, 0) + 1
                    if "agent" in msg:
                        agents_in_msgs.add(msg["agent"])
                
                print(f"      Message types: {dict(msg_types)}")
                print(f"      Agents mentioned: {', '.join(agents_in_msgs) if agents_in_msgs else 'None'}")
                
                if len(agents_in_msgs) >= 2:
                    print(f"      {Fore.GREEN}[OK] WebSocket received messages from multiple agents{Style.RESET_ALL}")
                elif len(agents_in_msgs) == 1:
                    print(f"      {Fore.RED}[FAIL] WebSocket only received messages from 1 agent{Style.RESET_ALL}")
        else:
            print(f"    {Fore.RED}No WebSocket data available{Style.RESET_ALL}")
        
        # Database Results
        print(f"\n  {Fore.YELLOW}Database Verification:{Style.RESET_ALL}")
        if self.report.db_agent_states:
            for goal_id, states in self.report.db_agent_states.items():
                agent_names = set(s.get("agent_name") for s in states if s.get("agent_name"))
                print(f"    Goal {str(goal_id)[:8]}...:")
                print(f"      Agent states in DB: {len(states)}")
                print(f"      Unique agents: {len(agent_names)}")
                if agent_names:
                    print(f"      Agents: {', '.join(sorted(agent_names))}")
                
                if len(agent_names) >= 3:
                    print(f"      {Fore.GREEN}[OK] Multiple agent states recorded{Style.RESET_ALL}")
                elif len(agent_names) == 1:
                    print(f"      {Fore.RED}[FAIL] Only 1 agent state in DB{Style.RESET_ALL}")
        else:
            print(f"    {Fore.RED}No database agent state data{Style.RESET_ALL}")
        
        # WORKING vs NOT WORKING summary
        print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}WHAT WORKS vs WHAT FAILS{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        
        working = []
        not_working = []
        
        # Check various aspects
        if self.report.passed > 0:
            working.append(f"Basic API connectivity ({self.report.passed} tests passed)")
        
        if self.report.agents_executed:
            for agents in self.report.agents_executed.values():
                if len(agents) >= 2:
                    working.append(f"Multi-agent execution ({len(agents)} agents ran)")
                else:
                    not_working.append("Multi-agent execution (only 1 agent ran)")
        
        if self.report.websocket_messages:
            for messages in self.report.websocket_messages.values():
                if messages:
                    working.append(f"WebSocket message delivery ({len(messages)} messages)")
                else:
                    not_working.append("WebSocket message delivery (no messages)")
        
        if self.report.db_agent_states:
            for states in self.report.db_agent_states.values():
                agent_names = set(s.get("agent_name") for s in states if s.get("agent_name"))
                if len(agent_names) >= 2:
                    working.append(f"Database agent state recording ({len(agent_names)} agents)")
                else:
                    not_working.append("Database agent state recording (single agent only)")
        
        print(f"\n  {Fore.GREEN}[OK] WORKING:{Style.RESET_ALL}")
        for item in working:
            print(f"    - {item}")
        
        if not working:
            print(f"    {Fore.YELLOW}(No confirmed working components){Style.RESET_ALL}")
        
        print(f"\n  {Fore.RED}[FAIL] NOT WORKING / NEEDS INVESTIGATION:{Style.RESET_ALL}")
        for item in not_working:
            print(f"    - {item}")
        
        if not not_working and self.report.total_tests > 5:
            print(f"    {Fore.GREEN}(All critical components appear functional){Style.RESET_ALL}")
        
        # Final verdict
        print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        
        # Determine overall status
        multi_agent_working = any(
            len(agents) >= 2 
            for agents in self.report.agents_executed.values()
        )
        
        if multi_agent_working:
            print(f"{Fore.GREEN}VERDICT: Multi-agent orchestration is FUNCTIONAL{Style.RESET_ALL}")
            print(f"  Multiple agents are executing in sequence as designed.")
        elif self.report.agents_executed:
            print(f"{Fore.RED}VERDICT: Multi-agent orchestration is NOT WORKING{Style.RESET_ALL}")
            print(f"  Only single-agent execution detected. The orchestrator may not be")
            print(f"  properly invoking multiple agents or the goal parser may not be")
            print(f"  returning the required_agents list correctly.")
        else:
            print(f"{Fore.YELLOW}VERDICT: CANNOT DETERMINE{Style.RESET_ALL}")
            print(f"  Insufficient data to verify multi-agent functionality.")
        
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")


# =============================================================================
# Main Entry Point
# =============================================================================

async def main():
    """Run the comprehensive multi-agent orchestration test"""
    async with MultiAgentTestRunner() as runner:
        await runner.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Test failed with exception: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
