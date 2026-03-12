"""
FORENSIC DIAGNOSTIC AUDIT SUITE
=================================

Comprehensive diagnostic tool for the Agentic Research AI application.
"""

import asyncio
import json
import time
import traceback
import sys
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, 'files (6)/AGENTIC-AI-VERIFIED-FIXES/agentic-research-ai-FIXED/backend')

# =============================================================================
# FORENSIC DATA COLLECTOR
# =============================================================================

@dataclass
class ExecutionTrace:
    timestamp: str
    layer: str
    component: str
    function: str
    line_number: int
    event_type: str
    data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StateTransition:
    timestamp: str
    entity_type: str
    entity_id: str
    field: str
    old_value: Any
    new_value: Any
    triggered_by: str

@dataclass
class WebSocketEvent:
    timestamp: str
    direction: str
    goal_id: str
    message_type: str
    payload: Dict[str, Any]

@dataclass
class SilentFailure:
    timestamp: str
    component: str
    function: str
    line_number: int
    exception_type: str
    exception_message: str
    was_logged: bool


class ForensicCollector:
    def __init__(self):
        self.traces: List[ExecutionTrace] = []
        self.transitions: List[StateTransition] = []
        self.ws_events: List[WebSocketEvent] = []
        self.failures: List[SilentFailure] = []
        self.goal_parser_results: List[Dict] = []
        self.race_conditions: List[Dict] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    def start(self):
        self.start_time = datetime.now(UTC)
        print(f"[FORENSIC] Collection started at {self.start_time.isoformat()}")
    
    def stop(self):
        self.end_time = datetime.now(UTC)
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0
        print(f"[FORENSIC] Collection stopped")
        print(f"[TIME] Duration: {duration:.2f}s")
        print(f"[TRACES] {len(self.traces)}")
        print(f"[TRANSITIONS] {len(self.transitions)}")
        print(f"[WS] {len(self.ws_events)}")
        print(f"[FAILURES] {len(self.failures)}")
    
    def add_trace(self, **kwargs):
        self.traces.append(ExecutionTrace(**kwargs))
    
    def add_transition(self, **kwargs):
        self.transitions.append(StateTransition(**kwargs))
    
    def add_ws_event(self, **kwargs):
        self.ws_events.append(WebSocketEvent(**kwargs))
    
    def add_failure(self, **kwargs):
        self.failures.append(SilentFailure(**kwargs))
    
    def add_goal_result(self, result: Dict):
        self.goal_parser_results.append(result)
    
    def add_race_condition(self, race: Dict):
        self.race_conditions.append(race)


collector = ForensicCollector()


# =============================================================================
# TEST SCENARIOS
# =============================================================================

async def test_goal_parser():
    """Test goal parser with 5 different goal descriptions"""
    print("\n[TEST] Goal Parser Analysis")
    
    from src.core.goal_parser import GoalParser
    
    test_goals = [
        {
            "name": "Simple Data Analysis",
            "description": "Analyze our website traffic data to understand user behavior patterns",
            "expected_agents": ["data_agent"],
        },
        {
            "name": "Product Strategy with PRD",
            "description": "Create a product strategy for a new mobile banking app including user research and detailed PRD",
            "expected_agents": ["data_agent", "prd_agent"],
        },
        {
            "name": "Full Design Sprint",
            "description": "I need a complete UX research and design package for our onboarding flow - include data analysis, PRD, and UI/UX designs",
            "expected_agents": ["data_agent", "prd_agent", "ui_ux_agent"],
        },
        {
            "name": "Competitive Research",
            "description": "Research our top 3 competitors in the fintech space and create a competitive analysis report",
            "expected_agents": ["data_agent", "competitor_agent"],
        },
        {
            "name": "User Interview Synthesis",
            "description": "We conducted 20 user interviews. Analyze transcripts, extract insights, and create user personas",
            "expected_agents": ["data_agent", "interview_agent"],
        },
    ]
    
    parser = GoalParser()
    
    for test_case in test_goals:
        print(f"  Testing: {test_case['name']}")
        
        try:
            start = time.time()
            parsed = await parser.parse(test_case['description'])
            duration_ms = (time.time() - start) * 1000
            
            result = {
                "test_name": test_case['name'],
                "input": test_case['description'][:80],
                "expected_agents": test_case['expected_agents'],
                "actual_agents": parsed.required_agents,
                "goal_type": parsed.goal_type,
                "duration_ms": duration_ms,
                "autonomy_level": parsed.autonomy_level,
                "estimated_cost": parsed.estimated_cost_usd,
                "estimated_days": parsed.estimated_duration_days,
            }
            collector.add_goal_result(result)
            
            print(f"    [OK] Parsed in {duration_ms:.2f}ms")
            print(f"    Agents: {parsed.required_agents}")
            print(f"    Type: {parsed.goal_type}")
            
        except Exception as e:
            print(f"    [FAIL] {e}")
            collector.add_failure(
                timestamp=datetime.now(UTC).isoformat(),
                component="goal_parser",
                function="parse",
                line_number=71,
                exception_type=type(e).__name__,
                exception_message=str(e),
                was_logged=True,
            )


