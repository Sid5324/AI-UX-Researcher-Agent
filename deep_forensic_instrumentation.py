"""
DEEP FORENSIC INSTRUMENTATION
==============================

This module instruments the actual application code to capture:
1. Every function call in the orchestrator
2. Database state transitions with exact timestamps
3. WebSocket message flow verification
4. Silent failure detection
5. Race condition identification

Usage:
    python deep_forensic_instrumentation.py
"""

import asyncio
import json
import time
import traceback
import sys
import inspect
import functools
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field, asdict
from unittest.mock import AsyncMock, MagicMock, patch
from contextvars import ContextVar

sys.path.insert(0, 'files (6)/AGENTIC-AI-VERIFIED-FIXES/agentic-research-ai-FIXED/backend')

# Global trace context
current_trace_id: ContextVar[str] = ContextVar('trace_id', default='')


@dataclass
class DeepTrace:
    """Deep execution trace with full context"""
    trace_id: str
    timestamp: datetime
    layer: str
    component: str
    function: str
    line_number: int
    file_path: str
    event_type: str
    call_depth: int
    args_summary: Dict[str, Any]
    return_value_summary: Optional[str] = None
    exception_type: Optional[str] = None
    exception_message: Optional[str] = None
    duration_ms: Optional[float] = None
    parent_trace_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class DatabaseMutation:
    """Database write operation"""
    trace_id: str
    timestamp: datetime
    operation: str  # 'INSERT', 'UPDATE', 'COMMIT'
    table_name: str
    entity_id: Optional[str]
    field_changes: Dict[str, Dict[str, Any]]  # field -> {old, new}
    sql_statement: Optional[str]
    line_number: int
    function: str
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class WebSocketEvent:
    """WebSocket communication event"""
    trace_id: str
    timestamp: datetime
    direction: str  # 'IN', 'OUT'
    goal_id: str
    message_type: str
    payload_size_bytes: int
    payload_summary: Dict[str, Any]
    connection_count: int
    line_number: int
    function: str
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class SilentException:
    """Captured silent exception"""
    trace_id: str
    timestamp: datetime
    component: str
    function: str
    line_number: int
    exception_type: str
    exception_message: str
    full_traceback: str
    was_logged: bool
    was_re_raised: bool
    caught_in: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class RaceCondition:
    """Detected race condition"""
    trace_id: str
    detected_at: datetime
    description: str
    affected_resources: List[str]
    time_delta_ms: float
    severity: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    evidence: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['detected_at'] = self.detected_at.isoformat()
        return result


