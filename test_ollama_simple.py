"""
Simple Ollama Test for Agentic Research AI
============================================

This script checks if Ollama is properly configured and working.
"""

import asyncio
import aiohttp
import sys

# Configuration from .env
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:3b"


def print_header(text):
    """Print a header with separators."""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


async def check_ollama_running():
    """Check if Ollama server is running."""
    print_header("CHECKING OLLAMA STATUS")
    print(f"\n[>] Ollama URL: {OLLAMA_URL}")
    print(f"[>] Configured Model: {OLLAMA_MODEL}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{OLLAMA_URL}/api/tags",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    models = [m["name"] for m in data.get("models", [])]
                    
                    print(f"\n[OK] Ollama is RUNNING!")
                    print(f"[i] Available Models ({len(models)}):")
                    for model in models:
                        marker = " <-- CONFIGURED" if OLLAMA_MODEL in model else ""
                        print(f"    - {model}{marker}")
                    
                    # Check if configured model is available
                    has_model = any(OLLAMA_MODEL in m for m in models)
                    if has_model:
                        print(f"\n[OK] Configured model '{OLLAMA_MODEL}' is AVAILABLE!")
                        return True
                    else:
                        print(f"\n[!] Configured model '{OLLAMA_MODEL}' NOT found!")
                        print(f"\n[*] To fix, run: ollama pull {OLLAMA_MODEL}")
                        return False
                else:
                    print(f"\n[ERROR] Ollama returned status: {response.status}")
                    return False
    except aiohttp.ClientConnectorError:
        print(f"\n[ERROR] Cannot connect to Ollama at {OLLAMA_URL}")
        print("\n[*] Make sure Ollama is running:")
        print("    - Windows: Start Ollama app or run 'ollama serve'")
        print("    - Check if port 11434 is accessible")
        print("    - Try: ollama list")
        return False
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return False


async def test_ollama_generation():
    """Test if Ollama can generate text."""
    print_header("TESTING AI GENERATION")
    
    test_prompt = "Say 'Ollama integration test successful' in one short sentence."
    
    print(f"\n[>] Sending test prompt...")
    print(f"    Prompt: {test_prompt}")
    
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": test_prompt,
                "temperature": 0.7,
                "num_predict": 50,
                "stream": False,
            }
            
            async with session.post(
                f"{OLLAMA_URL}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get("response", "")
                    
                    print(f"\n[OK] AI Generation SUCCESS!")
                    print(f"[i] Response: {content.strip()}")
                    print(f"[i] Tokens: {data.get('eval_count', 0)} generated")
                    return True
                else:
                    error_text = await response.text()
                    print(f"\n[ERROR] Generation failed: {response.status}")
                    print(f"    Error: {error_text[:200]}")
                    return False
                    
    except Exception as e:
        print(f"\n[ERROR] Generation error: {e}")
        return False


def check_env_file():
    """Check the .env file configuration."""
    print_header("CHECKING ENVIRONMENT CONFIGURATION")
    
    env_path = "files (6)/AGENTIC-AI-VERIFIED-FIXES/agentic-research-ai-FIXED/.env"
    
    try:
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Parse key settings
        settings = {}
        for line in content.split('\n'):
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                settings[key.strip()] = value.strip()
        
        app_mode = settings.get('APP_MODE', 'NOT SET').split()[0]  # Remove comments
        debug = settings.get('DEBUG', 'NOT SET')
        ollama_model = settings.get('OLLAMA_MODEL', 'NOT SET')
        ollama_url = settings.get('OLLAMA_BASE_URL', 'NOT SET')
        
        print(f"\n[i] APP_MODE: {app_mode} {'[OK]' if app_mode == 'demo' else '[!]'}")
        print(f"[i] DEBUG: {debug}")
        print(f"[i] OLLAMA_MODEL: {ollama_model}")
        print(f"[i] OLLAMA_BASE_URL: {ollama_url}")
        
        if app_mode == 'demo':
            print("\n[OK] Demo mode is properly configured")
        else:
            print("\n[!] App is not in demo mode")
            
        return app_mode == 'demo'
        
    except FileNotFoundError:
        print(f"\n[ERROR] .env file not found at {env_path}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Error reading .env: {e}")
        return False


async def main():
    """Run all checks."""
    print("\n" + "=" * 60)
    print("  OLLAMA + DEMO MODE VERIFICATION")
    print("=" * 60 + "\n")
    
    # Check 1: Environment
    env_ok = check_env_file()
    
    # Check 2: Ollama running
    ollama_ok = await check_ollama_running()
    
    # Check 3: AI generation (only if Ollama is running)
    ai_ok = False
    if ollama_ok:
        ai_ok = await test_ollama_generation()
    
    # Summary
    print_header("SUMMARY")
    print(f"\n[{'OK' if env_ok else 'FAIL'}] Environment Config: {'OK' if env_ok else 'ISSUES'}")
    print(f"[{'OK' if ollama_ok else 'FAIL'}] Ollama Running: {'YES' if ollama_ok else 'NO'}")
    print(f"[{'OK' if ai_ok else 'FAIL'}] AI Generation: {'WORKING' if ai_ok else 'NOT WORKING'}")
    
    print("\n" + "=" * 60)
    if env_ok and ollama_ok and ai_ok:
        print("[SUCCESS] ALL CHECKS PASSED!")
        print("   Your app is ready to use with Ollama in demo mode!")
        print("\n   Next steps:")
        print("   1. cd 'files (6)/AGENTIC-AI-VERIFIED-FIXES/agentic-research-ai-FIXED/backend'")
        print("   2. uvicorn src.api.main:app --reload")
        print("   3. Open http://localhost:8000/health to verify")
    elif env_ok and not ollama_ok:
        print("[WARNING] PARTIAL SETUP")
        print("   Demo mode is configured, but Ollama is not running.")
        print("\n   To start Ollama:")
        print("   1. Open a new terminal")
        print("   2. Run: ollama serve")
        print("   3. Or start the Ollama desktop app")
        print("\n   The app will run but AI agents won't generate content.")
    else:
        print("[ERROR] SETUP INCOMPLETE")
        print("   Please fix the issues above.")
    print("=" * 60)
    
    return env_ok and ollama_ok and ai_ok


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n[!] Check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