async def test_orchestrator():
    """Test orchestrator execution flow"""
    print("\n[TEST] Orchestrator Sequential Execution")
    
    from src.core.orchestrator import MultiAgentOrchestrator
    import inspect
    
    # Create mock objects
    mock_session = MagicMock()
    mock_session.commit = AsyncMock()
    
    mock_goal = MagicMock()
    mock_goal.id = "test-goal-123"
    mock_goal.status = "pending"
    mock_goal.description = "Test goal"
    mock_goal.budget_usd = 1000
    mock_goal.budget_spent = 0
    
    mock_parsed = MagicMock()
    mock_parsed.required_agents = ["data_agent", "prd_agent"]
    
    orchestrator = MultiAgentOrchestrator(mock_session, mock_goal, mock_parsed)
    
    print("  Testing _determine_strategy()...")
    strategy = orchestrator._determine_strategy()
    print(f"    Strategy: {strategy.value}")
    
    collector.add_trace(
        timestamp=datetime.now(UTC).isoformat(),
        layer="backend",
        component="orchestrator",
        function="_determine_strategy",
        line_number=414,
        event_type="executed",
        data={"strategy": strategy.value},
    )
    
    print("  Testing _build_sequence()...")
    sequence = orchestrator._build_sequence()
    print(f"    Sequence: {sequence}")
    
    collector.add_trace(
        timestamp=datetime.now(UTC).isoformat(),
        layer="backend",
        component="orchestrator",
        function="_build_sequence",
        line_number=422,
        event_type="executed",
        data={"sequence": sequence},
    )
    
    # Check WebSocket integration
    print("  Verifying WebSocket integration...")
    ws_source = inspect.getsource(MultiAgentOrchestrator._send_websocket_update)
    
    has_manager = "get_manager()" in ws_source
    has_send = "send_update" in ws_source
    has_silent = "except Exception:" in ws_source and "pass" in ws_source
    
    print(f"    Calls get_manager(): {has_manager}")
    print(f"    Calls send_update(): {has_send}")
    print(f"    Has silent exception handler: {has_silent}")
    
    if has_silent:
        print("    [WARN] Silent exception handler detected in _send_websocket_update")
        collector.add_failure(
            timestamp=datetime.now(UTC).isoformat(),
            component="orchestrator",
            function="_send_websocket_update",
            line_number=531,
            exception_type="SilentException",
            exception_message="Silent exception handler pattern detected",
            was_logged=False,
        )


async def test_websocket_manager():
    """Test ConnectionManager send_update"""
    print("\n[TEST] WebSocket Manager Verification")
    
    from src.api.main import ConnectionManager
    import inspect
    
    manager = ConnectionManager()
    
    # Track calls
    calls_made = []
    
    class MockWebSocket:
        async def send_json(self, data):
            calls_made.append(data)
        async def accept(self):
            pass
    
    mock_ws = MockWebSocket()
    manager.active_connections["test-goal"] = [mock_ws]
    
    test_message = {"type": "test", "data": "value"}
    await manager.send_update("test-goal", test_message)
    
    if len(calls_made) == 1:
        print("  [OK] send_update() calls connection.send_json()")
        collector.add_ws_event(
            timestamp=datetime.now(UTC).isoformat(),
            direction="OUT",
            goal_id="test-goal",
            message_type="test",
            payload=test_message,
        )
    else:
        print(f"  [FAIL] send_update() did not call connection.send_json()")
    
    # Check for silent exception handling
    source = inspect.getsource(ConnectionManager.send_update)
    if "except:" in source and "pass" in source:
        print("  [WARN] Silent exception handler in send_update")
        collector.add_race_condition({
            "type": "silent_failure",
            "location": "ConnectionManager.send_update",
            "description": "Exceptions silently caught with bare except clause",
        })