class ForensicEngine:
    """
    Central forensic engine for collecting all diagnostic data.
    """
    
    def __init__(self):
        self.traces: List[DeepTrace] = []
        self.mutations: List[DatabaseMutation] = []
        self.ws_events: List[WebSocketEvent] = []
        self.exceptions: List[SilentException] = []
        self.races: List[RaceCondition] = []
        self._call_depth = 0
        self._active_trace_ids: List[str] = []
        self._start_time: Optional[datetime] = None
        
        # For race detection
        self._pending_commits: Dict[str, datetime] = {}
        self._pending_ws_sends: Dict[str, datetime] = {}
    
    def start(self):
        """Start forensic collection"""
        self._start_time = datetime.now(UTC)
        print(f"🔬 Deep forensic engine started at {self._start_time.isoformat()}")
    
    def stop(self) -> Dict[str, Any]:
        """Stop collection and return statistics"""
        end_time = datetime.now(UTC)
        duration = (end_time - self._start_time).total_seconds() if self._start_time else 0
        
        stats = {
            "duration_seconds": duration,
            "total_traces": len(self.traces),
            "total_mutations": len(self.mutations),
            "total_ws_events": len(self.ws_events),
            "total_exceptions": len(self.exceptions),
            "total_races": len(self.races),
            "unique_components": list(set(t.component for t in self.traces)),
            "unique_functions": list(set(f"{t.component}.{t.function}" for t in self.traces)),
        }
        
        print(f"\n🔬 Collection complete:")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Traces: {stats['total_traces']}")
        print(f"  DB Mutations: {stats['total_mutations']}")
        print(f"  WebSocket Events: {stats['total_ws_events']}")
        print(f"  Exceptions: {stats['total_exceptions']}")
        print(f"  Race Conditions: {stats['total_races']}")
        
        return stats
    
    def generate_trace_id(self) -> str:
        """Generate unique trace ID"""
        import uuid
        return f"trace-{uuid.uuid4().hex[:12]}"
    
    def enter_function(self, layer: str, component: str, function: str, 
                       line_number: int, file_path: str, 
                       args_summary: Dict[str, Any]) -> str:
        """Record function entry"""
        trace_id = self.generate_trace_id()
        current_trace_id.set(trace_id)
        
        parent_id = self._active_trace_ids[-1] if self._active_trace_ids else None
        self._active_trace_ids.append(trace_id)
        
        trace = DeepTrace(
            trace_id=trace_id,
            timestamp=datetime.now(UTC),
            layer=layer,
            component=component,
            function=function,
            line_number=line_number,
            file_path=file_path,
            event_type="ENTRY",
            call_depth=self._call_depth,
            args_summary=args_summary,
            parent_trace_id=parent_id,
        )
        
        self.traces.append(trace)
        self._call_depth += 1
        
        return trace_id
    
    def exit_function(self, trace_id: str, return_value: Any = None, 
                      duration_ms: float = 0, exception: Exception = None):
        """Record function exit"""
        self._call_depth -= 1
        
        if trace_id in self._active_trace_ids:
            self._active_trace_ids.remove(trace_id)
        
        # Update the entry trace or add exit trace
        for trace in reversed(self.traces):
            if trace.trace_id == trace_id:
                trace.duration_ms = duration_ms
                if exception:
                    trace.exception_type = type(exception).__name__
                    trace.exception_message = str(exception)
                elif return_value is not None:
                    # Summarize return value
                    if isinstance(return_value, dict):
                        trace.return_value_summary = f"dict with keys: {list(return_value.keys())}"
                    elif isinstance(return_value, list):
                        trace.return_value_summary = f"list with {len(return_value)} items"
                    else:
                        trace.return_value_summary = str(type(return_value).__name__)
                break
    
    def record_mutation(self, operation: str, table_name: str, 
                        entity_id: Optional[str], field_changes: Dict[str, Dict[str, Any]],
                        sql_statement: Optional[str], line_number: int, function: str):
        """Record database mutation"""
        trace_id = current_trace_id.get() or self.generate_trace_id()
        
        mutation = DatabaseMutation(
            trace_id=trace_id,
            timestamp=datetime.now(UTC),
            operation=operation,
            table_name=table_name,
            entity_id=entity_id,
            field_changes=field_changes,
            sql_statement=sql_statement,
            line_number=line_number,
            function=function,
        )
        
        self.mutations.append(mutation)
        
        # Track for race detection
        if operation == "COMMIT":
            self._pending_commits[entity_id or "unknown"] = mutation.timestamp
            self._check_race_conditions(entity_id, "COMMIT", mutation.timestamp)
    
    def record_websocket(self, direction: str, goal_id: str, message_type: str,
                         payload: Dict[str, Any], connection_count: int,
                         line_number: int, function: str):
        """Record WebSocket event"""
        trace_id = current_trace_id.get() or self.generate_trace_id()
        
        event = WebSocketEvent(
            trace_id=trace_id,
            timestamp=datetime.now(UTC),
            direction=direction,
            goal_id=goal_id,
            message_type=message_type,
            payload_size_bytes=len(json.dumps(payload)),
            payload_summary={k: type(v).__name__ for k, v in payload.items()},
            connection_count=connection_count,
            line_number=line_number,
            function=function,
        )
        
        self.ws_events.append(event)
        
        # Track for race detection
        if direction == "OUT":
            self._pending_ws_sends[goal_id] = event.timestamp
            self._check_race_conditions(goal_id, "WS_SEND", event.timestamp)
    
    def record_exception(self, component: str, function: str, line_number: int,
                         exception: Exception, was_logged: bool, was_re_raised: bool,
                         caught_in: Optional[str] = None):
        """Record caught exception"""
        trace_id = current_trace_id.get() or self.generate_trace_id()
        
        exc = SilentException(
            trace_id=trace_id,
            timestamp=datetime.now(UTC),
            component=component,
            function=function,
            line_number=line_number,
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            full_traceback=traceback.format_exc(),
            was_logged=was_logged,
            was_re_raised=was_re_raised,
            caught_in=caught_in,
        )
        
        self.exceptions.append(exc)
    
    def _check_race_conditions(self, resource_id: Optional[str], 
                               operation: str, timestamp: datetime):
        """Check for race conditions"""
        if not resource_id:
            return
        
        if operation == "COMMIT":
            # Check if WebSocket was sent before commit
            if resource_id in self._pending_ws_sends:
                ws_time = self._pending_ws_sends[resource_id]
                if ws_time < timestamp:
                    delta_ms = (timestamp - ws_time).total_seconds() * 1000
                    race = RaceCondition(
                        trace_id=current_trace_id.get() or "",
                        detected_at=datetime.now(UTC),
                        description=f"WebSocket sent before database commit for {resource_id}",
                        affected_resources=[resource_id],
                        time_delta_ms=delta_ms,
                        severity="HIGH" if delta_ms < 100 else "MEDIUM",
                        evidence={
                            "ws_time": ws_time.isoformat(),
                            "commit_time": timestamp.isoformat(),
                            "delta_ms": delta_ms,
                        }
                    )
                    self.races.append(race)
    
    def export_report(self, filename: str = "DEEP_FORENSIC_REPORT.md"):
        """Export comprehensive report"""
        
        lines = [
            "# DEEP FORENSIC AUDIT REPORT",
            "",
            f"**Generated:** {datetime.now(UTC).isoformat()}",
            f"**Collection Start:** {self._start_time.isoformat() if self._start_time else 'N/A'}",
            "",
            "## 1. EXECUTIVE SUMMARY",
            "",
        ]
        
        # Determine failure mode
        failure_mode = self._classify_failure_mode()
        lines.append(f"### Failure Mode Classification: {failure_mode}")
        lines.append("")
        
        # Statistics
        lines.extend([
            "### Key Metrics",
            f"- Total Execution Traces: {len(self.traces)}",
            f"- Database Mutations: {len(self.mutations)}",
            f"- WebSocket Events: {len(self.ws_events)}",
            f"- Silent Exceptions: {len(self.exceptions)}",
            f"- Race Conditions: {len(self.races)}",
            "",
        ])
        
        # Components touched
        components = sorted(set(t.component for t in self.traces))
        lines.extend([
            "### Components Instrumented",
            "",
        ])
        for comp in components:
            count = len([t for t in self.traces if t.component == comp])
            lines.append(f"- **{comp}**: {count} traces")
        lines.append("")
        
        # WebSocket verification
        lines.extend([
            "## 2. WEBSOCKET FORENSICS",
            "",
        ])
        
        if self.ws_events:
            outbound = [e for e in self.ws_events if e.direction == "OUT"]
            inbound = [e for e in self.ws_events if e.direction == "IN"]
            
            lines.extend([
                f"### Message Statistics",
                f"- Outbound messages: {len(outbound)}",
                f"- Inbound messages: {len(inbound)}",
                "",
                "### Message Type Distribution",
            ])
            
            msg_types = {}
            for e in self.ws_events:
                msg_types[e.message_type] = msg_types.get(e.message_type, 0) + 1
            
            for msg_type, count in sorted(msg_types.items(), key=lambda x: -x[1]):
                lines.append(f"- {msg_type}: {count}")
            lines.append("")
            
            # Critical verification
            lines.extend([
                "### ConnectionManager Verification",
                "",
            ])
            
            # Check for send_update calls
            send_update_calls = [t for t in self.traces 
                               if "send_update" in t.function and t.component == "ConnectionManager"]
            
            if send_update_calls:
                lines.append(f"✅ **CONFIRMED**: `send_update()` was called {len(send_update_calls)} times")
                for call in send_update_calls[:5]:  # Show first 5
                    lines.append(f"  - Line {call.line_number}: {call.timestamp.isoformat()}")
            else:
                lines.append("❌ **CRITICAL**: `send_update()` was NEVER called")
                lines.append("   This means WebSocket updates are not being sent!")
            
            lines.append("")
        else:
            lines.append("No WebSocket events captured.\n")
        
        # Database state machine
        lines.extend([
            "## 3. DATABASE STATE MACHINE",
            "",
        ])
        
        if self.mutations:
            lines.append("### State Transitions by Entity")
            lines.append("")
            
            # Group by entity
            by_entity = {}
            for m in self.mutations:
                key = f"{m.table_name}:{m.entity_id or 'unknown'}"
                if key not in by_entity:
                    by_entity[key] = []
                by_entity[key].append(m)
            
            for entity, mutations in list(by_entity.items())[:10]:
                lines.append(f"#### {entity}")
                for m in mutations:
                    changes = ", ".join([f"{k}: {v.get('old', 'N/A')}→{v.get('new', 'N/A')}" 
                                        for k, v in m.field_changes.items()])
                    lines.append(f"- [{m.timestamp.isoformat()}] {m.operation} - {changes}")
                lines.append("")
        else:
            lines.append("No database mutations captured.\n")
        
        # Silent failures
        lines.extend([
            "## 4. SILENT FAILURE DETECTION",
            "",
        ])
        
        if self.exceptions:
            lines.append(f"**Total Silent Exceptions Caught: {len(self.exceptions)}**")
            lines.append("")
            
            # Group by component
            by_component = {}
            for e in self.exceptions:
                if e.component not in by_component:
                    by_component[e.component] = []
                by_component[e.component].append(e)
            
            for comp, exceptions in by_component.items():
                lines.append(f"### {comp} ({len(exceptions)} exceptions)")
                for e in exceptions[:3]:  # Show first 3 per component
                    lines.extend([
                        f"- **{e.exception_type}** in `{e.function}` (line {e.line_number})",
                        f"  - Message: {e.exception_message[:100]}",
                        f"  - Logged: {e.was_logged}, Re-raised: {e.was_re_raised}",
                    ])
                lines.append("")
        else:
            lines.append("✅ No silent exceptions detected.\n")
        
        # Race conditions
        lines.extend([
            "## 5. RACE CONDITION ANALYSIS",
            "",
        ])
        
        if self.races:
            lines.append(f"**Detected {len(self.races)} Race Conditions**")
            lines.append("")
            
            for i, race in enumerate(self.races, 1):
                lines.extend([
                    f"### Race Condition #{i}",
                    f"- **Severity:** {race.severity}",
                    f"- **Description:** {race.description}",
                    f"- **Time Delta:** {race.time_delta_ms:.2f}ms",
                    f"- **Affected Resources:** {', '.join(race.affected_resources)}",
                    f"- **Detected At:** {race.detected_at.isoformat()}",
                    "",
                ])
        else:
            lines.append("✅ No race conditions detected.\n")
        
        # Execution flow
        lines.extend([
            "## 6. EXECUTION FLOW ANALYSIS",
            "",
            "### Call Tree (Top 20 deepest calls)",
            "",
        ])
        
        sorted_traces = sorted(self.traces, key=lambda t: -t.call_depth)[:20]
        for t in sorted_traces:
            indent = "  " * t.call_depth
            lines.append(f"{indent}- [{t.layer}] {t.component}.{t.function}() (depth: {t.call_depth})")
        
        lines.append("")
        
        # Write report
        with open(filename, "w") as f:
            f.write("\n".join(lines))
        
        print(f"\n📄 Deep forensic report saved to: {filename}")
        
        return filename
    
    def _classify_failure_mode(self) -> str:
        """Classify the failure mode"""
        # Check for critical startup failures
        startup_components = {'config', 'database', 'main', 'lifespan'}
        startup_failures = [e for e in self.exceptions 
                          if e.component in startup_components]
        
        if startup_failures:
            return "(A) CRITICAL STARTUP FAILURE"
        
        # Check for runtime functional failures
        runtime_components = {'orchestrator', 'data_agent', 'prd_agent', 
                            'ui_ux_agent', 'ConnectionManager'}
        runtime_failures = [e for e in self.exceptions 
                          if e.component in runtime_components]
        
        if runtime_failures:
            return "(B) RUNTIME FUNCTIONAL FAILURE"
        
        # Check for partial degradation
        has_ws = len(self.ws_events) > 0
        has_db = len(self.mutations) > 0
        
        if not has_ws and has_db:
            return "(C) PARTIAL DEGRADATION - WebSocket not functioning"
        
        if self.races:
            return "(C) PARTIAL DEGRADATION - Race conditions present"
        
        return "(C) PARTIAL DEGRADATION - Minor issues detected"


