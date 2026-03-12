"""
ReAct Loop Engine
================

Core autonomous execution system:
- Think: Generate reasoning with chain-of-thought
- Act: Execute actions via tools
- Observe: Perceive results and interpret
- Learn: Update beliefs and memory

This is the heart of the agentic AI system.
"""

import json
from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
from enum import Enum

from src.core.config import get_settings, constants
from src.core.ai_manager import get_ai_manager
from src.database.models import ResearchGoal, AgentState, MemoryEntry
from src.database.session import AsyncSession


settings = get_settings()
ai_manager = get_ai_manager()


class ReActState(Enum):
    """Current state in ReAct loop"""
    THINK = "think"
    ACT = "act"
    OBSERVE = "observe"
    LEARN = "learn"
    CHECKPOINT = "checkpoint"
    COMPLETE = "complete"
    FAILED = "failed"


class ReActEngine:
    """
    Autonomous execution engine using ReAct pattern.
    
    Operates continuously:
    1. THINK: Reason about current situation
    2. ACT: Execute action via tools
    3. OBSERVE: Perceive and interpret results
    4. LEARN: Update beliefs and memory
    
    Repeats until goal achieved or checkpoint needed.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        goal: ResearchGoal,
        agent_state: AgentState,
    ):
        self.session = session
        self.goal = goal
        self.agent_state = agent_state
        
        # Working memory (volatile, cleared each goal)
        self.working_memory: Dict[str, Any] = {
            "hypotheses": [],
            "observations": [],
            "actions_taken": [],
            "context": {},
        }
        
        # Iteration tracking
        self.iteration = 0
        self.max_iterations = settings.max_react_iterations
        
        # State
        self.current_state = ReActState.THINK
        self.should_checkpoint = False
        self.checkpoint_reason: Optional[str] = None
        
    # =====================
    # Main Loop
    # =====================
    
    async def run(self) -> Dict[str, Any]:
        """
        Execute ReAct loop until goal complete or checkpoint needed.
        
        Returns:
            Dict with final output or checkpoint data
        """
        self.agent_state.started_at = datetime.utcnow()
        self.agent_state.status = "running"
        await self.session.commit()
        
        try:
            while self.iteration < self.max_iterations:
                self.iteration += 1
                self.agent_state.react_iteration = self.iteration
                
                # Execute current state
                if self.current_state == ReActState.THINK:
                    await self._think_step()
                
                elif self.current_state == ReActState.ACT:
                    await self._act_step()
                
                elif self.current_state == ReActState.OBSERVE:
                    await self._observe_step()
                
                elif self.current_state == ReActState.LEARN:
                    await self._learn_step()
                
                elif self.current_state == ReActState.CHECKPOINT:
                    # Pause for human approval
                    return await self._create_checkpoint()
                
                elif self.current_state == ReActState.COMPLETE:
                    # Goal achieved
                    return await self._complete_goal()
                
                elif self.current_state == ReActState.FAILED:
                    # Unrecoverable failure
                    return await self._fail_goal()
                
                # Check if checkpoint needed
                if self.should_checkpoint:
                    self.current_state = ReActState.CHECKPOINT
                
                # Safety: commit state periodically
                if self.iteration % 3 == 0:
                    await self.session.commit()
            
            # Max iterations reached
            return await self._create_checkpoint(
                reason="Max iterations reached. Need user guidance.",
            )
        
        except Exception as e:
            self.agent_state.error_message = str(e)
            self.agent_state.status = "failed"
            await self.session.commit()
            raise
    
    # =====================
    # Think Step
    # =====================
    
    async def _think_step(self) -> None:
        """
        Generate reasoning about current situation.
        
        Uses chain-of-thought prompting to:
        - Analyze current context
        - Form hypotheses
        - Plan next action
        """
        # Build context for reasoning
        context = self._build_context()
        
        prompt = f"""
You are an autonomous research agent executing this goal:
"{self.goal.description}"

CURRENT SITUATION:
{context}

THINK through the following:
1. What do we know so far?
2. What hypotheses are forming?
3. What's the most logical next action?
4. What could go wrong?
5. What's our contingency?

