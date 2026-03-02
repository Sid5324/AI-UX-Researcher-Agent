"""
Unit Tests - Core Modules
=========================

Tests for configuration, AI manager, goal parser, and ReAct engine.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.core.config import get_settings, constants
from src.core.ai_manager import AIManager
from src.core.goal_parser import GoalParser, parse_goal
from src.core.react_engine import ReActEngine, ReActState


# =====================
# Configuration Tests
# =====================

@pytest.mark.unit
class TestConfiguration:
    """Test configuration system."""
    
    def test_settings_singleton(self):
        """Test settings is singleton."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
    
    def test_default_values(self):
        """Test default configuration values."""
        settings = get_settings()
        
        assert settings.app_name == "Agentic Research AI"
        assert settings.debug is False
        assert settings.max_react_iterations == 10
    
    def test_demo_mode_detection(self):
        """Test demo mode is detected correctly."""
        settings = get_settings()
        
        # In test environment, should be demo mode
        assert settings.is_demo_mode is True
    
    def test_constants(self):
        """Test constants are defined."""
        assert constants.AGENT_DATA == "data_agent"
        assert constants.AGENT_PRD == "prd_agent"
        assert constants.AGENT_UIUX == "ui_ux_agent"
        assert constants.STATUS_PENDING == "pending"
        assert constants.STATUS_RUNNING == "running"


# =====================
# AI Manager Tests
# =====================

@pytest.mark.unit
class TestAIManager:
    """Test AI manager."""
    
    @pytest.fixture
    def ai_manager(self):
        """Create AI manager instance."""
        return AIManager()
    
    @pytest.mark.asyncio
    async def test_health_check_caching(self, ai_manager):
        """Test health check results are cached."""
        with patch.object(ai_manager, '_check_ollama_health_internal') as mock_check:
            mock_check.return_value = True
            
            # First call
            result1 = await ai_manager.check_ollama_health()
            
            # Second call should use cache
            result2 = await ai_manager.check_ollama_health()
            
            # Should only call internal check once
            assert mock_check.call_count == 1
            assert result1 is True
            assert result2 is True
    
    @pytest.mark.asyncio
    async def test_generate_with_ollama(self, ai_manager, mock_llm_response):
        """Test generation with Ollama."""
        with patch.object(ai_manager, '_generate_ollama') as mock_generate:
            mock_generate.return_value = mock_llm_response
            
            result = await ai_manager.generate(
                prompt="Test prompt",
                system="Test system"
            )
            
            assert result["content"] == mock_llm_response["content"]
            assert result["provider"] == "test-provider"
            assert "cost" in result
    
    @pytest.mark.asyncio
    async def test_fallback_chain(self, ai_manager):
        """Test fallback to alternative providers."""
        with patch.object(ai_manager, '_generate_ollama') as mock_ollama:
            with patch.object(ai_manager, '_generate_openrouter') as mock_openrouter:
                # Ollama fails
                mock_ollama.side_effect = Exception("Ollama unavailable")
                
                # OpenRouter succeeds
                mock_openrouter.return_value = {
                    "content": "Fallback response",
                    "provider": "openrouter",
                    "cost": 0.01
                }
                
                result = await ai_manager.generate(prompt="Test")
                
                assert result["provider"] == "openrouter"
                assert mock_ollama.call_count == 1
                assert mock_openrouter.call_count == 1
    
    @pytest.mark.asyncio
    async def test_json_mode(self, ai_manager):
        """Test JSON mode generation."""
        with patch.object(ai_manager, 'generate') as mock_generate:
            mock_generate.return_value = {
                "content": '{"key": "value"}',
                "provider": "test",
                "cost": 0.0
            }
            
            result = await ai_manager.generate_json(
                prompt="Generate JSON"
            )
            
            assert isinstance(result, dict)
            assert result["key"] == "value"
    
    @pytest.mark.asyncio
    async def test_cost_tracking(self, ai_manager):
        """Test cost is tracked correctly."""
        with patch.object(ai_manager, '_generate_ollama') as mock_generate:
            mock_generate.return_value = {
                "content": "Response",
                "provider": "ollama",
                "cost": 0.0,  # Ollama is free
                "tokens": {"prompt": 10, "completion": 20}
            }
            
            result = await ai_manager.generate(prompt="Test")
            
            assert result["cost"] == 0.0
    
    @pytest.mark.asyncio
    async def test_get_available_models(self, ai_manager):
        """Test getting available models."""
        with patch.object(ai_manager, 'check_ollama_health') as mock_health:
            mock_health.return_value = True
            
            models = await ai_manager.get_available_models()
            
            assert len(models) > 0
            assert all("name" in m for m in models)
            assert all("provider" in m for m in models)


# =====================
# Goal Parser Tests
# =====================

