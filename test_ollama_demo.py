"""
Test Ollama Integration with Demo Mode
=======================================

This script verifies:
1. Ollama is running and accessible
2. The configured model is available
3. Demo mode is properly configured
4. AI generation works through the AIManager
"""

import asyncio
import sys
import os

# Fix: Remove conflicting environment variables
# These can interfere with Pydantic Settings boolean parsing
env_vars_to_clear = ['DEBUG', 'APP_MODE']
for var in env_vars_to_clear:
    if var in os.environ:
        del os.environ[var]

# Add the backend src to path
backend_path = os.path.join("files (6)", "AGENTIC-AI-VERIFIED-FIXES", "agentic-research-ai-FIXED", "backend", "src")
sys.path.insert(0, backend_path)

from core.config import get_settings
from core.ai_manager import get_ai_manager
import aiohttp


async def check_ollama_running():
    """Check if Ollama server is running."""
    settings = get_settings()
    ollama_url = settings.ollama_base_url
    
    print("=" * 60)
    print("🔍 CHECKING OLLAMA STATUS")
    print("=" * 60)
    print(f"\n📍 Ollama URL: {ollama_url}")
    print(f"🤖 Configured Model: {settings.ollama_model}")
    print(f"⏱️  Timeout: {settings.ollama_timeout}s")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{ollama_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    models = [m["name"] for m in data.get("models", [])]
                    
                    print(f"\n✅ Ollama is RUNNING!")
                    print(f"📦 Available Models: {', '.join(models) if models else 'None'}")
                    
                    # Check if configured model is available
                    target_model = settings.ollama_model
                    if target_model in models or any(target_model in m for m in models):
                        print(f"✅ Configured model '{target_model}' is AVAILABLE!")
                        return True
                    else:
                        print(f"⚠️  Configured model '{target_model}' NOT found!")
                        print(f"   Available: {models}")
                        print(f"\n💡 To fix, run: ollama pull {target_model}")
                        return False
                else:
                    print(f"\n❌ Ollama returned status: {response.status}")
                    return False
    except aiohttp.ClientConnectorError as e:
        print(f"\n❌ Cannot connect to Ollama: {e}")
        print("\n💡 Make sure Ollama is running:")
        print("   - Windows: Start Ollama app or run 'ollama serve'")
        print("   - Check if port 11434 is accessible")
        return False
    except Exception as e:
        print(f"\n❌ Error checking Ollama: {e}")
        return False


async def check_demo_mode():
    """Check demo mode configuration."""
    settings = get_settings()
    
    print("\n" + "=" * 60)
    print("🔍 CHECKING DEMO MODE")
    print("=" * 60)
    print(f"\n📱 App Mode: {settings.app_mode}")
    print(f"🎯 Is Demo Mode: {settings.is_demo_mode}")
    
    if settings.is_demo_mode:
        print("✅ Demo mode is ACTIVE - will use synthetic data for APIs")
    else:
        print("⚠️  Demo mode is NOT active - will try to use real APIs")
    
    return settings.is_demo_mode


async def test_ai_generation():
    """Test AI generation through AIManager."""
    print("\n" + "=" * 60)
    print("🤖 TESTING AI GENERATION")
    print("=" * 60)
    
    ai_manager = get_ai_manager()
    
    # Test health check
    print("\n📊 Checking AI manager health...")
    ollama_healthy = await ai_manager.check_ollama_health()
    
    if ollama_healthy:
        print("✅ Ollama is healthy according to AI manager")
        
        # Try to generate something
        print("\n📝 Testing text generation...")
        try:
            result = await ai_manager.generate(
                prompt="Say 'Ollama is working with Agentic Research AI' in one sentence.",
                system="You are a helpful assistant.",
                max_tokens=50,
                temperature=0.7
            )
            
            print(f"\n✅ AI Generation SUCCESS!")
            print(f"📤 Model Used: {result['model']}")
            print(f"🔌 Provider: {result['provider']}")
            print(f"💰 Cost: ${result['cost']}")
            print(f"📝 Response: {result['content'][:200]}...")
            return True
            
        except Exception as e:
            print(f"\n❌ AI Generation FAILED: {e}")
            return False
    else:
        print("❌ Ollama is not healthy - AI generation will use fallbacks or fail")
        return False


async def main():
    """Run all checks."""
    print("\n" + "🚀" * 30)
    print("  OLLAMA + DEMO MODE VERIFICATION")
    print("🚀" * 30 + "\n")
    
    # Check 1: Ollama running
    ollama_ok = await check_ollama_running()
    
    # Check 2: Demo mode
    demo_ok = await check_demo_mode()
    
    # Check 3: AI generation (only if Ollama is running)
    ai_ok = False
    if ollama_ok:
        ai_ok = await test_ai_generation()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    print(f"\n{'✅' if ollama_ok else '❌'} Ollama Running: {'YES' if ollama_ok else 'NO'}")
    print(f"{'✅' if demo_ok else '❌'} Demo Mode: {'ACTIVE' if demo_ok else 'INACTIVE'}")
    print(f"{'✅' if ai_ok else '❌'} AI Generation: {'WORKING' if ai_ok else 'NOT WORKING'}")
    
    print("\n" + "=" * 60)
    if ollama_ok and demo_ok and ai_ok:
        print("🎉 ALL CHECKS PASSED!")
        print("   Your app is ready to use with Ollama in demo mode!")
    elif demo_ok and not ollama_ok:
        print("⚠️  PARTIAL SETUP")
        print("   Demo mode works, but Ollama is not running.")
        print("   AI agents will not generate content.")
        print("\n   To start Ollama:")
        print("   1. Open terminal/command prompt")
        print("   2. Run: ollama serve")
        print("   3. Or start Ollama desktop app")
    else:
        print("❌ SETUP INCOMPLETE")
        print("   Please fix the issues above.")
    print("=" * 60)
    
    return ollama_ok and demo_ok


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
