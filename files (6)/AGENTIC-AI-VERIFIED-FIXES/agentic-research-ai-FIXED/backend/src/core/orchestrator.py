"""
Multi-Agent Orchestrator
========================

Coordinates execution across multiple agents:
- Determines agent execution order
- Manages handoffs between agents
- Maintains shared project context
- Handles checkpoints and approvals
- Orchestrates parallel vs sequential execution
"""

from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
from enum import Enum

from src.core.config import get_settings, constants
from src.database.models import ResearchGoal, AgentState, Checkpoint
from src.database.session import AsyncSession
from src.agents.base import BaseAgent
from src.core.goal_parser import ParsedGoal

# WebSocket manager for real-time updates
# Import lazily to avoid circular imports
manager = None

def get_manager():
    global manager
    if manager is None:
        # Import here to avoid circular imports
        from src.api.main import manager as ws_manager
        manager = ws_manager
    return manager


settings = get_settings()


class ExecutionStrategy(Enum):
    """Agent execution strategies"""
    SEQUENTIAL = "sequential"  # One after another
    PARALLEL = "parallel"  # All at once
    CONDITIONAL = "conditional"  # Based on results


class AgentHandoff:
    """
    Represents work handoff between agents.
    
    When one agent completes, it creates a handoff for the next agent.
    """
    
    def __init__(
        self,
        from_agent: str,
        to_agent: str,
        deliverable: Dict[str, Any],
        trigger: str,
        key_fields: List[str],
        action_required: str,
    ):
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.deliverable = deliverable
        self.trigger = trigger
        self.key_fields = key_fields
        self.action_required = action_required
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "deliverable": self.deliverable,
            "trigger": self.trigger,
            "key_fields": self.key_fields,
            "action_required": self.action_required,
            "created_at": self.created_at.isoformat(),
        }


