# 🤖 AI UX Researcher Agent

An intelligent multi-agent system for automated UX research and product development insights.

## 📋 Overview

This project is a comprehensive AI-powered research platform that leverages multiple specialized agents to conduct competitive analysis, data analysis, user interviews, and generate product requirements. Built with Python (FastAPI) backend and Next.js frontend.

## ✨ Features

- **Multi-Agent Architecture**: Specialized agents for different research tasks
  - 🔍 Competitor Analysis Agent
  - 📊 Data Analysis Agent
  - 🎤 Interview/Feedback Agent
  - 📝 PRD Generation Agent
  - 🎨 UI/UX Design Agent
  - ✅ Validation Agent

- **Modern Tech Stack**
  - Backend: FastAPI + SQLAlchemy + Pydantic
  - Frontend: Next.js + TypeScript + Tailwind CSS
  - AI Integration: Ollama support for local LLMs
  - Database: SQLite (configurable)

- **Research Tools**
  - Web scraping capabilities
  - Data connector integrations (GA4, BigQuery, Kaggle, PostHog)
  - Email and Slack notifications
  - Real-time collaboration features

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- Ollama (for local AI models)
- Git

### Backend Setup

```bash
# Navigate to backend directory
cd files\ (6)\AGENTIC-AI-VERIFIED-FIXES\agentic-research-ai-FIXED\backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend directory
cd files\ (6)\AGENTIC-AI-VERIFIED-FIXES\agentic-research-ai-FIXED\frontend-nextjs

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## 📁 Project Structure

```
AI UX Researcher Agent/
├── files (6)/                    # Main project files
│   └── AGENTIC-AI-VERIFIED-FIXES/
│       └── agentic-research-ai-FIXED/
│           ├── backend/          # FastAPI backend
│           │   ├── src/
│           │   │   ├── agents/   # AI agents
│           │   │   ├── api/      # API routes
│           │   │   ├── core/     # Core logic
│           │   │   ├── database/ # Database models
│           │   │   └── connectors/ # External integrations
│           │   └── tests/
│           └── frontend-nextjs/  # Next.js frontend
├── builderplan/                  # Project documentation & research
└── [other files]
```

## 🔧 Configuration

Create a `.env` file in the backend directory with the following variables:

```env
# Database
DATABASE_URL=sqlite:///./data/agentic_research.db

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=llama3.2

# API Settings
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Optional: External APIs
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Optional: OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_core.py
```

## 📚 Documentation

- [Project Plan](builderplan/projectplan.txt)
- [PRD Document](builderplan/PRD.txt)
- [Build Plan](builderplan/build%20plan.txt)
- [Research Documentation](builderplan/research/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with FastAPI and Next.js
- AI powered by Ollama
- Inspired by modern agentic AI architectures

---

**Note**: This is an active development project. Some features may be incomplete or subject to change.
