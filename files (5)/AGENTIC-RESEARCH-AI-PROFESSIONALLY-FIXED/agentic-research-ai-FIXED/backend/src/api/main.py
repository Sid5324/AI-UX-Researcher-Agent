"""
FastAPI Main Application
========================

REST API + WebSocket for Agentic Research AI

Endpoints:
- POST /goals - Create research goal
- GET /goals - List goals
- GET /goals/{id} - Get goal status
- POST /goals/{id}/approve - Approve checkpoint
- WS /ws/{goal_id} - Real-time updates
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.core.config import get_settings
from src.database.session import (
    get_db,
    init_db,
    close_db,
    check_db_connection,
    AsyncSession,
)
from src.database.models import ResearchGoal, AgentState, Checkpoint
from src.core.goal_parser import parse_goal
from src.agents.data.agent import DataAgent
from src.core.react_engine import run_react_loop
from src.core.ai_manager import get_ai_manager
from src.tools.registry import list_available_tools
from src.core.memory_system import get_memory_manager

from sqlalchemy import select


settings = get_settings()
ai_manager = get_ai_manager()
memory_manager = get_memory_manager()


# =====================
# Lifespan Context
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""
    # Startup
    print(f"🚀 Starting {settings.app_name}")
    print(f"📊 Mode: {settings.app_mode}")
    print(f"🤖 Primary LLM: {settings.ollama_model}")
    
    # Initialize database
    await init_db()
    
    # Check AI availability
    if await ai_manager.check_ollama_health():
        print("✅ Ollama connected")
    else:
        print("⚠️  Ollama not available - will use cloud APIs")
    
    # Check memory system
    stats = memory_manager.get_stats()
    print(f"💾 Memory: {stats['insights_count']} insights, {stats['skills_count']} skills")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    await close_db()


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title=settings.app_name,
    description="Autonomous AI agent for product research",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================
# Request/Response Models
# =====================

class CreateGoalRequest(BaseModel):
    """Request to create a new research goal"""
    description: str = Field(..., min_length=10, description="Goal description")
    budget_usd: Optional[float] = Field(None, ge=0, description="Budget in USD")
    timeline_days: Optional[int] = Field(None, ge=1, description="Timeline in days")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class GoalResponse(BaseModel):
    """Response with goal information"""
    id: str
    description: str
    status: str
    progress_percent: float
    mode: str
    current_agent: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


class CheckpointApprovalRequest(BaseModel):
    """Request to approve a checkpoint"""
    decision: str = Field(..., description="approved|rejected|modified")
    feedback: Optional[str] = Field(None, description="User feedback")


# =====================
# Health & Info Endpoints
# =====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "mode": settings.app_mode,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_healthy = await check_db_connection()
    ollama_healthy = await ai_manager.check_ollama_health()
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "database": "connected" if db_healthy else "disconnected",
        "ai": "connected" if ollama_healthy else "disconnected",
        "mode": settings.app_mode,
    }


@app.get("/info")
async def system_info():
    """Get system information"""
    models = await ai_manager.get_available_models()
    tools = list_available_tools()
    memory_stats = memory_manager.get_stats()
    
    return {
        "app_name": settings.app_name,
        "mode": settings.app_mode,
        "ai_models": models,
        "tools_available": len(tools),
        "tools": tools,
        "memory": memory_stats,
    }


# =====================
# Goal Management Endpoints
# =====================

@app.post("/goals", response_model=GoalResponse, status_code=201)
async def create_goal(
    request: CreateGoalRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    Create a new research goal.
    
    This will:
    1. Parse the goal description
    2. Create database record
    3. Start agent execution asynchronously
    """
    # Parse goal
    parsed = await parse_goal(request.description)
    
    # Create goal in database
    goal = ResearchGoal(
        description=request.description,
        mode=settings.app_mode,
        budget_usd=request.budget_usd or parsed.estimated_cost_usd,
        timeline_days=request.timeline_days or parsed.estimated_duration_days,
        metadata=request.metadata,
        status="pending",
    )
    
    session.add(goal)
    await session.commit()
    await session.refresh(goal)
    
    # Start agent execution in background
    asyncio.create_task(execute_goal(goal.id))
    
    return GoalResponse(
        id=goal.id,
        description=goal.description,
        status=goal.status,
        progress_percent=goal.progress_percent,
        mode=goal.mode,
        current_agent=goal.current_agent,
        created_at=goal.created_at.isoformat(),
    )


