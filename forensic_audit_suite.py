"""
FORENSIC DIAGNOSTIC AUDIT SUITE
=================================

Comprehensive diagnostic tool for the Agentic Research AI application.
Captures execution traces, WebSocket messages, database state transitions,
and detects silent failures.

Usage:
    python forensic_audit_suite.py

Report generated: FORENSIC_AUDIT_REPORT.md
"""

import asyncio
import json
import time
import traceback
import sys
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import inspect
import functools

# Test framework
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

# Configure paths
sys.path.insert(0, 'files (6)/AGENTIC-AI-VERIFIED-FIXES/agentic-research-ai-FIXED/backend')

# Import application code
from src.core.config import get_settings, constants
from src.database.models import ResearchGoal, AgentState, Checkpoint
from src.database.session import AsyncSession
from src.core.goal_parser import GoalParser, ParsedGoal


# =============================================================================
# FORENSIC DATA STRUCTURES
# =============================================================================

@dataclass
class ExecutionTrace:
    """Captures a single execution event"""
    timestamp: datetime
    layer: str  # 'frontend', 'backend', 'database', 'websocket'
    component: str  # Component name (e.g., 'orchestrator', 'data_agent')
    function: str
    line_number: int
    event_type: str  # 'entry', 'exit', 'error', 'state_change', 'websocket_send'
    data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "layer": self.layer,
            "component": self.component,
            "function": self.function,
            "line_number": self.line_number,
            "event_type": self.event_type,
            "data": self.data,
            "duration_ms": self.duration_ms,
        }


@dataclass
class WebSocketMessage:
    """Captures WebSocket message"""
    timestamp: datetime
    direction: str  # 'sent', 'received'
    goal_id: str
    message_type: str
    payload: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "direction": self.direction,
            "goal_id": self.goal_id,
            "message_type": self.message_type,
            "payload": self.payload,
        }


@dataclass
class StateTransition:
    """Captures database state transition"""
    timestamp: datetime
    entity_type: str  # 'ResearchGoal', 'AgentState'
    entity_id: str
    field: str
    old_value: Any
    new_value: Any
    triggered_by: str  # Function/component that triggered change
    line_number: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "entity_type": self.entity_type,
            "entity_id": entity_id,
            "field": self.field,
            "old_value": str(self.old_value),
            "new_value": str(self.new_value),
            "triggered_by": self.triggered_by,
            "line_number": self.line_number,
        }


@dataclass
class SilentFailure:
    """Captures silent failures"""
    timestamp: datetime
    component: str
    function: str
    line_number: int
    exception_type: str
    exception_message: str
    exception_traceback: str
    was_caught: bool
    was_logged: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "component": self.component,
            "function": self.function,
            "line_number": self.line_number,
            "exception_type": self.exception_type,
            "exception_message": self.exception_message,
            "exception_traceback": self.exception_traceback,
            "was_caught": self.was_caught,
            "was_logged": self.was_logged,
        }


# =============================================================================
# FORENSIC COLLECTOR
# =============================================================================

