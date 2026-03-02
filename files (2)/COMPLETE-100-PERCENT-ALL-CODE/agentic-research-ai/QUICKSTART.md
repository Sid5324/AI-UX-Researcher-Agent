# 🚀 QUICK START GUIDE - Week 1 Complete System

## **Get Running in 5 Minutes**

### **Step 1: Extract & Setup** (2 minutes)

```bash
# 1. Extract the archive
tar -xzf agentic-research-ai-week1.tar.gz
cd agentic-research-ai

# 2. Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Create environment file
cp .env.example .env
```

### **Step 2: Verify Ollama** (1 minute)

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it:
# - macOS: Open Ollama app
# - Linux: sudo systemctl start ollama

# Pull required model (if not already pulled)
ollama pull llama3.2:3b
```

### **Step 3: Initialize Database** (30 seconds)

```bash
# Initialize database
cd backend
python -c "import asyncio; from src.database.session import init_db; asyncio.run(init_db())"

# Verify
python -c "import asyncio; from src.database.session import check_db_connection; print('DB OK' if asyncio.run(check_db_connection()) else 'DB FAIL')"
```

### **Step 4: Run Tests** (1 minute)

```bash
# Go back to project root
cd ..

# Run comprehensive test suite
python test_week1.py

# Expected output:
# ✅ Configuration System: PASSED
# ✅ Database System: PASSED
# ✅ AI Manager: PASSED
# ... (8 tests total)
# 🎉 ALL TESTS PASSED!
```

### **Step 5: Start the System** (30 seconds)

#### **Option A: Just API (for development)**

```bash
cd backend
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

#### **Option B: API + Dashboard (for demo)**

Terminal 1 (API):
```bash
cd backend
uvicorn src.api.main:app --reload
```

Terminal 2 (Dashboard):
```bash
cd frontend
python -m http.server 3000
```

Then open: **http://localhost:3000**

---

## **Test It Works**

### **Method 1: Using the Dashboard** (Easiest)

1. Open http://localhost:3000
2. Enter a goal: "Analyze user engagement and find improvement opportunities"
3. Click "Start Autonomous Research"
4. Watch the agent work! 🤖

### **Method 2: Using cURL** (For API testing)

```bash
# Create a goal
curl -X POST http://localhost:8000/goals \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Research why users are churning after 7 days",
    "budget_usd": 1500,
    "timeline_days": 7
  }'

# Response: {"id": "abc123", "status": "pending", ...}

# Check goal status
curl http://localhost:8000/goals/abc123

# List all goals
curl http://localhost:8000/goals
```

### **Method 3: Using Python** (For scripting)

```python
import asyncio
from backend.src.database.session import get_session
from backend.src.database.models import ResearchGoal
from backend.src.agents.data.agent import DataAgent

async def create_and_run_goal():
    async with get_session() as session:
        # Create goal
        goal = ResearchGoal(
            description="Find UX issues in our onboarding flow",
            mode="demo",
            budget_usd=2000,
            timeline_days=7,
        )
        session.add(goal)
        await session.commit()
        
        print(f"Created goal: {goal.id}")
        
        # Run agent
        agent = DataAgent(session, goal)
        result = await agent.run()
        
        print(f"Result: {result['success']}")
        if result['success']:
            print(f"Output: {result['output']['summary']}")

asyncio.run(create_and_run_goal())
```

---

## **What You Can Do Now**

### ✅ **Working Features**

1. **Create Research Goals** (natural language)
   - "Fix our activation rate decline"
   - "Understand why users churn after 7 days"
   - "Find improvement opportunities in onboarding"

2. **Autonomous Execution** (Demo Mode)
   - Agent generates realistic synthetic data
   - Analyzes data with LLM reasoning
   - Extracts insights automatically
   - Provides recommendations

3. **Progress Monitoring**
   - Real-time dashboard updates
   - Status tracking (pending → running → completed)
   - Progress percentage
   - Agent activity logs

4. **REST API**
   - Create goals: POST /goals
   - List goals: GET /goals
   - Get details: GET /goals/{id}
   - System info: GET /info

5. **Memory System**
   - Semantic memory (ChromaDB)
   - Insight storage
   - Cross-project learning

---

## **Example Workflows**

### **Workflow 1: Quick Demo**