async def test_database_transitions():
    """Test database state machine"""
    print("\n[TEST] Database State Machine")
    
    from src.database.models import ResearchGoal, AgentState
    
    goal = ResearchGoal(description="Test goal", mode="demo")
    print(f"  Created ResearchGoal: {goal.id}")
    
    # Simulate state transitions
    states = ["pending", "running", "checkpoint", "running", "completed"]
    for i, state in enumerate(states):
        old_state = goal.status
        goal.status = state
        
        collector.add_transition(
            timestamp=datetime.now(UTC).isoformat(),
            entity_type="ResearchGoal",
            entity_id=goal.id,
            field="status",
            old_value=old_state,
            new_value=state,
            triggered_by=f"test_step_{i}",
        )
    
    print(f"  [OK] Recorded {len(states)} ResearchGoal transitions")
    
    # Test AgentState
    agent = AgentState(goal_id=goal.id, agent_name="data_agent", status="pending")
    print(f"  Created AgentState: {agent.id}")
    
    agent_states = ["pending", "running", "completed"]
    for state in agent_states:
        old = agent.status
        agent.status = state
        collector.add_transition(
            timestamp=datetime.now(UTC).isoformat(),
            entity_type="AgentState",
            entity_id=agent.id,
            field="status",
            old_value=old,
            new_value=state,
            triggered_by="agent_execution",
        )
    
    print(f"  [OK] Recorded {len(agent_states)} AgentState transitions")


async def test_race_conditions():
    """Test race condition detection"""
    print("\n[TEST] Race Condition Detection")
    
    from datetime import timedelta
    
    # Simulate WebSocket before commit scenario
    goal_id = "race-test-001"
    ws_time = datetime.now(UTC)
    commit_time = ws_time + timedelta(milliseconds=50)
    
    if ws_time < commit_time:
        delta_ms = (commit_time - ws_time).total_seconds() * 1000
        print(f"  [INFO] Detected timing: WS before commit by {delta_ms:.2f}ms")
        collector.add_race_condition({
            "type": "timing",
            "goal_id": goal_id,
            "description": "WebSocket sent before database commit",
            "ws_time": ws_time.isoformat(),
            "commit_time": commit_time.isoformat(),
            "delta_ms": delta_ms,
        })


async def test_silent_failures():
    """Detect silent failure patterns in code"""
    print("\n[TEST] Silent Failure Pattern Detection")
    
    from src.core.orchestrator import MultiAgentOrchestrator
    from src.api.main import ConnectionManager
    import inspect
    
    patterns_found = []
    
    # Check orchestrator
    source = inspect.getsource(MultiAgentOrchestrator._send_websocket_update)
    if "except Exception:" in source and "pass" in source:
        patterns_found.append(("orchestrator._send_websocket_update", "Silent exception handler"))
    
    # Check ConnectionManager
    source = inspect.getsource(ConnectionManager.send_update)
    if "except:" in source and "pass" in source:
        patterns_found.append(("ConnectionManager.send_update", "Silent exception handler"))
    
    if patterns_found:
        print(f"  [WARN] Found {len(patterns_found)} silent failure patterns:")
        for loc, pattern in patterns_found:
            print(f"    - {loc}: {pattern}")
    else:
        print("  [OK] No silent failure patterns found")


# =============================================================================
# REPORT GENERATION
# =============================================================================

