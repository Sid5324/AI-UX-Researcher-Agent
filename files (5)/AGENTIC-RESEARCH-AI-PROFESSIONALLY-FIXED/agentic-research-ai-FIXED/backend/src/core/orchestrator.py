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
        if agent_name == constants.AGENT_PRD and self.data_findings:
            context["data_findings"] = self.data_findings
        
        elif agent_name == constants.AGENT_UIUX:
            if self.data_findings:
                context["data_findings"] = self.data_findings
            if self.product_strategy:
                context["product_strategy"] = self.product_strategy
        
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
            
            # Mark goal as complete
            self.goal.status = "completed"
            self.goal.progress_percent = 100.0
            self.goal.final_output = {
                "data_findings": self.context.data_findings,
                "product_strategy": self.context.product_strategy,
                "design_specs": self.context.design_specs,
                "decisions": self.context.decisions,
            }
            
            await self.session.commit()
            
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
        """Execute agents one after another"""
        results = []
        
        for agent_name in self.agent_sequence:
            # Update goal status
            self.goal.current_agent = agent_name
            await self.session.commit()
            
            # Create agent
            agent = await self._create_agent(agent_name)
            
            # Execute agent
            result = await agent.run()
            results.append(result)
            
            if not result["success"]:
                # Agent failed, stop execution
                break
            
            # Store agent output in context
            await self._store_agent_output(agent_name, result["output"])
            
            # Create handoff to next agent (if exists)
            if self.agent_sequence.index(agent_name) < len(self.agent_sequence) - 1:
                next_agent = self.agent_sequence[self.agent_sequence.index(agent_name) + 1]
                handoff = self._create_handoff(agent_name, next_agent, result["output"])
                self.context.add_handoff(handoff)
        
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
        """Create agent instance with context"""
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
        """Store agent output in shared context"""
        if agent_name == constants.AGENT_DATA:
            self.context.data_findings = output
        
        elif agent_name == constants.AGENT_PRD:
            self.context.product_strategy = output
        
        elif agent_name == constants.AGENT_UIUX:
            self.context.design_specs = output
    
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
        """Build agent execution sequence"""
        required_agents = self.parsed_goal.required_agents
        
        # Define standard sequences
        STANDARD_SEQUENCES = {
            "research_to_design": [
                constants.AGENT_DATA,
                constants.AGENT_PRD,
                constants.AGENT_UIUX,
            ],
            "data_only": [
                constants.AGENT_DATA,
            ],
            "design_only": [
                constants.AGENT_UIUX,
            ],
        }
        
        # Determine which sequence to use
        if len(required_agents) == 3:
            return STANDARD_SEQUENCES["research_to_design"]
        elif constants.AGENT_DATA in required_agents:
            return [constants.AGENT_DATA]
        else:
            # Use provided order
            return required_agents
    
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