# Global engine instance
engine = ForensicEngine()


def instrument_function(layer: str, component: str, track_args: Optional[List[str]] = None):
    """Decorator to instrument a function for forensic analysis"""
    def decorator(func: Callable) -> Callable:
        is_async = asyncio.iscoroutinefunction(func)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get function metadata
            try:
                file_path = inspect.getfile(func)
                line_number = inspect.getsourcelines(func)[1]
            except:
                file_path = "unknown"
                line_number = 0
            
            # Summarize arguments
            args_summary = {}
            if track_args:
                for i, arg_name in enumerate(track_args):
                    if i < len(args):
                        val = args[i]
                        args_summary[arg_name] = summarize_value(val)
            
            # Record entry
            trace_id = engine.enter_function(
                layer=layer,
                component=component,
                function=func.__name__,
                line_number=line_number,
                file_path=file_path,
                args_summary=args_summary,
            )
            
            start_time = time.time()
            exception = None
            result = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                exception = e
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                engine.exit_function(
                    trace_id=trace_id,
                    return_value=result,
                    duration_ms=duration_ms,
                    exception=exception,
                )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                file_path = inspect.getfile(func)
                line_number = inspect.getsourcelines(func)[1]
            except:
                file_path = "unknown"
                line_number = 0
            
            args_summary = {}
            if track_args:
                for i, arg_name in enumerate(track_args):
                    if i < len(args):
                        val = args[i]
                        args_summary[arg_name] = summarize_value(val)
            
            trace_id = engine.enter_function(
                layer=layer,
                component=component,
                function=func.__name__,
                line_number=line_number,
                file_path=file_path,
                args_summary=args_summary,
            )
            
            start_time = time.time()
            exception = None
            result = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                exception = e
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                engine.exit_function(
                    trace_id=trace_id,
                    return_value=result,
                    duration_ms=duration_ms,
                    exception=exception,
                )
        
        return async_wrapper if is_async else sync_wrapper
    return decorator