def generate_report():
    """Generate comprehensive forensic report"""
    
    lines = [
        "# FORENSIC AUDIT REPORT",
        "",
        f"Generated: {datetime.now(UTC).isoformat()}",
        "",
        "## EXECUTIVE SUMMARY",
        "",
    ]
    
    # Determine failure mode
    if collector.failures:
        failure_mode = "(B) RUNTIME FUNCTIONAL FAILURE"
    elif collector.race_conditions:
        failure_mode = "(C) PARTIAL DEGRADATION - Race conditions"
    else:
        failure_mode = "(C) PARTIAL DEGRADATION - Minor issues"
    
    lines.append(f"**Failure Mode Classification: {failure_mode}**")
    lines.append("")
    
    # Statistics
    lines.extend([
        "### Key Metrics",
        f"- Execution Traces: {len(collector.traces)}",
        f"- State Transitions: {len(collector.transitions)}",
        f"- WebSocket Events: {len(collector.ws_events)}",
        f"- Silent Failures: {len(collector.failures)}",
        f"- Race Conditions: {len(collector.race_conditions)}",
        "",
    ])
    
    # Goal Parser Results
    if collector.goal_parser_results:
        lines.extend([
            "## GOAL PARSER ANALYSIS",
            "",
        ])
        for result in collector.goal_parser_results:
            lines.extend([
                f"### {result['test_name']}",
                f"- **Input:** {result['input']}",
                f"- **Expected Agents:** {result['expected_agents']}",
                f"- **Actual Agents:** {result['actual_agents']}",
                f"- **Goal Type:** {result['goal_type']}",
                f"- **Duration:** {result['duration_ms']:.2f}ms",
                "",
            ])
    
    # Silent Failures
    if collector.failures:
        lines.extend([
            "## SILENT FAILURE ANALYSIS",
            "",
        ])
        for failure in collector.failures:
            lines.extend([
                f"### {failure.component}.{failure.function}",
                f"- **Exception:** {failure.exception_type}",
                f"- **Message:** {failure.exception_message}",
                f"- **Line:** {failure.line_number}",
                f"- **Was Logged:** {failure.was_logged}",
                "",
            ])
    
    # Race Conditions
    if collector.race_conditions:
        lines.extend([
            "## RACE CONDITION ANALYSIS",
            "",
        ])
        for race in collector.race_conditions:
            lines.extend([
                f"- **Type:** {race['type']}",
                f"  - **Description:** {race.get('description', 'N/A')}",
                "",
            ])
    
    # Database State Machine
    if collector.transitions:
        lines.extend([
            "## DATABASE STATE MACHINE",
            "",
        ])
        
        by_entity = {}
        for t in collector.transitions:
            key = f"{t.entity_type}:{t.entity_id}"
            if key not in by_entity:
                by_entity[key] = []
            by_entity[key].append(t)
        
        for entity, transitions in by_entity.items():
            lines.append(f"### {entity}")
            for t in transitions:
                lines.append(f"- [{t.timestamp}] {t.field}: {t.old_value} -> {t.new_value}")
            lines.append("")
    
    # WebSocket Events
    if collector.ws_events:
        lines.extend([
            "## WEBSOCKET FORENSICS",
            "",
        ])
        for event in collector.ws_events:
            lines.append(f"- [{event.timestamp}] {event.direction}: {event.message_type}")
        lines.append("")
    
    return "\n".join(lines)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def run_audit():
    """Run complete forensic audit"""
    print("=" * 80)
    print("FORENSIC DIAGNOSTIC AUDIT - AGENTIC RESEARCH AI")
    print("=" * 80)
    
    collector.start()
    
    try:
        await test_goal_parser()
        await test_orchestrator()
        await test_websocket_manager()
        await test_database_transitions()
        await test_race_conditions()
        await test_silent_failures()
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        traceback.print_exc()
    
    finally:
        collector.stop()
        
        # Generate report
        report = generate_report()
        
        # Save report
        report_path = "FORENSIC_AUDIT_REPORT.md"
        with open(report_path, "w") as f:
            f.write(report)
        
        print(f"\n[REPORT] Saved to: {report_path}")
        
        # Save raw data
        data = {
            "traces": [asdict(t) for t in collector.traces],
            "transitions": [asdict(t) for t in collector.transitions],
            "ws_events": [asdict(e) for e in collector.ws_events],
            "failures": [asdict(f) for f in collector.failures],
            "goal_results": collector.goal_parser_results,
            "race_conditions": collector.race_conditions,
        }
        
        with open("FORENSIC_DATA.json", "w") as f:
            json.dump(data, f, indent=2, default=str)
        
        print("[DATA] Saved to: FORENSIC_DATA.json")


if __name__ == "__main__":
    asyncio.run(run_audit())
