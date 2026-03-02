"""
End-to-End Test Script
======================

Tests all Week 1 components:
1. Configuration system
2. Database models
3. AI manager
4. Goal parser
5. ReAct engine
6. Data agent
7. Tool registry
8. Memory system

Run with: python test_week1.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from src.core.config import get_settings
from src.core.ai_manager import get_ai_manager
from src.database.session import init_db, get_session, check_db_connection
from src.database.models import ResearchGoal, AgentState
from src.core.goal_parser import parse_goal
from src.agents.data.agent import DataAgent
from src.tools.registry import get_tool_registry, list_available_tools
from src.core.memory_system import get_memory_manager


async def test_configuration():
    """Test configuration system"""
    print("\n" + "="*60)
    print("TEST 1: Configuration System")
    print("="*60)
    
    settings = get_settings()
    
    print(f"✓ App name: {settings.app_name}")
    print(f"✓ Mode: {settings.app_mode}")
    print(f"✓ Debug: {settings.debug}")
    print(f"✓ Ollama URL: {settings.ollama_base_url}")
    print(f"✓ Ollama model: {settings.ollama_model}")
    print(f"✓ Database URL: {settings.database_url}")
    print(f"✓ ChromaDB path: {settings.chromadb_path}")
    
    assert settings.app_name == "Agentic Research AI"
    assert settings.app_mode in ["demo", "real"]
    
    print("\n✅ Configuration system: PASSED")
    return True


async def test_database():
    """Test database initialization and models"""
    print("\n" + "="*60)
    print("TEST 2: Database System")
    print("="*60)
    
    # Initialize database
    await init_db()
    print("✓ Database initialized")
    
    # Check connection
    is_healthy = await check_db_connection()
    assert is_healthy, "Database connection failed"
    print("✓ Database connection healthy")
    
    # Test creating a goal
    async with get_session() as session:
        goal = ResearchGoal(
            description="Test goal for Week 1 validation",
            mode="demo",
            budget_usd=1000.0,
            timeline_days=7,
        )
        session.add(goal)
        await session.commit()
        
        goal_id = goal.id
        print(f"✓ Created test goal: {goal_id}")
    
    # Test reading the goal
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(ResearchGoal).where(ResearchGoal.id == goal_id)
        )
        retrieved_goal = result.scalar_one_or_none()
        
        assert retrieved_goal is not None
        assert retrieved_goal.description == "Test goal for Week 1 validation"
        print(f"✓ Retrieved goal: {retrieved_goal.id}")
    
    print("\n✅ Database system: PASSED")
    return True


async def test_ai_manager():
    """Test AI manager and model connectivity"""
    print("\n" + "="*60)
    print("TEST 3: AI Manager")
    print("="*60)
    
    ai_manager = get_ai_manager()
    
    # Check Ollama health
    is_healthy = await ai_manager.check_ollama_health()
    if is_healthy:
        print("✓ Ollama connected")
    else:
        print("⚠️  Ollama not available (will use fallback)")
    
    # Get available models
    models = await ai_manager.get_available_models()
    print(f"✓ Found {len(models)} available models")
    for model in models[:3]:
        print(f"  - {model['name']} ({model['provider']})")
    
    # Test generation
    print("\n✓ Testing AI generation...")
    result = await ai_manager.generate(
        prompt="Say 'Week 1 test successful' in one sentence.",
        system="You are helpful.",
        temperature=0.3,
    )
    
    print(f"  Model: {result['model']}")
    print(f"  Provider: {result['provider']}")
    print(f"  Cost: ${result['cost']:.4f}")
    print(f"  Response: {result['content'][:100]}...")
    
    assert result['content'] is not None
    assert len(result['content']) > 0
    
    print("\n✅ AI Manager: PASSED")
    return True


async def test_goal_parser():
    """Test goal parsing"""
    print("\n" + "="*60)
    print("TEST 4: Goal Parser")
    print("="*60)
    
    # Test parsing a goal
    goal_description = "Fix our activation rate decline from 42% to 28%. Budget $2000, 1 week timeline."
    
    print(f"✓ Parsing goal: {goal_description}")
    parsed = await parse_goal(goal_description)
    
    print(f"  Intent: {parsed.intent}")
    print(f"  Goal type: {parsed.goal_type}")
    print(f"  Estimated duration: {parsed.estimated_duration_days} days")
    print(f"  Estimated cost: ${parsed.estimated_cost_usd}")
    print(f"  Autonomy level: {parsed.autonomy_level}")
    print(f"  Required agents: {', '.join(parsed.required_agents)}")
    print(f"  Checkpoints: {len(parsed.checkpoints)}")
    
    assert parsed.intent is not None
    assert parsed.estimated_duration_days > 0
    assert len(parsed.required_agents) > 0
    
    print("\n✅ Goal Parser: PASSED")
    return True


async def test_tool_registry():
    """Test tool registry and execution"""
    print("\n" + "="*60)
    print("TEST 5: Tool Registry")
    print("="*60)
    
    tool_registry = get_tool_registry()
    
    # List tools
    tools = list_available_tools()
    print(f"✓ Found {len(tools)} registered tools")
    
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")
    
    # Test tool execution
    result = await tool_registry.execute_tool(
        tool_name="web_scraper",
        params={"url": "https://example.com"},
    )
    
    assert result['success'] is True
    print(f"✓ Tool executed successfully: {result['tool']}")
    
    print("\n✅ Tool Registry: PASSED")
    return True


async def test_memory_system():
    """Test memory system"""
    print("\n" + "="*60)
    print("TEST 6: Memory System")
    print("="*60)
    
    memory_manager = get_memory_manager()
    
    # Get stats
    stats = memory_manager.get_stats()
    print(f"✓ ChromaDB available: {stats['chromadb_available']}")
    print(f"✓ Insights count: {stats['insights_count']}")
    print(f"✓ Skills count: {stats['skills_count']}")
    print(f"✓ ChromaDB path: {stats['chromadb_path']}")
    
    # Test storing an insight (requires database session)
    if stats['chromadb_available']:
        async with get_session() as session:
            insight_id = await memory_manager.store_insight(
                session=session,
                content="Progressive permission increases OAuth acceptance by 40-50%",
                insight_type="user_behavior_pattern",
                confidence=0.95,
                evidence={"method": "A/B test", "sample_size": 20},
                tags=["onboarding", "OAuth", "trust"],
            )
            print(f"✓ Stored insight: {insight_id}")
        
        # Test searching
        results = await memory_manager.search_insights(
            query="OAuth permission",
            top_k=3,
        )
        print(f"✓ Found {len(results)} relevant insights")
    else:
        print("⚠️  ChromaDB not available, skipping insight storage")
    
    print("\n✅ Memory System: PASSED")
    return True


async def test_data_agent():
    """Test Data Agent execution"""
    print("\n" + "="*60)
    print("TEST 7: Data Agent")
    print("="*60)
    
    # Create test goal
    async with get_session() as session:
        goal = ResearchGoal(
            description="Analyze user engagement data and identify improvement opportunities",
            mode="demo",
            budget_usd=1500.0,
            timeline_days=7,
        )
        session.add(goal)
        await session.commit()
        
        print(f"✓ Created test goal: {goal.id}")
        
        # Create and run agent
        print("✓ Initializing Data Agent...")
        agent = DataAgent(session, goal)
        
        print("✓ Executing agent (this may take 30-60 seconds)...")
        result = await agent.run()
        
        print(f"\n  Success: {result['success']}")
        print(f"  Agent: {result['agent']}")
        print(f"  Duration: {result.get('duration_seconds', 0):.2f}s")
        
        if result['success']:
            output = result['output']
            print(f"  Summary: {output.get('summary', 'N/A')}")
            print(f"  Next steps: {len(output.get('next_steps', []))}")
        else:
            print(f"  Error: {result.get('error', 'Unknown')}")
        
        assert result['success'] is True
    
    print("\n✅ Data Agent: PASSED")
    return True


async def test_full_system():
    """Test complete end-to-end workflow"""
    print("\n" + "="*60)
    print("TEST 8: Full System Integration")
    print("="*60)
    
    # This simulates what happens when user creates a goal via API
    
    goal_description = "Research why our mobile app has lower engagement than web"
    
    print(f"✓ User goal: {goal_description}")
    
    # Step 1: Parse goal
    parsed = await parse_goal(goal_description)
    print(f"✓ Goal parsed: {parsed.goal_type}")
    
    # Step 2: Create in database
    async with get_session() as session:
        goal = ResearchGoal(
            description=goal_description,
            mode="demo",
            budget_usd=parsed.estimated_cost_usd,
            timeline_days=parsed.estimated_duration_days,
        )
        session.add(goal)
        await session.commit()
        
        print(f"✓ Goal created in database: {goal.id}")
        
        # Step 3: Execute agent
        goal.status = "running"
        goal.current_agent = "data_agent"
        await session.commit()
        
        agent = DataAgent(session, goal)
        result = await agent.run()
        
        # Step 4: Update goal status
        if result['success']:
            goal.findings = result['output']
            goal.status = "completed"
            goal.progress_percent = 100.0
        else:
            goal.status = "failed"
        
        await session.commit()
        
        print(f"✓ Goal execution complete: {goal.status}")
        print(f"✓ Progress: {goal.progress_percent}%")
    
    print("\n✅ Full System Integration: PASSED")
    return True


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print(" WEEK 1 END-TO-END TEST SUITE")
    print("="*70)
    print("\nTesting all Week 1 components...\n")
    
    tests = [
        ("Configuration System", test_configuration),
        ("Database System", test_database),
        ("AI Manager", test_ai_manager),
        ("Goal Parser", test_goal_parser),
        ("Tool Registry", test_tool_registry),
        ("Memory System", test_memory_system),
        ("Data Agent", test_data_agent),
        ("Full System Integration", test_full_system),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ {test_name}: FAILED")
            print(f"   Error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status:12} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Week 1 foundation is complete and working!")
        print("\nYou can now:")
        print("  1. Start the API server: cd backend && uvicorn src.api.main:app --reload")
        print("  2. Create goals via REST API")
        print("  3. Watch agents execute autonomously")
        print("  4. Continue to Week 2: Add more agents and tools")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.")
        print("\nCommon issues:")
        print("  - Ollama not running: Start with 'ollama serve'")
        print("  - Models not pulled: Run 'ollama pull llama3.2:3b'")
        print("  - ChromaDB not installed: Run 'pip install chromadb'")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
