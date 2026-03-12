# 🎯 ACTION PLAN - Priority Fixes & Completions

Based on the comprehensive audit, here's what needs to be done in priority order.

---

## 🔴 CRITICAL (Do Immediately)

### 1. Fix QUICKSTART.md - 30 minutes

**Problem:** Commands don't work, will frustrate users

**Fix:**

```markdown
# REPLACE THIS (broken):
cd backend
python -c "import asyncio; from src.database.session import init_db; asyncio.run(init_db())"

# WITH THIS (working):
cd backend
python -c "from src.database.session import init_db; import asyncio; asyncio.run(init_db())"
```

```markdown
# REPLACE THIS (wrong):
cd frontend && python -m http.server 3000

# WITH THIS (correct):
cd frontend-nextjs
npm install
npm run dev
```

**Add Missing Steps:**
```bash
# Before running frontend, set environment:
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" >> frontend-nextjs/.env.local
echo "NEXT_PUBLIC_WS_URL=ws://localhost:8000" >> frontend-nextjs/.env.local
```

---

### 2. Copy Missing Agents - 1 hour

**Problem:** Interview and Feedback agents missing from files (6)

**Fix:**
```bash
# Copy from files (5) to files (6):
copy "files (5)\AGENTIC-RESEARCH-AI-PROFESSIONALLY-FIXED\agentic-research-ai-FIXED\backend\src\agents\interview\agent.py" "files (6)\AGENTIC-AI-VERIFIED-FIXES\agentic-research-ai-FIXED\backend\src\agents\interview\agent.py"

copy "files (5)\AGENTIC-RESEARCH-AI-PROFESSIONALLY-FIXED\agentic-research-ai-FIXED\backend\src\agents\feedback\agent.py" "files (6)\AGENTIC-AI-VERIFIED-FIXES\agentic-research-ai-FIXED\backend\src\agents\feedback\agent.py"
```

**Register in orchestrator.py:**
```python
# Add to _create_agent() method in orchestrator.py (around line 390):

elif agent_name == constants.AGENT_INTERVIEW:
    from src.agents.interview.agent import InterviewAgent
    agent = InterviewAgent(self.session, self.goal)

elif agent_name == constants.AGENT_FEEDBACK:
    from src.agents.feedback.agent import FeedbackAgent
    agent = FeedbackAgent(self.session, self.goal)
```

---

### 3. Update README.md Accuracy - 30 minutes

**Problem:** Claims don't match reality

**Fix:**
```markdown
# REPLACE:
- "All 7 agents working"
- "Backend 95% Complete"
- "Frontend 30% Complete"

# WITH:
- "5 agents implemented, 2 in progress"
- "Backend ~78% Complete"
- "Frontend ~60% Complete"
```

---

## 🟡 HIGH PRIORITY (This Week)

### 4. Complete Multi-Agent Orchestration - 6-8 hours

**Problem:** Agent handoff not fully wired

**Steps:**

1. **Test current orchestration:**
```bash
cd backend
uvicorn src.api.main:app --reload

# In another terminal:
curl -X POST http://localhost:8000/goals \
  -H "Content-Type: application/json" \
  -d '{"description": "Analyze user activation data", "budget_usd": 2000}'
```

2. **Fix agent handoff in orchestrator.py:**
```python
# In _execute_sequential(), after agent completes:

# Store output
await self._store_agent_output(agent_name, result["output"])

# Create handoff for next agent
if idx < len(self.agent_sequence) - 1:
    next_agent = self.agent_sequence[idx + 1]
    handoff = self._create_handoff(agent_name, next_agent, result["output"])
    self.context.add_handoff(handoff)
    
    # Inject handoff into next agent's context
    next_agent_context = self.context.get_context_for_agent(next_agent)
    next_agent_context["handoff_from"] = agent_name
    next_agent_context["handoff_data"] = result["output"]
```

3. **Add WebSocket integration:**
```python
# In execute() method, send updates:

await self._send_websocket_update({
    "type": "agent_started",
    "agent": agent_name,
    "goal_id": self.goal.id,
})

# After completion:
await self._send_websocket_update({
    "type": "agent_completed",
    "agent": agent_name,
    "success": result["success"],
})
```

---

### 5. Activate ReAct Engine - 4-5 hours

**Problem:** Framework exists but not integrated

**Steps:**

1. **Import in base.py:**
```python
from src.core.react_engine import run_react_loop, ReActState
```

2. **Modify BaseAgent.run():**
```python
async def run(self) -> Dict[str, Any]:
    # Check if goal requires ReAct loop
    if self.goal.mode == "autonomous":
        # Use ReAct loop
        result = await run_react_loop(
            agent=self,
            goal=self.goal,
            session=self.session,
        )
    else:
        # Use direct execution
        result = await self.execute()
    
    return result
```

3. **Test ReAct loop:**
```python
# Create test script:
async def test_react():
    from src.core.react_engine import run_react_loop
    
    # Create test goal and agent
    # Run ReAct loop
    # Verify Think-Act-Observe-Learn cycle
```

---

### 6. Integrate WebSocket Updates - 2-3 hours

**Problem:** WebSocket endpoint exists but not used

**Steps:**

1. **In main.py, import manager in execute_goal():**
```python
async def execute_goal(goal_id: str):
    from src.api.main import manager as ws_manager
    
    # ... existing code ...
    
    # Send update when starting
    await ws_manager.send_update(goal_id, {
        "type": "goal_started",
        "goal_id": goal_id,
    })
    
    # Send updates during execution
    await ws_manager.send_update(goal_id, {
        "type": "progress_update",
        "progress_percent": 50,
        "current_agent": "data_agent",
    })
```

