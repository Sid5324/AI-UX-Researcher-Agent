# 🤖 Agentic Research AI - Production System

**An autonomous AI agent that conducts product research end-to-end with minimal human supervision.**

## 📋 **What We're Building**

A production-grade agentic AI system that:
- ✅ Accepts natural language goals ("Fix our activation rate decline")
- ✅ Autonomously executes ReAct loop (Think → Act → Observe → Learn)
- ✅ Runs multiple specialized agents (Data, PRD, UI/UX)
- ✅ Checkpoints at critical decisions only (2-3 per project)
- ✅ Delivers complete implementation packages (PRD, mockups, tickets)
- ✅ Learns from every project (research vault)

---

## 🏗️ **System Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                          │
│         Next.js 14 + WebSocket Real-Time Updates            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      API LAYER                              │
│              FastAPI + WebSocket Streaming                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  AGENTIC ORCHESTRATOR                       │
│         ReAct Loop + Dynamic Planning + Checkpoints         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────┬────────────────┬────────────────┬────────────┐
│  DATA AGENT  │   PRD AGENT    │ UI/UX DESIGNER │ VALIDATORS │
│              │                │                │            │
│ • Analytics  │ • Research Syn │ • Wireframes   │ • Stats    │
│ • Kaggle     │ • PRD Sections │ • Design Tokens│ • Surveys  │
│ • User Data  │ • Tech Specs   │ • Prototypes   │ • A/B Test │
└──────────────┴────────────────┴────────────────┴────────────┘
                            ↓
┌────────────┬──────────────┬──────────────┬────────────────┐
│   Ollama   │   ChromaDB   │   SQLite     │    Redis       │
│  (Local LLM)│  (Memory)   │   (State)    │   (Cache)      │
└────────────┴──────────────┴──────────────┴────────────────┘
```

---

## 🚀 **Current Build Status** (Week 1, Day 2)

### ✅ **Completed**

| Component | File | Status |
|-----------|------|--------|
| **Core Config** | `backend/src/core/config.py` | ✅ Dual mode (Real/Demo) |
| **Database Models** | `backend/src/database/models.py` | ✅ SQLAlchemy 2.0 async |
| **Session Manager** | `backend/src/database/session.py` | ✅ Connection pooling |
| **AI Manager** | `backend/src/core/ai_manager.py` | ✅ Multi-model + fallbacks |

### 🚧 **In Progress** (Next Steps)

- [ ] ReAct Loop Engine (core/react_engine.py)
- [ ] Goal Parser (core/goal_parser.py)
- [ ] Agent Base Class (agents/base.py)
- [ ] Data Agent (agents/data/agent.py)
- [ ] FastAPI Server (api/main.py)
- [ ] Next.js Frontend (frontend/)

---

## 📦 **Installation & Setup**

### **Prerequisites**

1. **Python 3.11+**
2. **Node.js 18+** (for frontend)
3. **Ollama** (for local LLMs)
   ```bash
   # Install Ollama from https://ollama.ai
   # Pull required models:
   ollama pull llama3.2:3b
   ollama pull qwen2.5-coder:7b
   ollama pull deepseek-r1:8b
   ollama pull nomic-embed-text
   ```

### **Backend Setup**

```bash
# 1. Navigate to project root
cd agentic-research-ai

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Create .env file
cp .env.example .env

# 5. Initialize database
cd backend
python -m src.database.session  # Will create tables

# 6. Run server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### **Frontend Setup** (Coming Soon)

```bash
cd frontend
npm install
npm run dev
```

---

## ⚙️ **Configuration**

### **Environment Variables** (.env)

```bash
# ===================
# Application
# ===================
APP_MODE=demo                    # "demo" or "real"
DEBUG=false
ENVIRONMENT=development

# ===================
# Database
# ===================
DATABASE_URL=sqlite+aiosqlite:///./data/agentic_research.db
USE_SUPABASE=false
# SUPABASE_URL=https://xxx.supabase.co
# SUPABASE_KEY=your_key

# ===================
# Ollama (Local LLM)
# ===================
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_FALLBACK_MODELS=qwen2.5-coder:7b,deepseek-r1:8b

# ===================
# Cloud LLMs (Optional)
# ===================
# OPENROUTER_API_KEY=sk-or-...
# ANTHROPIC_API_KEY=sk-ant-...
# GEMINI_API_KEY=...

# ===================
# Analytics (Real Mode)
# ===================
# POSTHOG_API_KEY=phc_...
# GA4_PROJECT_ID=your-project
# KAGGLE_USERNAME=...
# KAGGLE_KEY=...

# ===================
# Memory & Storage
# ===================
CHROMADB_PATH=./data/chromadb
USE_REDIS=false
# REDIS_URL=redis://localhost:6379/0

# ===================
# Observability
# ===================
ENABLE_TRACING=false
# LANGFUSE_PUBLIC_KEY=pk-...
# LANGFUSE_SECRET_KEY=sk-...

# ===================
# API Server
# ===================
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# ===================
# Agent Behavior
# ===================
MAX_REACT_ITERATIONS=10
CHECKPOINT_FREQUENCY=medium      # none/low/medium/high
AUTONOMOUS_MODE=supervised       # supervised/partial/full
```

