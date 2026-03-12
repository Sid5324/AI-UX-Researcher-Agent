# 🚀 QUICKSTART GUIDE
## Get Running in 10 Minutes

### Prerequisites

- Python 3.11+
- Node.js 18+
- Ollama (optional, but recommended)

---

### Backend Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database (FIXED COMMAND)
python -c "from src.database.session import AsyncSessionLocal, init_db; import asyncio; asyncio.run(init_db())"

# 5. Start backend
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend now running on:** http://localhost:8000  
**API Docs:** http://localhost:8000/docs

---

### Frontend Setup

```bash
# 1. Navigate to frontend
cd frontend-nextjs

# 2. Install dependencies
npm install

# 3. Configure environment (ADDED)
# Create .env.local file:
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
echo "NEXT_PUBLIC_WS_URL=ws://localhost:8000" >> .env.local

# 4. Start frontend
npm run dev
```

**Frontend now running on:** http://localhost:3000

---

### Test the System

1. **Open frontend:** http://localhost:3000
2. **Register account**
3. **Create goal:** "Create PRD and UI/UX design for mobile app"
4. **Watch agents execute** in real-time with WebSocket updates

**Expected:** All 3 agents (data → PRD → UI/UX) should execute in sequence with live progress updates!

---

### Optional: Ollama Setup

```bash
# Install Ollama from https://ollama.ai

# Pull model
ollama pull llama3.2:3b

# Start Ollama (runs automatically on port 11434)
```

**Without Ollama:** System will use demo mode or fallback to cloud APIs.

---

## Testing Multi-Agent Flow

```bash
# Test multi-agent workflow:
curl -X POST http://localhost:8000/goals \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Conduct comprehensive product research including data analysis, create detailed PRD, and design complete UI/UX mockups for mobile app",
    "budget_usd": 5000
  }'

# Expected result:
# - 3 agents execute: data_agent → prd_agent → ui_ux_agent
# - WebSocket sends 10+ events (goal_started, 3x agent_started, progress_updates, 3x agent_completed, goal_completed)
# - Database has 3 agent_states rows
# - final_output contains: data_findings, product_strategy, design_specs
```

---

## Troubleshooting

### Database Issues
```bash
# If database init fails, try:
cd backend
python -c "from src.database.session import init_db; import asyncio; asyncio.run(init_db())"
```

### Frontend Connection Issues
```bash
# Verify .env.local exists in frontend-nextjs/:
cat frontend-nextjs/.env.local

# Should show:
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Agent Registration Issues
```bash
# Check all 7 agents are registered:
curl http://localhost:8000/health

# Should list all agents: data, prd, ui_ux, validation, competitor, interview, feedback
```

---

## What's Fixed in This Version

✅ **Goal Parser:** Multi-agent selection now works (not just data_agent)  
✅ **Frontend Config:** Added .env.local and next.config.js  
✅ **All 7 Agents:** Interview and Feedback agents now registered  
✅ **WebSocket Events:** 7 event types for real-time progress  
✅ **AI Manager:** Temperature parameter added for JSON generation  
✅ **Documentation:** Updated with correct database init command  

---

**Ready to go!** Start with the Backend Setup above.