Provide structured reasoning in JSON format:
{{
    "interpretation": "what the observations tell us",
    "hypotheses": [
        {{
            "hypothesis": "statement",
            "confidence": 0.0-1.0,
            "evidence": ["supporting facts"]
        }}
    ],
    "uncertainties": ["what we don't know"],
    "next_action": {{
        "action_type": "data_gathering|analysis|validation|synthesis",
        "description": "what to do next",
        "reason": "why this advances the goal"
    }},
    "risks": ["potential failure modes"],
    "contingency": "what to do if action fails"
}}
"""
        
        try:
            thought = await ai_manager.generate_json(
                prompt=prompt,
                system="You are a strategic research agent. Think step-by-step.",
                temperature=0.7,
            )
            
            # Store thought
            self.agent_state.last_thought = json.dumps(thought, indent=2)
            self.working_memory["last_thought"] = thought
            
            # Log to episodic memory
            await self._log_memory(
                event_type="think",
                content=self.agent_state.last_thought,
                importance="high",
            )
            
            # Update hypotheses
            if "hypotheses" in thought:
                self.working_memory["hypotheses"] = thought["hypotheses"]
            
            # Transition to ACT
            self.current_state = ReActState.ACT
            
        except Exception as e:
            # Reasoning failed - this is critical
            await self._log_memory(
                event_type="think",
                content=f"Reasoning error: {str(e)}",
                importance="high",
            )
            self.current_state = ReActState.FAILED
    
    # =====================
    # Act Step
    # =====================
    
    async def _act_step(self) -> None:
        """
        Execute action based on reasoning.
        
        Selects appropriate tool and executes with parameters.
        """
        last_thought = self.working_memory.get("last_thought", {})
        next_action = last_thought.get("next_action", {})
        
        if not next_action:
            # No action specified, ask for clarification
            self.should_checkpoint = True
            self.checkpoint_reason = "Agent couldn't determine next action. Need guidance."
            return
        
        action_type = next_action.get("action_type", "analysis")
        description = next_action.get("description", "")
        
        # For now, simulate action (tools will be added in Phase 3)
        action_result = {
            "action": action_type,
            "description": description,
            "status": "simulated",
            "output": f"Simulated execution of: {description}",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Store action
        self.agent_state.last_action = json.dumps(action_result, indent=2)
        self.working_memory["last_action"] = action_result
        self.working_memory["actions_taken"].append(action_result)
        
        # Log to memory
        await self._log_memory(
            event_type="act",
            content=self.agent_state.last_action,
            importance="medium",
        )
        
        # Transition to OBSERVE
        self.current_state = ReActState.OBSERVE
    
    # =====================
    # Observe Step
    # =====================
    
    async def _observe_step(self) -> None:
        """
        Perceive and interpret action results.
        
        Analyzes what happened and extracts insights.
        """
        last_action = self.working_memory.get("last_action", {})
        
        prompt = f"""
You just executed this action:
{json.dumps(last_action, indent=2)}

OBSERVE and interpret:
1. What did this action reveal?
2. Does it confirm or challenge our hypotheses?
3. What new information do we have?
4. What patterns are emerging?

Provide structured observation in JSON:
{{
    "observation": "what we learned",
    "key_insights": ["important findings"],
    "hypothesis_updates": [
        {{
            "hypothesis": "statement",
            "status": "confirmed|challenged|needs_more_data",
            "confidence_change": "+0.15 or -0.10"
        }}
    ],
    "implications": ["what this means for the goal"],
    "unexpected": ["anything surprising"]
}}
"""
        
        try:
            observation = await ai_manager.generate_json(
                prompt=prompt,
                system="You are a meticulous research observer.",
                temperature=0.5,
            )
            
            # Store observation
            self.agent_state.last_observation = json.dumps(observation, indent=2)
            self.working_memory["last_observation"] = observation
            self.working_memory["observations"].append(observation)
            
            # Log to memory
            await self._log_memory(
                event_type="observe",
                content=self.agent_state.last_observation,
                importance="high",
            )
            
            # Transition to LEARN
            self.current_state = ReActState.LEARN
            
        except Exception as e:
            await self._log_memory(
                event_type="observe",
                content=f"Observation error: {str(e)}",
                importance="medium",
            )
            self.current_state = ReActState.LEARN  # Continue anyway
    
    # =====================
    # Learn Step
    # =====================
    
    async def _learn_step(self) -> None:
        """
        Update beliefs and memory based on observations.
        
        Decides:
        - Should we continue?
        - Is goal achieved?
        - Need checkpoint?
        """
        last_observation = self.working_memory.get("last_observation", {})
        
        prompt = f"""
Current goal: "{self.goal.description}"
Iteration: {self.iteration} / {self.max_iterations}

Recent observation:
{json.dumps(last_observation, indent=2)}

Working memory:
- Hypotheses: {len(self.working_memory.get('hypotheses', []))}
- Actions taken: {len(self.working_memory.get('actions_taken', []))}
- Observations: {len(self.working_memory.get('observations', []))}