---

## 📖 **Usage Examples**

### **Demo Mode** (No API Keys Required)

```python
from backend.src.core.config import settings

# Check mode
print(f"Running in {settings.app_mode} mode")

# Demo mode uses LLM-generated synthetic data
if settings.is_demo_mode:
    # Agent will generate realistic fake analytics data
    pass
```

### **Create Research Goal**

```python
from backend.src.database.models import ResearchGoal
from backend.src.database.session import get_session

async def create_goal():
    async with get_session() as session:
        goal = ResearchGoal(
            description="Fix our activation rate decline from 42% to 28%",
            mode="demo",
            budget_usd=2000.0,
            timeline_days=7,
        )
        session.add(goal)
        await session.commit()
        
        print(f"Created goal: {goal.id}")

# Run with: python -m asyncio your_script.py
```

### **Generate with AI**

```python
from backend.src.core.ai_manager import generate

async def test_ai():
    result = await generate(
        prompt="What are 3 common reasons users abandon onboarding?",
        system="You are a product research expert.",
        temperature=0.7,
    )
    
    print(f"Model: {result['model']}")
    print(f"Provider: {result['provider']}")
    print(f"Cost: ${result['cost']:.4f}")
    print(f"Response: {result['content']}")
```

---

## 🏃 **Quick Start Commands**

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Check database
python -c "import asyncio; from backend.src.database.session import check_db_connection; print(asyncio.run(check_db_connection()))"

# Run backend server
cd backend
uvicorn src.api.main:app --reload

# Run tests (when available)
pytest tests/

# Reset database (⚠️ deletes all data)
python -m src.database.session --reset
```

---

## 📚 **Project Structure**

```
agentic-research-ai/
├── backend/
│   ├── src/
│   │   ├── core/
│   │   │   ├── config.py          ✅ Settings & constants
│   │   │   ├── ai_manager.py      ✅ Multi-model LLM manager
│   │   │   ├── react_engine.py    🚧 ReAct loop (Next)
│   │   │   └── goal_parser.py     🚧 NL → Mission (Next)
│   │   ├── database/
│   │   │   ├── models.py          ✅ SQLAlchemy models
│   │   │   └── session.py         ✅ Session management
│   │   ├── agents/
│   │   │   ├── base.py            🚧 Base agent class
│   │   │   ├── data/              🚧 Data collection agent
│   │   │   ├── prd/               🚧 PRD generation agent
│   │   │   └── ui_ux/             🚧 UI/UX design agent
│   │   ├── api/
│   │   │   ├── main.py            🚧 FastAPI app
│   │   │   ├── routes/            🚧 REST endpoints
│   │   │   └── websocket/         🚧 Real-time updates
│   │   ├── tools/                 🚧 Tool registry
│   │   └── observability/         🚧 Langfuse tracing
│   └── requirements.txt           🚧 Dependencies (Next)
├── frontend/                      🚧 Next.js app (Week 9-12)
├── tests/                         🚧 Test suite (Week 13-14)
├── docker/                        🚧 Deployment (Week 15)
├── docs/                          📝 Documentation
└── README.md                      ✅ This file
```

---

## 🎯 **Development Roadmap**

### **Phase 1: Core Engine** (Week 1-4) - In Progress

- ✅ Configuration system
- ✅ Database models
- ✅ AI manager (multi-model)
- 🚧 ReAct loop engine
- 🚧 Goal parser
- 🚧 Base agent class
- 🚧 Memory system (ChromaDB)

### **Phase 2: Agents** (Week 5-8)

- Data Agent (analytics, uploads, Kaggle)
- PRD Agent (research synthesis)
- UI/UX Designer Agent (wireframes, prototypes)
- Validator Agent (A/B tests, surveys)

### **Phase 3: API & UI** (Week 9-12)

- FastAPI backend with WebSocket
- Next.js frontend
- Real-time dashboard
- Checkpoint UI

### **Phase 4: Testing & Deployment** (Week 13-15)

- Unit tests
- Integration tests
- E2E tests
- Docker deployment
- CI/CD pipeline

---

## 🔧 **Technologies Used**

| Layer | Technology | Why |
|-------|------------|-----|
| **LLM** | Ollama (Llama 3.2, Qwen, DeepSeek) | Free, local, fast |
| **Backend** | FastAPI + SQLAlchemy 2.0 | Async, type-safe, modern |
| **Frontend** | Next.js 14 + Tailwind | SSR, real-time, professional |
| **Database** | SQLite → Supabase (PostgreSQL) | Start simple, scale later |
| **Memory** | ChromaDB + Redis | Semantic search + caching |
| **Tracing** | Langfuse | LLM observability |
| **Testing** | Pytest + Playwright | Unit + E2E coverage |

---

## 📊 **Key Features**

### **Dual Mode Architecture**

```python
# Demo Mode (No API keys)
settings.app_mode = "demo"
# → Agent generates synthetic realistic data
# → Perfect for testing, demos, development