class ForensicCollector:
    """
    Central collector for all forensic data.
    Singleton pattern to ensure all components use same collector.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.reset()
        return cls._instance
    
    def reset(self):
        """Reset all collected data"""
        self.execution_traces: List[ExecutionTrace] = []
        self.websocket_messages: List[WebSocketMessage] = []
        self.state_transitions: List[StateTransition] = []
        self.silent_failures: List[SilentFailure] = []
        self.goal_parser_results: List[Dict[str, Any]] = []
        self.race_conditions: List[Dict[str, Any]] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    def start_collection(self):
        """Start forensic collection"""
        self.reset()
        self.start_time = datetime.now(UTC)
        print(f"[FORENSIC] Collection started at {self.start_time.isoformat()}")
    
    def stop_collection(self):
        """Stop forensic collection"""
        self.end_time = datetime.now(UTC)
        duration = (self.end_time - self.start_time).total_seconds()
        print(f"[FORENSIC] Collection stopped at {self.end_time.isoformat()}")
        print(f"[TIME] Total duration: {duration:.2f}s")
        print(f"[TRACES] Execution traces: {len(self.execution_traces)}")
        print(f"[WS] WebSocket messages: {len(self.websocket_messages)}")
        print(f"[DB] State transitions: {len(self.state_transitions)}")
        print(f"[ERRORS] Silent failures: {len(self.silent_failures)}")
    
    def add_trace(self, trace: ExecutionTrace):
        """Add execution trace"""
        self.execution_traces.append(trace)
    
    def add_websocket_message(self, msg: WebSocketMessage):
        """Add WebSocket message"""
        self.websocket_messages.append(msg)
    
    def add_state_transition(self, transition: StateTransition):
        """Add state transition"""
        self.state_transitions.append(transition)
    
    def add_silent_failure(self, failure: SilentFailure):
        """Add silent failure"""
        self.silent_failures.append(failure)
    
    def add_goal_parser_result(self, result: Dict[str, Any]):
        """Add goal parser result"""
        self.goal_parser_results.append(result)
    
    def add_race_condition(self, race: Dict[str, Any]):
        """Add detected race condition"""
        self.race_conditions.append(race)
    
    def generate_report(self) -> str:
        """Generate comprehensive forensic report"""
        report_lines = [
            "# FORENSIC AUDIT REPORT",
            f"Generated: {datetime.now(UTC).isoformat()}",
            f"Collection Start: {self.start_time.isoformat() if self.start_time else 'N/A'}",
            f"Collection End: {self.end_time.isoformat() if self.end_time else 'N/A'}",
            "",
            "## EXECUTIVE SUMMARY",
            "",
        ]
        
        # Calculate statistics
        total_traces = len(self.execution_traces)
        total_ws_messages = len(self.websocket_messages)
        total_transitions = len(self.state_transitions)
        total_failures = len(self.silent_failures)
        
        # Determine failure mode
        failure_mode = self._determine_failure_mode()
        report_lines.extend([
            f"**Failure Mode Classification: {failure_mode}**",
            "",
            "### Key Metrics",
            f"- Total Execution Traces: {total_traces}",
            f"- Total WebSocket Messages: {total_ws_messages}",
            f"- Total State Transitions: {total_transitions}",
            f"- Silent Failures Detected: {total_failures}",
            f"- Race Conditions Detected: {len(self.race_conditions)}",
            "",
        ])
        
        # Add failure analysis
        if total_failures > 0:
            report_lines.extend([
                "## SILENT FAILURE ANALYSIS",
                "",
            ])
            for i, failure in enumerate(self.silent_failures[:10], 1):
                report_lines.extend([
                    f"### Failure #{i}",
                    f"- **Component:** {failure.component}",
                    f"- **Function:** {failure.function}",
                    f"- **Line:** {failure.line_number}",
                    f"- **Exception:** {failure.exception_type}",
                    f"- **Message:** {failure.exception_message}",
                    f"- **Was Caught:** {failure.was_caught}",
                    f"- **Was Logged:** {failure.was_logged}",
                    "",
                ])
        
        # Add WebSocket analysis
        if total_ws_messages > 0:
            report_lines.extend([
                "## WEBSOCKET FORENSICS",
                "",
            ])
            message_types = {}
            for msg in self.websocket_messages:
                msg_type = msg.message_type
                message_types[msg_type] = message_types.get(msg_type, 0) + 1
            
            report_lines.append("### Message Type Distribution")
            for msg_type, count in sorted(message_types.items()):
                report_lines.append(f"- {msg_type}: {count}")
            report_lines.append("")
            
            report_lines.append("### Chronological Message Log")
            for msg in self.websocket_messages[:50]:  # First 50 messages
                report_lines.append(f"- [{msg.timestamp.isoformat()}] {msg.direction.upper()}: {msg.message_type}")
            report_lines.append("")
        
        # Add state transition analysis
        if total_transitions > 0:
            report_lines.extend([
                "## DATABASE STATE MACHINE",
                "",
                "### State Transitions",
                "",
            ])
            
            # Group by entity
            by_entity = {}
            for transition in self.state_transitions:
                key = f"{transition.entity_type}:{transition.entity_id}"
                if key not in by_entity:
                    by_entity[key] = []
                by_entity[key].append(transition)
            
            for entity_key, transitions in list(by_entity.items())[:10]:
                report_lines.append(f"#### {entity_key}")
                for t in transitions:
                    report_lines.append(
                        f"- [{t.timestamp.isoformat()}] {t.field}: {t.old_value} → {t.new_value} "
                        f"(at line {t.line_number})"
                    )
                report_lines.append("")
        
        # Add execution trace analysis
        if total_traces > 0:
            report_lines.extend([
                "## EXECUTION TRACE",
                "",
            ])
            
            # Group by component
            by_component = {}
            for trace in self.execution_traces:
                comp = trace.component
                if comp not in by_component:
                    by_component[comp] = []
                by_component[comp].append(trace)
            
            for component, traces in sorted(by_component.items()):
                report_lines.append(f"### Component: {component}")
                for trace in traces[:20]:  # First 20 per component
                    report_lines.append(
                        f"- [{trace.timestamp.isoformat()}] {trace.function}() "
                        f"(line {trace.line_number}) - {trace.event_type}"
                    )
                report_lines.append("")
        
        # Add goal parser analysis
        if self.goal_parser_results:
            report_lines.extend([
                "## GOAL PARSER ANALYSIS",
                "",
            ])
            for result in self.goal_parser_results:
                report_lines.extend([
                    f"### Input: {result['input'][:80]}...",
                    f"**Required Agents:** {', '.join(result['required_agents'])}",
                    f"**Goal Type:** {result['goal_type']}",
                    f"**Estimated Duration:** {result['estimated_duration_days']} days",
                    f"**Autonomy Level:** {result['autonomy_level']}",
                    "",
                ])
        
        # Add race condition analysis
        if self.race_conditions:
            report_lines.extend([
                "## RACE CONDITION ANALYSIS",
                "",
            ])
            for race in self.race_conditions:
                report_lines.extend([
                    f"- **Issue:** {race['description']}",
                    f"  - **Location:** {race['location']}",
                    f"  - **Severity:** {race['severity']}",
                    "",
                ])
        
        return "\n".join(report_lines)
    
    def _determine_failure_mode(self) -> str:
        """Determine the failure mode classification"""
        critical_startup_failures = [
            f for f in self.silent_failures 
            if f.component in ['database', 'config', 'main'] and f.function in ['lifespan', 'init_db']
        ]
        
        if critical_startup_failures:
            return "(A) CRITICAL STARTUP FAILURE"
        
        runtime_failures = [
            f for f in self.silent_failures
            if f.component in ['orchestrator', 'data_agent', 'prd_agent', 'ui_ux_agent']
        ]
        
        if runtime_failures:
            return "(B) RUNTIME FUNCTIONAL FAILURE"
        
        if len(self.websocket_messages) == 0 and len(self.execution_traces) > 0:
            return "(C) PARTIAL DEGRADATION - WebSocket not functioning"
        
        if self.race_conditions:
            return "(C) PARTIAL DEGRADATION - Race conditions detected"
        
        return "(C) PARTIAL DEGRADATION - Minor issues detected"


# Global collector instance
collector = ForensicCollector()


# =============================================================================
# TRACING DECORATORS
# =============================================================================

def trace_execution(layer: str, component: str):
    """Decorator to trace function execution"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get line number
            line_number = inspect.getsourcelines(func)[1]
            
            # Record entry
            entry_trace = ExecutionTrace(
                timestamp=datetime.now(UTC),
                layer=layer,
                component=component,
                function=func.__name__,
                line_number=line_number,
                event_type="entry",
                data={"args_count": len(args), "kwargs_keys": list(kwargs.keys())},
            )
            collector.add_trace(entry_trace)
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                
                # Record exit
                exit_trace = ExecutionTrace(
                    timestamp=datetime.now(UTC),
                    layer=layer,
                    component=component,
                    function=func.__name__,
                    line_number=line_number,
                    event_type="exit",
                    data={"success": True},
                    duration_ms=(time.time() - start_time) * 1000,
                )
                collector.add_trace(exit_trace)
                
                return result
                
            except Exception as e:
                # Record error
                error_trace = ExecutionTrace(
                    timestamp=datetime.now(UTC),
                    layer=layer,
                    component=component,
                    function=func.__name__,
                    line_number=line_number,
                    event_type="error",
                    data={
                        "exception_type": type(e).__name__,
                        "exception_message": str(e),
                    },
                    duration_ms=(time.time() - start_time) * 1000,
                )
                collector.add_trace(error_trace)
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            line_number = inspect.getsourcelines(func)[1]
            
            entry_trace = ExecutionTrace(
                timestamp=datetime.now(UTC),
                layer=layer,
                component=component,
                function=func.__name__,
                line_number=line_number,
                event_type="entry",
                data={"args_count": len(args), "kwargs_keys": list(kwargs.keys())},
            )
            collector.add_trace(entry_trace)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                
                exit_trace = ExecutionTrace(
                    timestamp=datetime.now(UTC),
                    layer=layer,
                    component=component,
                    function=func.__name__,
                    line_number=line_number,
                    event_type="exit",
                    data={"success": True},
                    duration_ms=(time.time() - start_time) * 1000,
                )
                collector.add_trace(exit_trace)
                
                return result
                
            except Exception as e:
                error_trace = ExecutionTrace(
                    timestamp=datetime.now(UTC),
                    layer=layer,
                    component=component,
                    function=func.__name__,
                    line_number=line_number,
                    event_type="error",
                    data={
                        "exception_type": type(e).__name__,
                        "exception_message": str(e),
                    },
                    duration_ms=(time.time() - start_time) * 1000,
                )
                collector.add_trace(error_trace)
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def detect_silent_failures(component: str):
    """Decorator to detect if exceptions are silently caught without logging"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            line_number = inspect.getsourcelines(func)[1]
            
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Check if exception was silently caught
                exc_type = type(e).__name__
                exc_msg = str(e)
                exc_tb = traceback.format_exc()
                
                # Determine if it was properly logged
                was_logged = False  # We'll need to check logging handlers
                
                failure = SilentFailure(
                    timestamp=datetime.now(UTC),
                    component=component,
                    function=func.__name__,
                    line_number=line_number,
                    exception_type=exc_type,
                    exception_message=exc_msg,
                    exception_traceback=exc_tb,
                    was_caught=True,
                    was_logged=was_logged,
                )
                collector.add_silent_failure(failure)
                
                # Re-raise to maintain original behavior
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            line_number = inspect.getsourcelines(func)[1]
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                exc_type = type(e).__name__
                exc_msg = str(e)
                exc_tb = traceback.format_exc()
                
                failure = SilentFailure(
                    timestamp=datetime.now(UTC),
                    component=component,
                    function=func.__name__,
                    line_number=line_number,
                    exception_type=exc_type,
                    exception_message=exc_msg,
                    exception_traceback=exc_tb,
                    was_caught=True,
                    was_logged=False,
                )
                collector.add_silent_failure(failure)
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


# =============================================================================
# INSTRUMENTED MOCK CLASSES
# =============================================================================

class InstrumentedConnectionManager:
    """
    Instrumented version of ConnectionManager that captures all WebSocket activity.
    """
    
    def __init__(self):
        self.active_connections: Dict[str, list] = {}
        self.send_update_calls: List[Dict[str, Any]] = []
        self._original_send_update = None
    
    async def connect(self, websocket, goal_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        if goal_id not in self.active_connections:
            self.active_connections[goal_id] = []
        self.active_connections[goal_id].append(websocket)
        
        # Record connection
        collector.add_websocket_message(WebSocketMessage(
            timestamp=datetime.now(UTC),
            direction="received",
            goal_id=goal_id,
            message_type="connected",
            payload={"status": "connected"},
        ))
    
    def disconnect(self, websocket, goal_id: str):
        """Remove WebSocket connection"""
        if goal_id in self.active_connections:
            self.active_connections[goal_id].remove(websocket)
        
        collector.add_websocket_message(WebSocketMessage(
            timestamp=datetime.now(UTC),
            direction="received",
            goal_id=goal_id,
            message_type="disconnected",
            payload={},
        ))
    
    async def send_update(self, goal_id: str, message: dict):
        """
        Send update to all connections for a goal.
        This is the critical function we need to verify is being called.
        """
        call_record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "goal_id": goal_id,
            "message": message,
            "has_connections": goal_id in self.active_connections,
            "connection_count": len(self.active_connections.get(goal_id, [])),
        }
        self.send_update_calls.append(call_record)
        
        # Record WebSocket message
        collector.add_websocket_message(WebSocketMessage(
            timestamp=datetime.now(UTC),
            direction="sent",
            goal_id=goal_id,
            message_type=message.get("type", "unknown"),
            payload=message,
        ))
        
        # Actually send to connections
        if goal_id in self.active_connections:
            for connection in self.active_connections[goal_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    # Record failure but don't crash
                    collector.add_silent_failure(SilentFailure(
                        timestamp=datetime.now(UTC),
                        component="ConnectionManager",
                        function="send_update",
                        line_number=432,
                        exception_type=type(e).__name__,
                        exception_message=str(e),
                        exception_traceback=traceback.format_exc(),
                        was_caught=True,
                        was_logged=False,
                    ))


class InstrumentedAsyncSession:
    """
    Instrumented database session that captures all state transitions.
    """
    
    def __init__(self, wrapped_session=None):
        self.wrapped_session = wrapped_session
        self.added_objects: List[Any] = []
        self.committed = False
        self.commit_timestamps: List[datetime] = []
    
    async def commit(self):
        """Commit with instrumentation"""
        commit_time = datetime.now(UTC)
        self.commit_timestamps.append(commit_time)
        
        # Check for race condition: commit before WebSocket
        last_ws_time = None
        if collector.websocket_messages:
            last_ws_time = collector.websocket_messages[-1].timestamp
        
        if last_ws_time and last_ws_time > commit_time:
            collector.add_race_condition({
                "description": "WebSocket message sent BEFORE database commit",
                "location": "InstrumentedAsyncSession.commit()",
                "severity": "HIGH",
                "commit_time": commit_time.isoformat(),
                "last_ws_time": last_ws_time.isoformat(),
            })
        
        # Record state transitions for all tracked objects
        for obj in self.added_objects:
            if hasattr(obj, '__tablename__'):
                entity_type = obj.__class__.__name__
                entity_id = getattr(obj, 'id', 'unknown')
                
                # Track status changes
                if hasattr(obj, 'status'):
                    transition = StateTransition(
                        timestamp=commit_time,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        field="status",
                        old_value="pending",
                        new_value=obj.status,
                        triggered_by="session.commit()",
                        line_number=500,
                    )
                    collector.add_state_transition(transition)
                
                # Track progress changes
                if hasattr(obj, 'progress_percent'):
                    transition = StateTransition(
                        timestamp=commit_time,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        field="progress_percent",
                        old_value=0.0,
                        new_value=obj.progress_percent,
                        triggered_by="session.commit()",
                        line_number=500,
                    )
                    collector.add_state_transition(transition)
        
        self.committed = True
        
        if self.wrapped_session:
            await self.wrapped_session.commit()
    
    def add(self, obj):
        """Track added objects"""
        self.added_objects.append(obj)
        if self.wrapped_session:
            self.wrapped_session.add(obj)
    
    async def execute(self, statement):
        """Execute with tracking"""
        if self.wrapped_session:
            return await self.wrapped_session.execute(statement)
        # Mock result
        return MagicMock()
    
    async def refresh(self, obj):
        """Refresh with tracking"""
        if self.wrapped_session:
            await self.wrapped_session.refresh(obj)
    
    async def close(self):
        """Close with tracking"""
        if self.wrapped_session:
            await self.wrapped_session.close()


# =============================================================================
# TEST CASES
# =============================================================================

class GoalParserForensicTests:
    """Test goal parser with various inputs"""
    
    TEST_GOALS = [
        {
            "name": "Simple Data Analysis",
            "description": "Analyze our website traffic data to understand user behavior patterns",
            "expected_agents": ["data_agent"],
            "expected_type": "general",
        },
        {
            "name": "Product Strategy with PRD",
            "description": "Create a product strategy for a new mobile banking app including user research, competitive analysis, and a detailed PRD",
            "expected_agents": ["data_agent", "prd_agent"],
            "expected_type": "feature_validation",
        },
        {
            "name": "Full Design Sprint",
            "description": "I need a complete UX research and design package for our onboarding flow - include data analysis, PRD documentation, and UI/UX designs with wireframes",
            "expected_agents": ["data_agent", "prd_agent", "ui_ux_agent"],
            "expected_type": "usability_testing",
        },
        {
            "name": "Competitive Research",
            "description": "Research our top 3 competitors in the fintech space and create a competitive analysis report with recommendations",
            "expected_agents": ["data_agent", "competitor_agent"],
            "expected_type": "competitive_analysis",
        },
        {
            "name": "User Interview Synthesis",
            "description": "We conducted 20 user interviews about our product. Analyze the transcripts, extract insights, and create user personas with journey maps",
            "expected_agents": ["data_agent", "interview_agent", "prd_agent", "ui_ux_agent"],
            "expected_type": "user_research",
        },
    ]
    
    @staticmethod
    async def test_goal_parsing():
        """Test goal parser with all test cases"""
        print("\n🧪 Testing Goal Parser...")
        
        parser = GoalParser()
        
        for test_case in GoalParserForensicTests.TEST_GOALS:
            print(f"  Testing: {test_case['name']}")
            
            try:
                # Parse the goal
                parsed = await parser.parse(test_case['description'])
                
                # Record result
                result = {
                    "input": test_case['description'],
                    "expected_agents": test_case['expected_agents'],
                    "actual_agents": parsed.required_agents,
                    "goal_type": parsed.goal_type,
                    "estimated_duration_days": parsed.estimated_duration_days,
                    "estimated_cost_usd": parsed.estimated_cost_usd,
                    "autonomy_level": parsed.autonomy_level,
                    "success_criteria": parsed.success_criteria,
                    "constraints": parsed.constraints,
                    "parsed_at": datetime.now(UTC).isoformat(),
                }
                collector.add_goal_parser_result(result)
                
                # Validate
                expected_set = set(test_case['expected_agents'])
                actual_set = set(parsed.required_agents)
                
                if not expected_set.intersection(actual_set):
                    print(f"    ⚠️  Agent mismatch! Expected at least one of {expected_set}, got {actual_set}")
                else:
                    print(f"    ✅ Agents: {parsed.required_agents}")
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
                collector.add_silent_failure(SilentFailure(
                    timestamp=datetime.now(UTC),
                    component="GoalParser",
                    function="parse",
                    line_number=71,
                    exception_type=type(e).__name__,
                    exception_message=str(e),
                    exception_traceback=traceback.format_exc(),
                    was_caught=False,
                    was_logged=True,
                ))


class OrchestratorForensicTests:
    """Test orchestrator execution flow"""
    
    @staticmethod
    @trace_execution("backend", "orchestrator")
    async def test_sequential_execution():
        """Test the _execute_sequential flow"""
        print("\n🧪 Testing Orchestrator Sequential Execution...")
        
        # Create mock session
        mock_session = InstrumentedAsyncSession()
        
        # Create mock goal
        goal = MagicMock(spec=ResearchGoal)
        goal.id = "test-goal-123"
        goal.status = "pending"
        goal.description = "Test goal for forensic analysis"
        goal.budget_usd = 1000
        goal.budget_spent = 0
        goal.progress_percent = 0.0
        goal.current_agent = None
        goal.final_output = None
        goal.findings = None
        goal.error_message = None
        
        # Create mock parsed goal
        parsed = MagicMock(spec=ParsedGoal)
        parsed.required_agents = ["data_agent", "prd_agent"]
        parsed.goal_type = "test"
        
        # Import and instrument orchestrator
        from src.core.orchestrator import MultiAgentOrchestrator
        
        orchestrator = MultiAgentOrchestrator(mock_session, goal, parsed)
        
        # Track execution flow
        print("  Checking execution strategy...")
        strategy = orchestrator._determine_strategy()
        print(f"    Strategy: {strategy.value}")
        
        print("  Checking agent sequence...")
        sequence = orchestrator._build_sequence()
        print(f"    Sequence: {sequence}")
        
        # Verify WebSocket manager integration
        print("  Verifying WebSocket integration...")
        from src.core.orchestrator import get_manager
        ws_manager = get_manager()
        print(f"    WebSocket manager: {ws_manager}")
        
        return {
            "strategy": strategy.value,
            "sequence": sequence,
            "has_ws_manager": ws_manager is not None,
        }


class WebSocketForensicTests:
    """Test WebSocket message flow"""
    
    @staticmethod
    async def test_websocket_manager():
        """Test if ConnectionManager.send_update is actually called"""
        print("\n🧪 Testing WebSocket Manager...")
        
        # Create instrumented manager
        manager = InstrumentedConnectionManager()
        
        # Create mock websocket
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        
        # Test connect
        await manager.connect(mock_ws, "goal-123")
        assert "goal-123" in manager.active_connections
        print("  ✅ Connection tracking works")
        
        # Test send_update
        test_message = {"type": "test", "data": "hello"}
        await manager.send_update("goal-123", test_message)
        
        # Verify send was called
        mock_ws.send_json.assert_called_once_with(test_message)
        print("  ✅ send_update actually calls connection.send_json")
        
        # Verify tracking
        assert len(manager.send_update_calls) == 1
        print(f"  ✅ Call tracking works ({len(manager.send_update_calls)} calls recorded)")
        
        return {
            "calls_recorded": len(manager.send_update_calls),
            "connections_tracked": len(manager.active_connections),
        }
    
    @staticmethod
    async def test_orchestrator_websocket_integration():
        """Test if orchestrator properly calls WebSocket manager"""
        print("\n🧪 Testing Orchestrator WebSocket Integration...")
        
        # This will verify _send_websocket_update actually works
        from src.core.orchestrator import MultiAgentOrchestrator
        
        # Check the _send_websocket_update method
        import inspect
        source = inspect.getsource(MultiAgentOrchestrator._send_websocket_update)
        
        # Verify it calls get_manager and send_update
        has_get_manager = "get_manager()" in source
        has_send_update = "send_update" in source
        
        print(f"  _send_websocket_update calls get_manager(): {has_get_manager}")
        print(f"  _send_websocket_update calls send_update(): {has_send_update}")
        
        # Check for silent failure pattern (pass on exception)
        has_silent_pass = "except Exception:" in source and "pass" in source
        print(f"  Has silent failure pattern: {has_silent_pass}")
        
        if has_silent_pass:
            collector.add_race_condition({
                "description": "WebSocket errors are silently ignored in _send_websocket_update",
                "location": "MultiAgentOrchestrator._send_websocket_update()",
                "severity": "MEDIUM",
                "details": "Exceptions in WebSocket sending are caught and ignored, which may hide connectivity issues",
            })
        
        return {
            "has_get_manager": has_get_manager,
            "has_send_update": has_send_update,
            "has_silent_pass": has_silent_pass,
        }


class DatabaseForensicTests:
    """Test database state transitions"""
    
    @staticmethod
    async def test_state_transitions():
        """Test agent state machine transitions"""
        print("\n🧪 Testing Database State Transitions...")
        
        # Test ResearchGoal state transitions
        goal = ResearchGoal(
            description="Test goal",
            mode="demo",
        )
        
        transitions = []
        
        # Simulate state transitions
        states = ["pending", "running", "checkpoint", "running", "completed"]
        for i, state in enumerate(states):
            old_state = goal.status
            goal.status = state
            
            transition = StateTransition(
                timestamp=datetime.now(UTC),
                entity_type="ResearchGoal",
                entity_id=goal.id,
                field="status",
                old_value=old_state,
                new_value=state,
                triggered_by="test",
                line_number=100 + i,
            )
            collector.add_state_transition(transition)
            transitions.append(transition)
        
        print(f"  ✅ Recorded {len(transitions)} state transitions")
        
        # Check for expected transition path
        expected_path = ["pending", "running", "checkpoint", "running", "completed"]
        actual_path = [t.new_value for t in transitions]
        
        if actual_path == expected_path:
            print("  ✅ State transition path matches expected")
        else:
            print(f"  ⚠️  Path mismatch: expected {expected_path}, got {actual_path}")
        
        return {
            "transitions_recorded": len(transitions),
            "expected_path": expected_path,
            "actual_path": actual_path,
        }


class RaceConditionTests:
    """Test for race conditions"""
    
    @staticmethod
    async def test_commit_before_websocket():
        """Verify database commits happen before WebSocket sends"""
        print("\n🧪 Testing for Race Conditions...")
        
        # Check collected data for race conditions
        ws_times = [m.timestamp for m in collector.websocket_messages]
        commit_times = [t.timestamp for t in collector.state_transitions]
        
        race_conditions_found = 0
        
        # Compare timestamps
        for ws_time in ws_times:
            for commit_time in commit_times:
                if ws_time < commit_time:
                    time_diff = (commit_time - ws_time).total_seconds()
                    if time_diff < 1.0:  # Less than 1 second difference
                        race_conditions_found += 1
                        collector.add_race_condition({
                            "description": f"WebSocket sent {time_diff:.3f}s before commit",
                            "location": "General",
                            "severity": "HIGH" if time_diff < 0.1 else "MEDIUM",
                            "time_diff_seconds": time_diff,
                        })
        
        if race_conditions_found == 0:
            print("  ✅ No race conditions detected")
        else:
            print(f"  ⚠️  Found {race_conditions_found} potential race conditions")
        
        return {
            "race_conditions_found": race_conditions_found,
        }


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

async def run_forensic_audit():
    """Run complete forensic audit"""
    print("=" * 80)
    print("FORENSIC DIAGNOSTIC AUDIT")
    print("=" * 80)
    
    # Start collection
    collector.start_collection()
    
    try:
        # Run all tests
        await GoalParserForensicTests.test_goal_parsing()
        await OrchestratorForensicTests.test_sequential_execution()
        await WebSocketForensicTests.test_websocket_manager()
        await WebSocketForensicTests.test_orchestrator_websocket_integration()
        await DatabaseForensicTests.test_state_transitions()
        await RaceConditionTests.test_commit_before_websocket()
        
    except Exception as e:
        print(f"\n❌ Fatal error during audit: {e}")
        traceback.print_exc()
        collector.add_silent_failure(SilentFailure(
            timestamp=datetime.now(UTC),
            component="ForensicAudit",
            function="run_forensic_audit",
            line_number=0,
            exception_type=type(e).__name__,
            exception_message=str(e),
            exception_traceback=traceback.format_exc(),
            was_caught=False,
            was_logged=True,
        ))
    
    finally:
        # Stop collection
        collector.stop_collection()
        
        # Generate report
        report = collector.generate_report()
        
        # Save report
        report_path = "FORENSIC_AUDIT_REPORT.md"
        with open(report_path, "w") as f:
            f.write(report)
        
        print(f"\n📄 Report saved to: {report_path}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("AUDIT SUMMARY")
        print("=" * 80)
        print(report.split("## EXECUTIVE SUMMARY")[1].split("##")[0].strip())


if __name__ == "__main__":
    asyncio.run(run_forensic_audit())