LEARN and decide:
1. What have we learned overall?
2. Is the goal achieved? (If yes, we're done)
3. Do we need human approval for next step?
4. Should we continue autonomously?

Provide decision in JSON:
{{
    "learning": "what we've learned",
    "goal_status": "in_progress|achieved|blocked",
    "confidence": 0.0-1.0,
    "next_step": "continue|checkpoint|complete",
    "reason": "explanation"
}}
"""
        
        try:
            learning = await ai_manager.generate_json(
                prompt=prompt,
                system="You are a strategic decision-maker.",
                temperature=0.3,
            )
            
            # Store learning
            await self._log_memory(
                event_type="learn",
                content=json.dumps(learning, indent=2),
                importance="high",
            )
            
            # Make decision
            goal_status = learning.get("goal_status", "in_progress")
            next_step = learning.get("next_step", "continue")
            
            if goal_status == "achieved" or next_step == "complete":
                self.current_state = ReActState.COMPLETE
            
            elif next_step == "checkpoint":
                self.should_checkpoint = True
                self.checkpoint_reason = learning.get("reason", "Agent requests approval")
                self.current_state = ReActState.CHECKPOINT
            
            elif goal_status == "blocked":
                self.should_checkpoint = True
                self.checkpoint_reason = "Agent is blocked and needs guidance"
                self.current_state = ReActState.CHECKPOINT
            
            else:
                # Continue to next iteration
                self.current_state = ReActState.THINK
            
            # Update progress
            confidence = learning.get("confidence", 0.0)
            self.goal.progress_percent = min(
                self.goal.progress_percent + 10,
                confidence * 100
            )
            
        except Exception as e:
            await self._log_memory(
                event_type="learn",
                content=f"Learning error: {str(e)}",
                importance="medium",
            )
            # Default: continue
            self.current_state = ReActState.THINK
    
    # =====================
    # Checkpoint & Completion
    # =====================
    
    async def _create_checkpoint(self, reason: Optional[str] = None) -> Dict[str, Any]:
        """Create checkpoint for human approval"""
        from src.database.models import Checkpoint
        
        checkpoint = Checkpoint(
            goal_id=self.goal.id,
            agent_name=self.agent_name,
            checkpoint_type=constants.CHECKPOINT_CUSTOM,
            title=f"Checkpoint at iteration {self.iteration}",
            description=reason or self.checkpoint_reason or "Agent needs approval",
            agent_reasoning=self.agent_state.last_thought,
            status="pending",
        )
        
        self.session.add(checkpoint)
        self.goal.status = "checkpoint"
        self.agent_state.status = "checkpoint"
        await self.session.commit()
        
        return {
            "status": "checkpoint",
            "checkpoint_id": checkpoint.id,
            "reason": checkpoint.description,
            "iteration": self.iteration,
        }
    
    async def _complete_goal(self) -> Dict[str, Any]:
        """Mark goal as complete"""
        self.agent_state.status = "completed"
        self.agent_state.completed_at = datetime.utcnow()
        self.goal.status = "completed"
        self.goal.completed_at = datetime.utcnow()
        self.goal.progress_percent = 100.0
        
        # Store final output
        self.goal.final_output = {
            "iterations": self.iteration,
            "hypotheses": self.working_memory.get("hypotheses", []),
            "observations": self.working_memory.get("observations", []),
            "actions_taken": self.working_memory.get("actions_taken", []),
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.session.commit()
        
        return {
            "status": "completed",
            "iterations": self.iteration,
            "output": self.goal.final_output,
        }
    
    async def _fail_goal(self) -> Dict[str, Any]:
        """Mark goal as failed"""
        self.agent_state.status = "failed"
        self.agent_state.completed_at = datetime.utcnow()
        self.goal.status = "failed"
        self.goal.error_message = "ReAct loop failed"
        
        await self.session.commit()
        
        return {
            "status": "failed",
            "error": self.goal.error_message,
            "iteration": self.iteration,
        }
    
    # =====================
    # Utility Methods
    # =====================
    
    def _build_context(self) -> str:
        """Build context string for reasoning"""
        context_parts = []
        
        # Goal info
        context_parts.append(f"Goal: {self.goal.description}")
        context_parts.append(f"Iteration: {self.iteration}/{self.max_iterations}")
        context_parts.append(f"Progress: {self.goal.progress_percent:.1f}%")
        
        # Recent observations
        recent_obs = self.working_memory.get("observations", [])[-3:]
        if recent_obs:
            context_parts.append("\nRecent observations:")
            for obs in recent_obs:
                context_parts.append(f"  - {obs.get('observation', 'N/A')}")
        
        # Active hypotheses
        hypotheses = self.working_memory.get("hypotheses", [])
        if hypotheses:
            context_parts.append("\nActive hypotheses:")
            for hyp in hypotheses:
                confidence = hyp.get("confidence", 0)
                context_parts.append(
                    f"  - {hyp.get('hypothesis', 'N/A')} "
                    f"(confidence: {confidence:.0%})"
                )
        
        return "\n".join(context_parts)
    
    async def _log_memory(
        self,
        event_type: str,
        content: str,
        importance: Literal["low", "medium", "high"] = "medium",
    ) -> None:
        """Log event to episodic memory"""
        entry = MemoryEntry(
            goal_id=self.goal.id,
            memory_type="episodic",
            event_type=event_type,
            content=content,
            importance=importance,
            metadata={
                "iteration": self.iteration,
                "agent": self.agent_state.agent_name,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        
        self.session.add(entry)


# =====================
# Convenience Functions
# =====================

async def run_react_loop(
    session: AsyncSession,
    goal: ResearchGoal,
    agent_state: AgentState,
) -> Dict[str, Any]:
    """
    Run ReAct loop for a goal.
    
    Convenience function for starting autonomous execution.
    
    Args:
        session: Database session
        goal: Research goal to execute
        agent_state: Agent state tracker
        
    Returns:
        Dict with result (completed, checkpoint, or failed)
    """
    engine = ReActEngine(session, goal, agent_state)
    return await engine.run()