# Real Mode (Connect to APIs)
settings.app_mode = "real"
# → PostHog, GA4 BigQuery, Kaggle
# → Real analytics, real participants
```

### **Multi-Model AI**

```python
# Automatic fallback chain:
# 1. Ollama local (free, fast) ✅
# 2. OpenRouter (pay-as-you-go)
# 3. Gemini (free tier)
# 4. OpenAI/Anthropic (backup)

result = await ai_manager.generate("Your prompt")
# → Uses first available provider
```

### **ReAct Loop** (Coming Next)

```python
# Think → Act → Observe → Learn
while not goal.is_complete():
    thought = await agent.think()
    action = await agent.act(thought)
    observation = await agent.observe(action)
    await agent.learn(observation)
```

---

## 🐛 **Troubleshooting**

### **Ollama Not Working**

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
# macOS: Open Ollama app
# Linux: sudo systemctl restart ollama

# Pull missing models
ollama pull llama3.2:3b
```

### **Database Issues**

```bash
# Reset database (⚠️ deletes data)
python -c "import asyncio; from backend.src.database.session import reset_db; asyncio.run(reset_db())"

# Check connection
python -c "import asyncio; from backend.src.database.session import check_db_connection; print(asyncio.run(check_db_connection()))"
```

### **Import Errors**

```bash
# Make sure you're in the right directory
cd agentic-research-ai/backend

# Run as module
python -m src.core.config  # Not: python src/core/config.py
```

---

## 🤝 **Contributing**

This is a professional build following industry best practices:
- Type hints everywhere
- Async-first
- Comprehensive error handling
- Full test coverage (coming)
- Documentation

---

## 📝 **License**

MIT License - Use freely for commercial/personal projects

---

## 🚀 **What's Next?**

### **CRITICAL DECISION NEEDED:**

I've built the core foundation (Week 1, Days 1-2). Before continuing, please answer:

### **1. What Should I Build Next?** (Pick ONE)

**Option A: Complete ReAct Loop** (2-3 hours)
- React engine with Think→Act→Observe→Learn
- Goal parser (NL → structured mission)
- Memory system (ChromaDB integration)
- **Result:** Agent can execute simple autonomous tasks

**Option B: Build Data Agent First** (2-3 hours)
- Data collection agent (analytics, CSV uploads)
- Tool registry framework
- Demo data generation with LLM
- **Result:** Can analyze data and generate insights

**Option C: Build FastAPI + Basic UI** (3-4 hours)
- REST API endpoints
- Simple HTML dashboard
- WebSocket real-time updates
- **Result:** Can interact with system via web UI

**Option D: Complete Week 1 Foundation** (4-5 hours)
- All of the above (ReAct + Agent + API)
- Fully working end-to-end MVP
- **Result:** Complete Week 1 milestone

### **2. Your Priorities:**

- Speed to demo? → Choose **Option B** (Data Agent)
- Want autonomy working? → Choose **Option A** (ReAct Loop)
- Need web interface? → Choose **Option C** (FastAPI + UI)
- Build it right? → Choose **Option D** (Complete Week 1)

### **3. Confirm Your Setup:**

- ✅ Ollama models installed? (llama3.2:3b, qwen2.5-coder:7b, etc.)
- ✅ Python 3.11+ with venv?
- ✅ Want SQLite (simple) or Supabase (scalable)?

**Tell me your choice and I'll continue building immediately!** 🚀

---

## 📧 **Contact & Support**

- Documentation: `docs/` folder
- Issues: Create detailed bug reports
- Questions: Check troubleshooting section first

---

**Built with ❤️ for Product Managers who want their research to happen autonomously.**