@pytest.mark.unit
class TestGoalParser:
    """Test goal parsing."""
    
    @pytest.fixture
    def goal_parser(self):
        """Create goal parser instance."""
        return GoalParser()
    
    @pytest.mark.asyncio
    async def test_parse_simple_goal(self, goal_parser):
        """Test parsing simple goal."""
        goal = "Analyze user engagement data"
        
        with patch.object(goal_parser.ai_manager, 'generate_json') as mock_gen:
            mock_gen.return_value = {
                "intent": "Analyze user engagement",
                "goal_type": "general",
                "required_agents": ["data_agent"],
                "estimated_duration_days": 3,
                "estimated_cost_usd": 500,
            }
            
            parsed = await goal_parser.parse(goal)
            
            assert parsed.intent == "Analyze user engagement"
            assert "data_agent" in parsed.required_agents
            assert parsed.estimated_duration_days == 3
    
    @pytest.mark.asyncio
    async def test_parse_with_budget(self, goal_parser):
        """Test parsing goal with budget mentioned."""
        goal = "Fix checkout with $2000 budget and 1 week timeline"
        
        with patch.object(goal_parser.ai_manager, 'generate_json') as mock_gen:
            mock_gen.return_value = {
                "intent": "Fix checkout",
                "constraints": {
                    "budget_usd": 2000,
                    "timeline_days": 7
                },
                "required_agents": ["data_agent", "prd_agent"],
            }
            
            parsed = await goal_parser.parse(goal)
            
            assert parsed.constraints["budget_usd"] == 2000
            assert parsed.constraints["timeline_days"] == 7
    
    @pytest.mark.asyncio
    async def test_fallback_on_error(self, goal_parser):
        """Test fallback mission created on parse error."""
        goal = "Test goal"
        
        with patch.object(goal_parser.ai_manager, 'generate_json') as mock_gen:
            mock_gen.side_effect = Exception("Parse error")
            
            parsed = await goal_parser.parse(goal)
            
            # Should return fallback mission
            assert parsed.intent == goal
            assert parsed.goal_type == "general"
            assert len(parsed.sub_goals) > 0
    
    @pytest.mark.asyncio
    async def test_validation(self, goal_parser):
        """Test mission data is validated."""
        goal = "Test"
        
        with patch.object(goal_parser.ai_manager, 'generate_json') as mock_gen:
            # Return invalid data
            mock_gen.return_value = {
                "intent": "Test",
                "estimated_duration_days": -5,  # Invalid
                "estimated_cost_usd": -100,  # Invalid
            }
            
            parsed = await goal_parser.parse(goal)
            
            # Should normalize invalid values
            assert parsed.estimated_duration_days >= 1
            assert parsed.estimated_cost_usd >= 0
    
    @pytest.mark.asyncio
    async def test_quick_estimate(self, goal_parser):
        """Test quick estimation."""
        with patch.object(goal_parser.ai_manager, 'generate_json') as mock_gen:
            mock_gen.return_value = {
                "estimated_days": 5,
                "estimated_cost_usd": 1000,
                "complexity": "medium",
                "feasibility": "moderate"
            }
            
            from src.core.goal_parser import quick_estimate
            result = await quick_estimate("Test goal")
            
            assert result["estimated_days"] == 5
            assert result["complexity"] == "medium"


# =====================
# ReAct Engine Tests
# =====================

@pytest.mark.unit
class TestReActEngine:
    """Test ReAct engine."""
    
    @pytest.mark.asyncio
    async def test_state_transitions(self, session, test_goal, test_user):
        """Test ReAct state transitions."""
        from src.database.models import AgentState
        
        agent_state = AgentState(
            goal_id=test_goal.id,
            agent_name="test_agent",
            status="pending"
        )
        session.add(agent_state)
        await session.commit()
        
        engine = ReActEngine(session, test_goal, agent_state)
        
        # Initial state
        assert engine.current_state == ReActState.THINK
        
        # Simulate state changes
        engine.current_state = ReActState.ACT
        assert engine.current_state == ReActState.ACT
        
        engine.current_state = ReActState.OBSERVE
        assert engine.current_state == ReActState.OBSERVE
        
        engine.current_state = ReActState.LEARN
        assert engine.current_state == ReActState.LEARN
    
    @pytest.mark.asyncio
    async def test_max_iterations(self, session, test_goal, test_user):
        """Test max iterations limit."""
        from src.database.models import AgentState
        from src.core.config import get_settings
        
        settings = get_settings()
        
        agent_state = AgentState(
            goal_id=test_goal.id,
            agent_name="test_agent",
            status="pending"
        )
        session.add(agent_state)
        await session.commit()
        
        engine = ReActEngine(session, test_goal, agent_state)
        
        assert engine.max_iterations == settings.max_react_iterations
        assert engine.iteration == 0
    
    @pytest.mark.asyncio
    async def test_working_memory(self, session, test_goal, test_user):
        """Test working memory is initialized."""
        from src.database.models import AgentState
        
        agent_state = AgentState(
            goal_id=test_goal.id,
            agent_name="test_agent"
        )
        session.add(agent_state)
        await session.commit()
        
        engine = ReActEngine(session, test_goal, agent_state)
        
        assert "hypotheses" in engine.working_memory
        assert "observations" in engine.working_memory
        assert "actions_taken" in engine.working_memory
        assert isinstance(engine.working_memory["hypotheses"], list)
    
    @pytest.mark.asyncio
    async def test_checkpoint_creation(self, session, test_goal, test_user):
        """Test checkpoint creation."""
        from src.database.models import AgentState
        
        agent_state = AgentState(
            goal_id=test_goal.id,
            agent_name="test_agent"
        )
        session.add(agent_state)
        await session.commit()
        
        engine = ReActEngine(session, test_goal, agent_state)
        engine.iteration = 5
        
        result = await engine._create_checkpoint(reason="Test checkpoint")
        
        assert result["status"] == "checkpoint"
        assert result["iteration"] == 5
        assert "checkpoint_id" in result


# =====================
# Run All Tests
# =====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
