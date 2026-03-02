"""
Base Agent
==========

Abstract base class for all specialized agents.

Provides:
- Common agent lifecycle
- Tool execution
- Memory access
- State management
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from backend.src.core.config import constants
from backend.src.database.models import ResearchGoal, AgentState
from backend.src.database.session import AsyncSession
from backend.src.tools.registry import get_tool_registry
from backend.src.core.memory_system import get_memory_manager


tool_registry = get_tool_registry()
memory_manager = get_memory_manager()


class BaseAgent(ABC):
    """
    Base class for all specialized agents.
    
    Agents are autonomous workers that execute specific tasks:
    - DataAgent: Gathers and analyzes data
    - PRDAgent: Generates product requirements
    - UIUXAgent: Creates designs and prototypes
    
    Each agent inherits common functionality from this base class.
    """
    
    # Subclasses must override these
    agent_name: str = "base_agent"
    agent_description: str = "Base agent class"
    required_tools: List[str] = []
    
    def __init__(
        self,
        session: AsyncSession,
        goal: ResearchGoal,
        agent_state: Optional[AgentState] = None,
    ):
        self.session = session
        self.goal = goal
        
        # Create or use existing agent state
        if agent_state is None:
            self.agent_state = AgentState(
                goal_id=goal.id,
                agent_name=self.agent_name,
                status="pending",
            )
            session.add(self.agent_state)
        else:
            self.agent_state = agent_state
        
        # Working memory (agent-specific)
        self.working_memory: Dict[str, Any] = {}
    
    # =====================
    # Main Execution
    # =====================
    
    @abstractmethod
    async def execute(self) -> Dict[str, Any]:
        """
        Main execution method.
        
        Subclasses must implement this with their specific logic.
        
        Returns:
            Dict with agent output
        """
        pass
    
    async def run(self) -> Dict[str, Any]:
        """
        Run agent with lifecycle management.
        
        Handles:
        - State transitions
        - Error handling
        - Performance tracking
        """
        start_time = datetime.utcnow()
        
        try:
            # Mark as running
            self.agent_state.status = "running"
            self.agent_state.started_at = start_time
            await self.session.commit()
            
            # Execute agent logic
            result = await self.execute()
            
            # Mark as completed
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            self.agent_state.status = "completed"
            self.agent_state.completed_at = end_time
            self.agent_state.duration_seconds = duration
            self.agent_state.output = result
            
            await self.session.commit()
            
            return {
                "success": True,
                "agent": self.agent_name,
                "output": result,
                "duration_seconds": duration,
            }
        
        except Exception as e:
            # Mark as failed
            self.agent_state.status = "failed"
            self.agent_state.error_message = str(e)
            self.agent_state.completed_at = datetime.utcnow()
            await self.session.commit()
            
            return {
                "success": False,
                "agent": self.agent_name,
                "error": str(e),
            }
    
    # =====================
    # Tool Execution
    # =====================
    
    async def use_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a tool and track usage.
        
        Args:
            tool_name: Name of tool to use
            params: Tool parameters
            
        Returns:
            Tool execution result
        """
        result = await tool_registry.execute_tool(
            tool_name=tool_name,
            params=params,
            session=self.session,
            goal_id=self.goal.id,
            agent_name=self.agent_name,
        )
        
        # Track tool calls
        self.agent_state.llm_calls += 1
        if result.get("cost_usd"):
            self.agent_state.cost_usd += result["cost_usd"]
        
        return result
    
    # =====================
    # Memory Access
    # =====================
    
    async def remember(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Search semantic memory for relevant insights.
        
        Args:
            query: What to search for
            **kwargs: Additional search parameters
            
        Returns:
            List of relevant insights
        """
        return await memory_manager.search_insights(query, **kwargs)
    
    async def learn(
        self,
        content: str,
        insight_type: str,
        confidence: float,
        **kwargs,
    ) -> str:
        """
        Store new insight in semantic memory.
        
        Args:
            content: Insight content
            insight_type: Type of insight
            confidence: Confidence score (0-1)
            **kwargs: Additional metadata
            
        Returns:
            Insight ID
        """
        return await memory_manager.store_insight(
            session=self.session,
            content=content,
            insight_type=insight_type,
            confidence=confidence,
            **kwargs,
        )
    
    # =====================
    # Progress Tracking
    # =====================
    
    async def update_progress(
        self,
        step: str,
        percent: Optional[float] = None,
    ) -> None:
        """
        Update agent progress.
        
        Args:
            step: Current step description
            percent: Progress percentage (0-100)
        """
        self.agent_state.current_step = step
        self.agent_state.steps_completed += 1
        
        if percent is not None:
            self.goal.progress_percent = percent
        
        await self.session.commit()
    
    # =====================
    # Utility Methods
    # =====================
    
    def get_context(self) -> Dict[str, Any]:
        """Get agent execution context"""
        return {
            "goal_description": self.goal.description,
            "goal_mode": self.goal.mode,
            "agent_name": self.agent_name,
            "current_step": self.agent_state.current_step,
            "steps_completed": self.agent_state.steps_completed,
            "working_memory": self.working_memory,
        }