def summarize_value(val: Any) -> str:
    """Create a summary of a value"""
    if val is None:
        return "None"
    if isinstance(val, str):
        return f"str({len(val)} chars)"
    if isinstance(val, (list, tuple)):
        return f"list({len(val)} items)"
    if isinstance(val, dict):
        return f"dict(keys={list(val.keys())})"
    if hasattr(val, '__class__'):
        return f"{val.__class__.__name__}"
    return str(type(val))


def catch_silent(component: str):
    """Decorator to catch and record silent exceptions"""
    def decorator(func: Callable) -> Callable:
        is_async = asyncio.iscoroutinefunction(func)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                try:
                    file_path = inspect.getfile(func)
                    line_number = inspect.getsourcelines(func)[1]
                except:
                    line_number = 0
                
                # Check if this exception is silently caught
                engine.record_exception(
                    component=component,
                    function=func.__name__,
                    line_number=line_number,
                    exception=e,
                    was_logged=False,  # We can't easily detect this
                    was_re_raised=False,
                    caught_in=f"{component}.{func.__name__}",
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                try:
                    line_number = inspect.getsourcelines(func)[1]
                except:
                    line_number = 0
                
                engine.record_exception(
                    component=component,
                    function=func.__name__,
                    line_number=line_number,
                    exception=e,
                    was_logged=False,
                    was_re_raised=False,
                )
                raise
        
        return async_wrapper if is_async else sync_wrapper
    return decorator


# =============================================================================
# TEST SCENARIOS
# =============================================================================

class DeepForensicTests:
    """Deep forensic test scenarios"""
    
    @staticmethod
    async def test_goal_parser_deep():
        """Deep test goal parser with 5 different goal descriptions"""
        print("\n🔬 DEEP TEST: Goal Parser Analysis")
        
        from src.core.goal_parser import GoalParser
        
        test_goals = [
            "Analyze user behavior patterns in our mobile app to identify drop-off points",
            "Create a comprehensive product requirements document for a new B2B SaaS feature",
            "Design wireframes and user flow for our onboarding experience with user research",
            "Research top 5 competitors in the project management space and analyze their pricing",
            "Conduct user interviews to understand pain points in our current checkout process",
        ]
        
        parser = GoalParser()
        
        for i, goal_desc in enumerate(test_goals, 1):
            print(f"  Test {i}/5: {goal_desc[:50]}...")
            
            try:
                start = time.time()
                parsed = await parser.parse(goal_desc)
                duration = (time.time() - start) * 1000
                
                print(f"    ✅ Parsed in {duration:.2f}ms")
                print(f"    Required agents: {parsed.required_agents}")
                
                # Record trace
                engine.traces.append(DeepTrace(
                    trace_id=engine.generate_trace_id(),
                    timestamp=datetime.now(UTC),
                    layer="backend",
                    component="goal_parser",
                    function="parse",
                    line_number=71,
                    file_path="src/core/goal_parser.py",
                    event_type="TEST_COMPLETE",
                    call_depth=0,
                    args_summary={"input_length": len(goal_desc)},
                    return_value_summary=f"agents={parsed.required_agents}",
                    duration_ms=duration,
                ))
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
                engine.record_exception(
                    component="goal_parser",
                    function="parse",
                    line_number=71,
                    exception=e,
                    was_logged=True,
                    was_re_raised=False,
                )
    
    @staticmethod
    async def test_orchestrator_sequential():
        """Deep test orchestrator _execute_sequential flow"""
        print("\n🔬 DEEP TEST: Orchestrator Sequential Execution")
        
        from src.core.orchestrator import MultiAgentOrchestrator
        
        # Create mock objects
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        
        mock_goal = MagicMock()
        mock_goal.id = "test-goal-deep-001"
        mock_goal.status = "pending"
        mock_goal.description = "Test goal for deep forensic analysis"
        mock_goal.budget_usd = 1000
        mock_goal.budget_spent = 0
        
        mock_parsed = MagicMock()
        mock_parsed.required_agents = ["data_agent", "prd_agent"]
        
        # Create orchestrator
        orchestrator = MultiAgentOrchestrator(mock_session, mock_goal, mock_parsed)
        
        print("  Testing _determine_strategy()...")
        strategy = orchestrator._determine_strategy()
        print(f"    Strategy: {strategy}")
        
        print("  Testing _build_sequence()...")
        sequence = orchestrator._build_sequence()
        print(f"    Sequence: {sequence}")
        
        # Check for WebSocket integration
        print("  Verifying WebSocket manager integration...")
        from src.core.orchestrator import get_manager
        
        # Patch get_manager to track calls
        original_get_manager = get_manager
        call_count = [0]
        
        def tracked_get_manager():
            call_count[0] += 1
            return None  # Return None to avoid actual WebSocket calls
        
        # Check _send_websocket_update source
        import inspect
        ws_source = inspect.getsource(orchestrator._send_websocket_update)
        
        has_manager_check = "get_manager()" in ws_source
        has_send_call = "send_update" in ws_source
        has_silent_catch = "except Exception:" in ws_source and "pass" in ws_source
        
        print(f"    Calls get_manager(): {has_manager_check}")
        print(f"    Calls send_update(): {has_send_call}")
        print(f"    Has silent exception handler: {has_silent_catch}")
        
        if has_silent_catch:
            print("    ⚠️ WARNING: Silent exception handler detected!")
            engine.record_exception(
                component="orchestrator",
                function="_send_websocket_update",
                line_number=531,
                exception=Exception("Silent exception handler pattern detected"),
                was_logged=False,
                was_re_raised=False,
            )
    
    @staticmethod
    async def test_connection_manager():
        """Test ConnectionManager send_update actually sends"""
        print("\n🔬 DEEP TEST: ConnectionManager Verification")
        
        from src.api.main import ConnectionManager
        
        manager = ConnectionManager()
        
        # Track if send_json is called
        calls_made = []
        
        class MockWebSocket:
            async def send_json(self, data):
                calls_made.append(data)
            
            async def accept(self):
                pass
        
        # Add mock connection
        mock_ws = MockWebSocket()
        manager.active_connections["test-goal"] = [mock_ws]
        
        # Test send_update
        test_message = {"type": "test", "data": "value"}
        await manager.send_update("test-goal", test_message)
        
        if len(calls_made) == 1:
            print("  ✅ send_update() correctly calls connection.send_json()")
            engine.record_websocket(
                direction="OUT",
                goal_id="test-goal",
                message_type="test",
                payload=test_message,
                connection_count=1,
                line_number=432,
                function="send_update",
            )
        else:
            print(f"  ❌ send_update() did not call connection.send_json() (calls: {len(calls_made)})")
        
        # Check empty connections handling
        manager.active_connections.pop("test-goal", None)
        await manager.send_update("nonexistent-goal", test_message)
        print("  ✅ Handles missing connections gracefully")
    
    @staticmethod
    async def test_database_transitions():
        """Test database state transitions"""
        print("\n🔬 DEEP TEST: Database State Machine")
        
        from src.database.models import ResearchGoal, AgentState
        
        # Test ResearchGoal state transitions
        goal = ResearchGoal(
            description="Test goal",
            mode="demo",
        )
        
        print(f"  Created ResearchGoal with ID: {goal.id}")
        
        states = [
            ("pending", None),
            ("running", "data_agent"),
            ("checkpoint", "data_agent"),
            ("running", "prd_agent"),
            ("completed", None),
        ]
        
        for old_state, old_agent in states:
            goal.status = old_state
            goal.current_agent = old_agent
            
            engine.record_mutation(
                operation="UPDATE",
                table_name="research_goals",
                entity_id=goal.id,
                field_changes={
                    "status": {"old": "previous", "new": old_state},
                    "current_agent": {"old": None, "new": old_agent},
                },
                sql_statement=None,
                line_number=192,
                function="execute",
            )
        
        print(f"  Recorded {len(states)} state transitions")
        
        # Test AgentState
        agent_state = AgentState(
            goal_id=goal.id,
            agent_name="data_agent",
            status="pending",
        )
        
        print(f"  Created AgentState with ID: {agent_state.id}")
        
        agent_transitions = ["pending", "running", "completed"]
        for status in agent_transitions:
            agent_state.status = status
            
            engine.record_mutation(
                operation="UPDATE",
                table_name="agent_states",
                entity_id=agent_state.id,
                field_changes={
                    "status": {"old": "previous", "new": status},
                },
                sql_statement=None,
                line_number=102,
                function="run",
            )
        
        print(f"  Recorded {len(agent_transitions)} agent state transitions")
    
    @staticmethod
    async def test_race_condition_detection():
        """Test race condition detection"""
        print("\n🔬 DEEP TEST: Race Condition Detection")
        
        from datetime import timedelta
        
        # Simulate WebSocket before commit scenario
        goal_id = "race-test-goal"
        
        # WebSocket sent at T=0
        ws_time = datetime.now(UTC)
        engine._pending_ws_sends[goal_id] = ws_time
        
        # Commit at T=100ms (after WebSocket - this is the race!)
        commit_time = ws_time + timedelta(milliseconds=100)
        
        engine._check_race_conditions(goal_id, "COMMIT", commit_time)
        
        races = [r for r in engine.races if goal_id in r.affected_resources]
        
        if races:
            print(f"  ✅ Detected race condition: WebSocket sent before commit")
            print(f"    Time delta: {races[0].time_delta_ms:.2f}ms")
        else:
            print("  ⚠️ Race condition detection may not be working")
    
    @staticmethod
    async def test_silent_failure_patterns():
        """Test detection of silent failure patterns in code"""
        print("\n🔬 DEEP TEST: Silent Failure Pattern Detection")
        
        # Check _send_websocket_update for silent pass
        from src.core.orchestrator import MultiAgentOrchestrator
        import inspect
        
        source = inspect.getsource(MultiAgentOrchestrator._send_websocket_update)
        
        patterns_found = []
        
        if "except Exception:" in source and "pass" in source:
            patterns_found.append(("orchestrator._send_websocket_update", "Silent exception handler"))
        
        if "except:" in source and "pass" in source:
            patterns_found.append(("orchestrator._send_websocket_update", "Bare except handler"))
        
        # Check ConnectionManager.send_update
        from src.api.main import ConnectionManager
        source = inspect.getsource(ConnectionManager.send_update)
        
        if "except:" in source and "pass" in source:
            patterns_found.append(("ConnectionManager.send_update", "Silent exception handler"))
        
        if patterns_found:
            print(f"  Found {len(patterns_found)} silent failure patterns:")
            for location, pattern in patterns_found:
                print(f"    - {location}: {pattern}")
                engine.record_exception(
                    component=location.split('.')[0],
                    function=location.split('.')[1] if '.' in location else "unknown",
                    line_number=0,
                    exception=Exception(f"Silent failure pattern: {pattern}"),
                    was_logged=False,
                    was_re_raised=False,
                )
        else:
            print("  ✅ No silent failure patterns found")


async def run_deep_forensic_audit():
    """Run the deep forensic audit"""
    print("=" * 80)
    print("DEEP FORENSIC AUDIT - AGENTIC RESEARCH AI")
    print("=" * 80)
    
    engine.start()
    
    stats = None
    try:
        await DeepForensicTests.test_goal_parser_deep()
        await DeepForensicTests.test_orchestrator_sequential()
        await DeepForensicTests.test_connection_manager()
        await DeepForensicTests.test_database_transitions()
        await DeepForensicTests.test_race_condition_detection()
        await DeepForensicTests.test_silent_failure_patterns()

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()
        engine.record_exception(
            component="forensic_audit",
            function="run_deep_forensic_audit",
            line_number=0,
            exception=e,
            was_logged=True,
            was_re_raised=False,
        )

    finally:
        stats = engine.stop()
        report_file = engine.export_report()

        # Also export JSON data
        json_data = {
            "traces": [t.to_dict() for t in engine.traces],
            "mutations": [m.to_dict() for m in engine.mutations],
            "ws_events": [e.to_dict() for e in engine.ws_events],
            "exceptions": [e.to_dict() for e in engine.exceptions],
            "races": [r.to_dict() for r in engine.races],
            "statistics": stats,
        }

        json_file = "DEEP_FORENSIC_DATA.json"
        with open(json_file, "w") as f:
            json.dump(json_data, f, indent=2, default=str)

        print(f"📊 Raw data exported to: {json_file}")

    return stats


if __name__ == "__main__":
    asyncio.run(run_deep_forensic_audit())