2. **Test WebSocket connection:**
```javascript
// In browser console on frontend:
const ws = new WebSocket('ws://localhost:8000/ws/YOUR_GOAL_ID');
ws.onmessage = (event) => console.log(JSON.parse(event.data));
```

---

### 7. Complete Frontend Pages - 4-6 hours

**Problem:** /projects, /settings, /team are empty

**Steps:**

1. **Create projects page:**
```bash
# Create file:
frontend-nextjs/app/projects/page.tsx
```

```typescript
'use client'

import { useGoals } from '@/hooks/useGoals'

export default function ProjectsPage() {
  const { goals, loading } = useGoals()
  
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Projects</h1>
      {loading ? (
        <div>Loading...</div>
      ) : (
        <div className="grid gap-4">
          {goals.map(goal => (
            <div key={goal.id} className="border p-4 rounded">
              <h3>{goal.description}</h3>
              <p>Status: {goal.status}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

2. **Create settings page:**
```bash
frontend-nextjs/app/settings/page.tsx
```

3. **Create team page:**
```bash
frontend-nextjs/app/team/page.tsx
```

---

## 🟢 MEDIUM PRIORITY (Next Week)

### 8. Test Connectors - 8-10 hours

**Problem:** Connectors exist but untested

**Steps:**

1. **Test PostHog:**
```python
# Create test script:
async def test_posthog():
    from src.connectors.posthog import PostHogConnector
    
    connector = PostHogConnector()
    
    # Test event query
    result = await connector.query_events(
        event_name="button_clicked",
        limit=10,
    )
    print(result)
    
    # Test funnel
    funnel = await connector.build_funnel(
        steps=["signup", "email_verify", "oauth"],
    )
    print(funnel)
```

2. **Implement GA4/BigQuery:**
```python
# Expand ga4_bigquery.py with real implementation
# Add BigQuery client
# Write SQL queries for GA4 data
```

---

### 9. Add File Upload Processing - 4-5 hours

**Problem:** Upload endpoint exists but doesn't process files

**Steps:**

1. **Complete upload.py:**
```python
@upload_router.post("/upload/csv")
async def upload_csv(file: UploadFile):
    # Read CSV
    content = await file.read()
    df = pd.read_csv(io.BytesIO(content))
    
    # Analyze
    analysis = await analyze_dataframe(df)
    
    return {"rows": len(df), "columns": list(df.columns)}
```

2. **Add pandas integration:**
```python
async def analyze_dataframe(df):
    # Generate stats
    # Detect patterns
    # Suggest insights
```

---

### 10. Expand Test Coverage - 10-15 hours

**Problem:** Only 45% test coverage

**Steps:**

1. **Add agent tests:**
```python
# backend/tests/agents/test_data_agent.py
async def test_data_agent_demo_mode():
    agent = DataAgent(session, goal)
    result = await agent.run()
    assert result["success"] is True
    assert "data_collected" in result["output"]
```

2. **Add API tests:**
```python
# backend/tests/api/test_goals.py
def test_create_goal():
    response = client.post("/goals", json={
        "description": "Test goal"
    })
    assert response.status_code == 201
```

3. **Add integration tests:**
```python
# backend/tests/integration/test_full_workflow.py
async def test_full_research_workflow():
    # Create goal
    # Run orchestration
    # Verify all agents executed
```

---

## 📋 QUICK REFERENCE: What Works Now

### ✅ Verified Working Commands

```bash
# 1. Start Backend
cd "files (6)\AGENTIC-AI-VERIFIED-FIXES\agentic-research-ai-FIXED\backend"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload

# 2. Test Health
curl http://localhost:8000/health

# 3. Create Goal
curl -X POST http://localhost:8000/goals ^
  -H "Content-Type: application/json" ^
  -d "{\"description\": \"Analyze activation rate\", \"mode\": \"demo\"}"

# 4. List Goals
curl http://localhost:8000/goals

# 5. Start Frontend
cd "files (6)\AGENTIC-AI-VERIFIED-FIXES\agentic-research-ai-FIXED\frontend-nextjs"
npm install
npm run dev
```

### ⚠️ Known Limitations

- Multi-agent orchestration incomplete
- WebSocket not integrated
- 2 agents missing (Interview, Feedback)
- Connectors mostly stubs
- ReAct engine not active

---

## 📊 PRIORITY MATRIX

| Task | Impact | Effort | Priority |
|------|--------|--------|----------|
| Fix QUICKSTART.md | High | Low | 🔴 1 |
| Copy Missing Agents | High | Low | 🔴 2 |
| Update README | Medium | Low | 🔴 3 |
| Complete Orchestration | High | High | 🟡 4 |
| Activate ReAct Engine | High | Medium | 🟡 5 |
| Integrate WebSocket | Medium | Medium | 🟡 6 |
| Complete Frontend Pages | Medium | Medium | 🟡 7 |
| Test Connectors | Medium | High | 🟢 8 |
| Add File Upload | Medium | Medium | 🟢 9 |
| Expand Tests | Medium | High | 🟢 10 |

---

## 🎯 2-WEEK SPRINT PLAN

### Week 1: Critical Fixes
- [x] Day 1: Fix documentation (1 hour)
- [x] Day 1: Copy missing agents (1 hour)
- [ ] Day 2-3: Complete orchestration (6 hours)
- [ ] Day 4: Integrate WebSocket (3 hours)
- [ ] Day 5: Test end-to-end (4 hours)

### Week 2: Feature Completion
- [ ] Day 1-2: Activate ReAct engine (5 hours)
- [ ] Day 3-4: Complete frontend pages (6 hours)
- [ ] Day 5: Test connectors (4 hours)

**Result after 2 weeks:** ~85% functional system

---

**Created:** March 2, 2026  
**Based on:** Comprehensive Project Audit  
**Estimated Total Effort:** ~40 hours to 85% completion