@app.get("/goals", response_model=list[GoalResponse])
async def list_goals(
    skip: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_db),
):
    """List all research goals"""
    result = await session.execute(
        select(ResearchGoal)
        .order_by(ResearchGoal.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    goals = result.scalars().all()
    
    return [
        GoalResponse(
            id=g.id,
            description=g.description,
            status=g.status,
            progress_percent=g.progress_percent,
            mode=g.mode,
            current_agent=g.current_agent,
            created_at=g.created_at.isoformat(),
        )
        for g in goals
    ]


@app.get("/goals/{goal_id}", response_model=Dict[str, Any])
async def get_goal(
    goal_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Get detailed goal information"""
    result = await session.execute(
        select(ResearchGoal).where(ResearchGoal.id == goal_id)
    )
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Get agent states
    result = await session.execute(
        select(AgentState).where(AgentState.goal_id == goal_id)
    )
    agents = result.scalars().all()
    
    # Get checkpoints
    result = await session.execute(
        select(Checkpoint).where(Checkpoint.goal_id == goal_id)
    )
    checkpoints = result.scalars().all()
    
    return {
        "goal": {
            "id": goal.id,
            "description": goal.description,
            "status": goal.status,
            "progress_percent": goal.progress_percent,
            "mode": goal.mode,
            "current_agent": goal.current_agent,
            "budget_usd": goal.budget_usd,
            "budget_spent": goal.budget_spent,
            "findings": goal.findings,
            "final_output": goal.final_output,
            "created_at": goal.created_at.isoformat(),
        },
        "agents": [
            {
                "name": a.agent_name,
                "status": a.status,
                "current_step": a.current_step,
                "duration_seconds": a.duration_seconds,
            }
            for a in agents
        ],
        "checkpoints": [
            {
                "id": c.id,
                "type": c.checkpoint_type,
                "title": c.title,
                "status": c.status,
                "created_at": c.created_at.isoformat(),
            }
            for c in checkpoints
        ],
    }


@app.post("/goals/{goal_id}/approve")
async def approve_checkpoint(
    goal_id: str,
    request: CheckpointApprovalRequest,
    session: AsyncSession = Depends(get_db),
):
    """Approve or reject a checkpoint"""
    # Get pending checkpoint
    result = await session.execute(
        select(Checkpoint)
        .where(Checkpoint.goal_id == goal_id)
        .where(Checkpoint.status == "waiting")
        .order_by(Checkpoint.created_at.desc())
    )
    checkpoint = result.scalar_one_or_none()
    
    if not checkpoint:
        raise HTTPException(status_code=404, detail="No pending checkpoint found")
    
    # Update checkpoint
    checkpoint.status = request.decision
    checkpoint.user_decision = request.feedback
    checkpoint.responded_at = asyncio.get_event_loop().time()
    
    # Resume goal execution
    result = await session.execute(
        select(ResearchGoal).where(ResearchGoal.id == goal_id)
    )
    goal = result.scalar_one()
    goal.status = "running"
    
    await session.commit()
    
    # Resume agent execution in background
    asyncio.create_task(execute_goal(goal_id))
    
    return {"status": "checkpoint_approved", "decision": request.decision}


# =====================
# Background Execution
# =====================

async def execute_goal(goal_id: str):
    """
    Execute goal in background.
    
    Uses multi-agent orchestrator for full workflow.
    """
    from src.database.session import get_session
    from src.core.orchestrator import orchestrate_agents
    
    async with get_session() as session:
        # Get goal
        result = await session.execute(
            select(ResearchGoal).where(ResearchGoal.id == goal_id)
        )
        goal = result.scalar_one_or_none()
        
        if not goal or goal.status not in ["pending", "running"]:
            return
        
        # Mark as running
        goal.status = "running"
        await session.commit()
        
        try:
            # Parse goal to determine agents needed
            parsed = await parse_goal(goal.description)
            
            # Use orchestrator for multi-agent execution
            result = await orchestrate_agents(session, goal, parsed)
            
            if result["success"]:
                goal.status = "completed"
                goal.progress_percent = 100.0
            else:
                goal.status = "failed"
                goal.error_message = result.get("error")
            
            await session.commit()
            
        except Exception as e:
            goal.status = "failed"
            goal.error_message = str(e)
            await session.commit()


# =====================
# WebSocket for Real-Time Updates
# =====================

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, list[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, goal_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        if goal_id not in self.active_connections:
            self.active_connections[goal_id] = []
        self.active_connections[goal_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, goal_id: str):
        """Remove WebSocket connection"""
        if goal_id in self.active_connections:
            self.active_connections[goal_id].remove(websocket)
    
    async def send_update(self, goal_id: str, message: dict):
        """Send update to all connections for a goal"""
        if goal_id in self.active_connections:
            for connection in self.active_connections[goal_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass


manager = ConnectionManager()


@app.websocket("/ws/{goal_id}")
async def websocket_endpoint(websocket: WebSocket, goal_id: str):
    """
    WebSocket for real-time goal updates.
    
    Sends progress updates as agent executes.
    """
    await manager.connect(websocket, goal_id)
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "goal_id": goal_id,
            "message": "Connected to goal updates",
        })
        
        # Keep connection alive and send updates
        while True:
            # Wait for messages (ping/pong)
            data = await websocket.receive_text()
            
            # Echo back
            await websocket.send_json({
                "type": "pong",
                "received": data,
            })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, goal_id)


# =====================
# Error Handlers
# =====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


# =====================
# Run Server
# =====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        workers=settings.api_workers,
    )

# =====================
# NEW ROUTE INTEGRATIONS
# =====================

try:
    from src.api.routes.auth import auth_router
    from src.api.routes.workspaces import collaboration_router  
    from src.api.routes.upload import upload_router
    
    app.include_router(auth_router)
    app.include_router(collaboration_router)
    app.include_router(upload_router)
    
    print("✅ Auth, Collaboration, and Upload routes registered!")
except Exception as e:
    print(f"⚠️  Route registration error (optional): {e}")