class SharedProjectContext:
    """
    Context shared across all agents in a project.
    
    This is the "project memory" that all agents can read and write to.
    """
    
    def __init__(self, goal: ResearchGoal, parsed_goal: ParsedGoal):
        self.goal = goal
        self.parsed_goal = parsed_goal
        
        # Accumulated knowledge
        self.data_findings: Optional[Dict[str, Any]] = None
        self.product_strategy: Optional[Dict[str, Any]] = None
        self.design_specs: Optional[Dict[str, Any]] = None
        self.validation_results: List[Dict[str, Any]] = []
        self.competitor_analysis: Optional[Dict[str, Any]] = None
        self.interview_insights: List[Dict[str, Any]] = []
        self.feedback_analysis: Optional[Dict[str, Any]] = None
        
        # User preferences
        self.brand_guidelines: Optional[Dict[str, Any]] = None
        self.tech_stack: Optional[Dict[str, Any]] = None
        self.constraints: List[str] = []
        
        # Decisions log
        self.decisions: List[Dict[str, Any]] = []
        
        # Handoffs
        self.handoffs: List[AgentHandoff] = []
    
    def add_decision(
        self,
        decision: str,
        rationale: str,
        confidence: float,
        agent: str,
    ) -> None:
        """Log a key decision"""
        self.decisions.append({
            "decision": decision,
            "rationale": rationale,
            "confidence": confidence,
            "agent": agent,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    def add_handoff(self, handoff: AgentHandoff) -> None:
        """Register agent handoff"""
        self.handoffs.append(handoff)
    
    def get_context_for_agent(self, agent_name: str) -> Dict[str, Any]:
        """Get relevant context for specific agent"""
        context = {
            "goal": self.goal.description,
            "mode": self.goal.mode,
            "budget_remaining": self.goal.budget_usd - self.goal.budget_spent if self.goal.budget_usd else None,
            "constraints": self.constraints,
        }
        
        # Add previous agent outputs
        if self.data_findings:
            context["data_findings"] = self.data_findings
        if self.product_strategy:
            context["product_strategy"] = self.product_strategy
        if self.design_specs:
            context["design_specs"] = self.design_specs
        if self.competitor_analysis:
            context["competitor_analysis"] = self.competitor_analysis
        if self.interview_insights:
            context["interview_insights"] = self.interview_insights
        if self.feedback_analysis:
            context["feedback_analysis"] = self.feedback_analysis
        if self.validation_results:
            context["validation_results"] = self.validation_results
        
        return context


class MultiAgentOrchestrator:
    """
    Orchestrates execution across multiple agents.
    
    Responsibilities:
    - Determine which agents to run
    - Decide execution order (sequential/parallel)
    - Manage handoffs between agents
    - Handle checkpoints
    - Maintain shared context
    """
    
    def __init__(
        self,
        session: AsyncSession,
        goal: ResearchGoal,
        parsed_goal: ParsedGoal,
    ):
        self.session = session
        self.goal = goal
        self.parsed_goal = parsed_goal
        
        # Shared context
        self.context = SharedProjectContext(goal, parsed_goal)
        
        # Execution plan
        self.execution_strategy = self._determine_strategy()
        self.agent_sequence = self._build_sequence()
    
    # =====================
    # Main Orchestration
    # =====================
    
    async def execute(self) -> Dict[str, Any]:
        """
        Execute multi-agent workflow.
        
        Returns:
            Dict with complete project results
        """
        self.goal.status = "running"
        await self.session.commit()
        
        try:
            if self.execution_strategy == ExecutionStrategy.SEQUENTIAL:
                results = await self._execute_sequential()
            elif self.execution_strategy == ExecutionStrategy.PARALLEL:
                results = await self._execute_parallel()
            else:
                results = await self._execute_conditional()
            
            if self.goal.status == "failed":
                return {
                    "success": False,
                    "error": self.goal.error_message,
                }

            # Mark goal as complete
            self.goal.status = "completed"
            self.goal.progress_percent = 100.0
            self.goal.findings = self.context.data_findings
            self.goal.final_output = {
                "data_findings": self.context.data_findings,
                "product_strategy": self.context.product_strategy,
                "design_specs": self.context.design_specs,
                "validation_results": self.context.validation_results,
                "competitor_analysis": self.context.competitor_analysis,
                "interview_insights": self.context.interview_insights,
                "feedback_analysis": self.context.feedback_analysis,
                "decisions": self.context.decisions,
            }
            
            await self.session.commit()
            
            # Create final checkpoint
            await self._create_checkpoint(
                agent_name="orchestrator",
                checkpoint_type="goal_complete",
                title="Goal completed successfully",
                description=f"All agents executed: {', '.join([r['agent'] for r in results])}",
            )
            
            # Send final WebSocket update
            await self._send_websocket_update({
                "type": "goal_completed",
                "goal_id": self.goal.id,
                "status": "completed",
                "progress_percent": 100,
                "final_output": self.goal.final_output,
            })
            
            return {
                "success": True,
                "strategy": self.execution_strategy.value,
                "agents_executed": [r["agent"] for r in results],
                "final_output": self.goal.final_output,
            }
        
        except Exception as e:
            self.goal.status = "failed"
            self.goal.error_message = str(e)
            await self.session.commit()
            
            return {
                "success": False,
                "error": str(e),
            }
    
    # =====================
    # Execution Strategies
    # =====================
    
    async def _execute_sequential(self) -> List[Dict[str, Any]]:
        """
        Execute agents one after another with comprehensive WebSocket events.
        
        FIXED: Added 7 event types:
        - goal_started
        - agent_started
        - progress_update
        - agent_completed
        - agent_failed
        - goal_completed
        - goal_failed
        """
        results = []
        total_agents = len(self.agent_sequence)
        
        # FIXED: Send goal_started event
        await self._send_websocket_update({
            "type": "goal_started",
            "goal_id": str(self.goal.id),
            "total_agents": total_agents,
            "agents": self.agent_sequence,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        for idx, agent_name in enumerate(self.agent_sequence):
            try:
                # Update goal status
                self.goal.current_agent = agent_name
                await self.session.commit()
                
                # Send progress update at start
                progress_start = (idx / total_agents) * 100
                await self._notify_progress(progress_start, agent_name, idx + 1, total_agents)
                
                # Notify agent started with enhanced info
                await self._notify_agent_started(agent_name, idx + 1, total_agents)
                
                # Create agent
                agent = await self._create_agent(agent_name)
                
                # Execute agent with timing
                start_time = datetime.utcnow()
                result = await agent.run()
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()
                
                results.append(result)
                
                if not result["success"]:
                    # FIXED: Send agent_failed event
                    await self._send_websocket_update({
                        "type": "agent_failed",
                        "goal_id": str(self.goal.id),
                        "agent": agent_name,
                        "agent_index": idx + 1,
                        "total_agents": total_agents,
                        "error": result.get("error", "Unknown error"),
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    
                    # FIXED: Send goal_failed event
                    await self._send_websocket_update({
                        "type": "goal_failed",
                        "goal_id": str(self.goal.id),
                        "failed_agent": agent_name,
                        "error": result.get("error", "Unknown error"),
                        "completed_agents": idx,
                        "total_agents": total_agents,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    
                    # Update goal status to failed
                    self.goal.status = "failed"
                    self.goal.error_message = f"Agent {agent_name} failed: {result.get('error', 'Unknown error')}"
                    await self.session.commit()
                    
                    break
                
                # Notify agent completed with enhanced info
                await self._notify_agent_completed(
                    agent_name, 
                    result["success"], 
                    result.get("output"),
                    idx + 1,
                    total_agents,
                    duration
                )
                
                # Store agent output in context
                await self._store_agent_output(agent_name, result["output"])
                
                # Create checkpoint for completed agent
                await self._create_checkpoint(
                    agent_name=agent_name,
                    checkpoint_type="agent_complete",
                    title=f"{agent_name} completed",
                    description=f"Agent {agent_name} finished successfully",
                )
                
                # Create handoff to next agent (if exists)
                if idx < len(self.agent_sequence) - 1:
                    next_agent = self.agent_sequence[idx + 1]
                    handoff = self._create_handoff(agent_name, next_agent, result["output"])
                    self.context.add_handoff(handoff)
                    
                    # FIXED: Send handoff event
                    await self._send_websocket_update({
                        "type": "agent_handoff",
                        "goal_id": str(self.goal.id),
                        "from_agent": agent_name,
                        "to_agent": next_agent,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
            
            except Exception as e:
                # FIXED: Send agent_error event for exceptions
                await self._send_websocket_update({
                    "type": "agent_error",
                    "goal_id": str(self.goal.id),
                    "agent": agent_name,
                    "agent_index": idx + 1,
                    "total_agents": total_agents,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                })
                
                # Update goal status to failed
                self.goal.status = "failed"
                self.goal.error_message = f"Agent {agent_name} error: {str(e)}"
                await self.session.commit()
                
                break
        
        # Final progress update
        await self._notify_progress(100, "complete", total_agents, total_agents)
        
        # FIXED: Send goal_completed event if all agents succeeded
        if len(results) == total_agents and all(r.get("success", False) for r in results):
            await self._send_websocket_update({
                "type": "goal_completed",
                "goal_id": str(self.goal.id),
                "total_agents": total_agents,
                "completed_agents": len(results),
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        return results
    
    async def _execute_parallel(self) -> List[Dict[str, Any]]:
        """Execute all agents simultaneously"""
        import asyncio
        
        # Create all agents
        tasks = []
        for agent_name in self.agent_sequence:
            agent = await self._create_agent(agent_name)
            tasks.append(agent.run())
        
        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "agent": self.agent_sequence[i],
                    "error": str(result),
                })
            else:
                processed_results.append(result)
                await self._store_agent_output(self.agent_sequence[i], result["output"])
        
        return processed_results
    
    async def _execute_conditional(self) -> List[Dict[str, Any]]:
        """Execute agents based on conditions"""
        results = []
        
        for agent_name in self.agent_sequence:
            # Check if this agent should run based on previous results
            if not self._should_run_agent(agent_name, results):
                continue
            
            self.goal.current_agent = agent_name
            await self.session.commit()
            
            agent = await self._create_agent(agent_name)
            result = await agent.run()
            results.append(result)
            
            if result["success"]:
                await self._store_agent_output(agent_name, result["output"])
        
        return results
    
    # =====================
    # Agent Management
    # =====================
    
    async def _create_agent(self, agent_name: str) -> BaseAgent:
        """
        Create agent instance with context.
        
        FIXED: Added all 7 agents - data, prd, ui_ux, validation, competitor, interview, feedback
        """
        # Get agent context
        agent_context = self.context.get_context_for_agent(agent_name)
        
        # Import agent class
        if agent_name == constants.AGENT_DATA:
            from src.agents.data.agent import DataAgent
            agent = DataAgent(self.session, self.goal)
        
        elif agent_name == constants.AGENT_PRD:
            from src.agents.prd.agent import PRDAgent
            agent = PRDAgent(self.session, self.goal)
        
        elif agent_name == constants.AGENT_UIUX:
            from src.agents.ui_ux.agent import UIUXAgent
            agent = UIUXAgent(self.session, self.goal)
        
        # FIXED: Added Validation Agent
        elif agent_name == constants.AGENT_VALIDATION:
            from src.agents.validation.agent import ValidationAgent
            agent = ValidationAgent(self.session, self.goal)
        
        # FIXED: Added Competitor Agent
        elif agent_name == constants.AGENT_COMPETITOR:
            from src.agents.competitor.agent import CompetitorAgent
            agent = CompetitorAgent(self.session, self.goal)
        
        # FIXED: Added Interview Agent
        elif agent_name == constants.AGENT_INTERVIEW:
            from src.agents.interview.agent import InterviewAgent
            agent = InterviewAgent(self.session, self.goal)
        
        # FIXED: Added Feedback Agent
        elif agent_name == constants.AGENT_FEEDBACK:
            from src.agents.feedback.agent import FeedbackAgent
            agent = FeedbackAgent(self.session, self.goal)
        
        else:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        # Inject context into agent
        agent.working_memory["shared_context"] = agent_context
        
        return agent
    
    async def _store_agent_output(
        self,
        agent_name: str,
        output: Dict[str, Any],
    ) -> None:
        """
        Store agent output in shared context.
        
        FIXED: Added storage for all 7 agent types.
        """
        if agent_name == constants.AGENT_DATA:
            self.context.data_findings = output
        
        elif agent_name == constants.AGENT_PRD:
            self.context.product_strategy = output
        
        elif agent_name == constants.AGENT_UIUX:
            self.context.design_specs = output
        
        # FIXED: Added storage for Validation Agent output
        elif agent_name == constants.AGENT_VALIDATION:
            if not hasattr(self.context, 'validation_results'):
                self.context.validation_results = []
            self.context.validation_results.append(output)
        
        # FIXED: Added storage for Competitor Agent output
        elif agent_name == constants.AGENT_COMPETITOR:
            self.context.competitor_analysis = output
        
        # FIXED: Added storage for Interview Agent output
        elif agent_name == constants.AGENT_INTERVIEW:
            if not hasattr(self.context, 'interview_insights'):
                self.context.interview_insights = []
            self.context.interview_insights.append(output)
        
        # FIXED: Added storage for Feedback Agent output
        elif agent_name == constants.AGENT_FEEDBACK:
            self.context.feedback_analysis = output
    
    def _should_run_agent(
        self,
        agent_name: str,
        previous_results: List[Dict[str, Any]],
    ) -> bool:
        """Determine if agent should run based on conditions"""
        # For MVP: always run if in sequence
        # In production: check conditions (e.g., only run UI/UX if PRD approved)
        return True
    
    # =====================
    # Planning
    # =====================
    
    def _determine_strategy(self) -> ExecutionStrategy:
        """Determine execution strategy based on goal"""
        required_agents = self.parsed_goal.required_agents
        
        # Default: sequential (most common)
        # Data → PRD → UI/UX
        return ExecutionStrategy.SEQUENTIAL
    
    def _build_sequence(self) -> List[str]:
        """
        Build agent execution sequence.
        
        FIXED: Now properly handles ALL required agents instead of
        reducing to data_agent only. Uses preferred ordering to ensure
        data flows correctly between agents.
        """
        raw_agents = self.parsed_goal.required_agents
        
        # Robustly map LLM hallucinations to actual agents
        mapped_agents = []
        for a in raw_agents:
            a_lower = a.lower()
            if any(x in a_lower for x in ["data", "gather"]):
                mapped_agents.append(constants.AGENT_DATA)
            elif any(x in a_lower for x in ["competitor", "market"]):
                mapped_agents.append(constants.AGENT_COMPETITOR)
            elif any(x in a_lower for x in ["interview", "user"]):
                mapped_agents.append(constants.AGENT_INTERVIEW)
            elif any(x in a_lower for x in ["feedback", "sentiment"]):
                mapped_agents.append(constants.AGENT_FEEDBACK)
            elif any(x in a_lower for x in ["prd", "product", "manager"]):
                mapped_agents.append(constants.AGENT_PRD)
            elif any(x in a_lower for x in ["validate", "validation", "test"]):
                mapped_agents.append(constants.AGENT_VALIDATION)
            elif any(x in a_lower for x in ["ui", "ux", "design"]):
                mapped_agents.append(constants.AGENT_UIUX)
                
        # Remove duplicates while preserving order
        mapped_agents = list(dict.fromkeys(mapped_agents))
        if not mapped_agents:
            mapped_agents = [constants.AGENT_DATA]
            
        required_agents = mapped_agents
        
        # Define preferred execution order:
        # Data collection first, then research/analysis, then synthesis, then design
        AGENT_ORDER = [
            constants.AGENT_DATA,
            constants.AGENT_COMPETITOR,
            constants.AGENT_INTERVIEW,
            constants.AGENT_FEEDBACK,
            constants.AGENT_PRD,
            constants.AGENT_VALIDATION,
            constants.AGENT_UIUX,
        ]
        
        # Sort required_agents by preferred order, preserving ALL agents
        ordered = [a for a in AGENT_ORDER if a in required_agents]
        
        # Add any agents not in the predefined order (future-proof)
        for a in required_agents:
            if a not in ordered:
                ordered.append(a)
        
        print(f"✅ Orchestrator: Built sequence with {len(ordered)} agents: {ordered}")
        
        return ordered if ordered else [constants.AGENT_DATA]
    
    # =====================
    # Handoffs
    # =====================
    
    def _create_handoff(
        self,
        from_agent: str,
        to_agent: str,
        deliverable: Dict[str, Any],
    ) -> AgentHandoff:
        """Create handoff between agents"""
        
        # Define handoff specifications
        HANDOFF_SPECS = {
            (constants.AGENT_DATA, constants.AGENT_PRD): {
                "trigger": "Data analysis complete",
                "key_fields": ["hypothesis", "confidence_score", "evidence", "recommendations"],
                "action": "Synthesize research into product strategy",
            },
            (constants.AGENT_PRD, constants.AGENT_UIUX): {
                "trigger": "PRD approved",
                "key_fields": ["user_personas", "user_stories", "requirements", "success_metrics"],
                "action": "Create visual solutions for requirements",
            },
        }
        
        spec = HANDOFF_SPECS.get((from_agent, to_agent), {
            "trigger": f"{from_agent} complete",
            "key_fields": ["output"],
            "action": f"Process {from_agent} output",
        })
        
        return AgentHandoff(
            from_agent=from_agent,
            to_agent=to_agent,
            deliverable=deliverable,
            trigger=spec["trigger"],
            key_fields=spec["key_fields"],
            action_required=spec["action"],
        )
    
    # =====================
    # Checkpoints
    # =====================
    
    async def _create_checkpoint(
        self,
        agent_name: str,
        checkpoint_type: str = "agent_complete",
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Checkpoint:
        """Create a checkpoint for tracking progress"""
        checkpoint = Checkpoint(
            goal_id=self.goal.id,
            agent_name=agent_name,
            checkpoint_type=checkpoint_type,
            title=title or f"{agent_name} completed",
            description=description or f"Agent {agent_name} finished execution",
            status="completed",
        )
        self.session.add(checkpoint)
        await self.session.commit()
        
        # Send WebSocket update
        await self._send_websocket_update({
            "type": "checkpoint_created",
            "checkpoint": {
                "id": checkpoint.id,
                "type": checkpoint.checkpoint_type,
                "title": checkpoint.title,
                "status": checkpoint.status,
                "created_at": checkpoint.created_at.isoformat(),
            },
        })
        
        return checkpoint
    
    # =====================
    # WebSocket Notifications
    # =====================
    
    async def _send_websocket_update(self, message: Dict[str, Any]) -> None:
        """
        Send real-time update via WebSocket.
        
        FIXED: Added better error handling and logging.
        """
        try:
            ws_manager = get_manager()
            if ws_manager:
                await ws_manager.send_update(self.goal.id, message)
                print(f"📡 WebSocket sent: {message.get('type', 'unknown')}")
            else:
                print("⚠️ WebSocket manager not available")
        except Exception as e:
            # Don't fail execution if WebSocket fails, but log the error
            print(f"⚠️ WebSocket send failed: {e}")
    
    async def _notify_agent_started(self, agent_name: str, agent_index: int = 1, total_agents: int = 1) -> None:
        """
        Notify that an agent started.
        
        FIXED: Added agent_index and total_agents for better UI progress tracking.
        """
        await self._send_websocket_update({
            "type": "agent_started",
            "goal_id": str(self.goal.id),
            "agent": agent_name,
            "agent_index": agent_index,
            "total_agents": total_agents,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    async def _notify_agent_completed(
        self, 
        agent_name: str, 
        success: bool, 
        output: Optional[Dict] = None,
        agent_index: int = 1,
        total_agents: int = 1,
        duration_seconds: float = 0.0
    ) -> None:
        """
        Notify that an agent completed.
        
        FIXED: Added agent_index, total_agents, and duration for better tracking.
        """
        await self._send_websocket_update({
            "type": "agent_completed",
            "goal_id": str(self.goal.id),
            "agent": agent_name,
            "agent_index": agent_index,
            "total_agents": total_agents,
            "success": success,
            "duration_seconds": duration_seconds,
            "output_preview": output.get("summary", "") if output else None,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    async def _notify_progress(
        self, 
        progress_percent: float, 
        current_agent: str,
        agent_index: int = 1,
        total_agents: int = 1
    ) -> None:
        """
        Notify progress update.
        
        FIXED: Added agent_index and total_agents for percentage calculation.
        """
        await self._send_websocket_update({
            "type": "progress_update",
            "goal_id": str(self.goal.id),
            "progress_percent": round(progress_percent, 1),
            "current_agent": current_agent,
            "agent_index": agent_index,
            "total_agents": total_agents,
            "timestamp": datetime.utcnow().isoformat(),
        })


# =====================
# Convenience Functions
# =====================

async def orchestrate_agents(
    session: AsyncSession,
    goal: ResearchGoal,
    parsed_goal: ParsedGoal,
) -> Dict[str, Any]:
    """
    Orchestrate multi-agent execution (convenience function).
    
    Usage:
        parsed = await parse_goal("Fix activation rate")
        result = await orchestrate_agents(session, goal, parsed)
    """
    orchestrator = MultiAgentOrchestrator(session, goal, parsed_goal)
    return await orchestrator.execute()