```bash
# 1. Start API
cd backend && uvicorn src.api.main:app --reload

# 2. In another terminal, create goal
curl -X POST http://localhost:8000/goals \
  -H "Content-Type: application/json" \
  -d '{"description": "Analyze engagement metrics"}'

# 3. Watch logs in API terminal - agent executes automatically!

# 4. Check result
curl http://localhost:8000/goals | jq '.[0]'
```

### **Workflow 2: Full Dashboard Demo**

1. Start API: `cd backend && uvicorn src.api.main:app --reload`
2. Start dashboard: `cd frontend && python -m http.server 3000`
3. Open browser: http://localhost:3000
4. Create goal in UI
5. Watch real-time progress
6. See completed results

### **Workflow 3: Python Script Integration**

```python
# your_script.py
import asyncio
import httpx

async def create_goal():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/goals",
            json={
                "description": "Your research goal here",
                "budget_usd": 2000,
                "timeline_days": 7,
            }
        )
        goal = response.json()
        print(f"Goal created: {goal['id']}")
        return goal['id']

asyncio.run(create_goal())
```

---

## **Troubleshooting**

### **Problem: "Ollama not available"**

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it
# macOS: Open Ollama app
# Linux: sudo systemctl start ollama

# Pull required model
ollama pull llama3.2:3b
```

### **Problem: "ModuleNotFoundError"**

```bash
# Make sure you're in venv
source venv/bin/activate

# Reinstall dependencies
pip install -r backend/requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

### **Problem: "Database locked"**

```bash
# Reset database
cd backend
python -c "import asyncio; from src.database.session import reset_db; asyncio.run(reset_db())"
```

### **Problem: "ChromaDB error"**

```bash
# ChromaDB is optional - system works without it
# But if you want to fix it:
pip install chromadb==0.4.22

# Or disable it by removing semantic memory features
```

### **Problem: "API returns 500 error"**

```bash
# Check API logs for details
# Common causes:
# 1. Database not initialized: run init_db()
# 2. Ollama not running: start Ollama
# 3. Import errors: check Python path
```

---

## **What's Next?**

You've completed **Week 1 Foundation**! 🎉

### **Immediate Next Steps:**

1. **Test thoroughly:**
   - Create 3-5 different goals
   - Verify agent execution
   - Check database persistence

2. **Customize:**
   - Edit `.env` for your settings
   - Add custom tools in `tools/registry.py`
   - Adjust agent behavior in `agents/data/agent.py`

3. **Explore:**
   - Read the code comments
   - Try different goal types
   - Experiment with demo mode vs real mode

### **Week 2 Plans: (Next 7 days)**

1. **More Agents:**
   - PRD Agent (generates product requirements)
   - UI/UX Agent (creates wireframes, prototypes)
   - Validator Agent (runs A/B tests, surveys)

2. **More Tools:**
   - Real analytics connectors (PostHog, GA4)
   - Email/Slack notifications
   - File generation (PDFs, presentations)

3. **ReAct Loop Integration:**
   - Full Think→Act→Observe→Learn cycle
   - Dynamic task planning
   - Self-correction on failures

4. **Better UI:**
   - Next.js frontend
   - Real-time WebSocket updates
   - Checkpoint approval UI

---

## **Need Help?**

1. **Check logs:**
   - API logs: Terminal where uvicorn is running
   - Database: `data/agentic_research.db`
   - ChromaDB: `data/chromadb/`

2. **Run diagnostics:**
   ```bash
   python test_week1.py  # Comprehensive test suite
   ```

3. **Verify configuration:**
   ```bash
   cd backend
   python -c "from src.core.config import settings; print(settings.dict())"
   ```

---

## **Success Checklist**

- [ ] Ollama running with llama3.2:3b model
- [ ] Python venv activated
- [ ] Dependencies installed
- [ ] Database initialized
- [ ] Test suite passes (8/8 tests)
- [ ] API server starts successfully
- [ ] Can create goal via API or dashboard
- [ ] Agent executes and completes goal
- [ ] Can view results

If all checked ✅, you're ready to build! 🚀

---

**You now have a working autonomous AI research system!**

The agent can:
- ✅ Parse natural language goals
- ✅ Generate realistic demo data
- ✅ Analyze data with LLM reasoning
- ✅ Extract insights automatically
- ✅ Provide recommendations
- ✅ Store results in database
- ✅ Expose REST API
- ✅ Serve web dashboard

**Next: Continue to Week 2 for more agents and full ReAct loop integration!**
