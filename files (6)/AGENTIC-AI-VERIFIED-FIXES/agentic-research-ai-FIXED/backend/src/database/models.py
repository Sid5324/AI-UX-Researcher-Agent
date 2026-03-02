"""
Database Models
==============

SQLAlchemy 2.0 async models with:
- Mapped columns with type hints
- Relationships for goal → agents → checkpoints
- JSON fields for flexible data storage
- Timestamps and audit fields
"""

from datetime import datetime, UTC
from typing import Optional, Dict, Any, List
from uuid import uuid4, UUID

from sqlalchemy import String, Text, Float, Integer, Boolean, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


def utcnow() -> datetime:
    """Get current UTC time"""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


# =====================
# Core Research Models
# =====================

class ResearchGoal(Base):
    """
    Central entity tracking research projects from start to finish.
    
    One ResearchGoal has many AgentState, Checkpoint, and MemoryEntry records.
    """
    __tablename__ = "research_goals"
    
    # Primary Key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )
    
    # Goal Details
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="User's natural language goal"
    )
    mode: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="'real' or 'demo' mode"
    )
    
    # Status Tracking
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        comment="pending → running → checkpoint → completed/failed"
    )
    current_agent: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Which agent is currently executing"
    )
    progress_percent: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        comment="Completion percentage (0-100)"
    )
    
    # Budget & Constraints
    budget_usd: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Research budget in USD"
    )
    budget_spent: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        comment="Amount spent so far"
    )
    timeline_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Expected timeline in days"
    )
    
    # Results (Flexible JSON)
    findings: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Intermediate findings from agents"
    )
    final_output: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Complete deliverable (PRD, designs, etc.)"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if failed"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=utcnow,
        comment="When goal was created"
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
        comment="Last update time"
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="When agent execution started"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="When goal was completed/failed"
    )
    
    # User Context
    user_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="User identifier (future auth)"
    )
    meta_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional context (company, industry, etc.)"
    )
    
    # Relationships
    agent_states: Mapped[List["AgentState"]] = relationship(
        back_populates="goal",
        cascade="all, delete-orphan"
    )
    checkpoints: Mapped[List["Checkpoint"]] = relationship(
        back_populates="goal",
        cascade="all, delete-orphan"
    )
    memory_entries: Mapped[List["MemoryEntry"]] = relationship(
        back_populates="goal",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<ResearchGoal(id={self.id}, status={self.status}, progress={self.progress_percent}%)>"


class AgentState(Base):
    """
    Tracks individual agent executions within a research goal.
    Each agent run (Data, PRD, UI/UX) creates one AgentState record.
    """
    __tablename__ = "agent_states"
    
    # Primary Key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )
    
    # Foreign Key
    goal_id: Mapped[str] = mapped_column(
        ForeignKey("research_goals.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Agent Details
    agent_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Agent identifier (data_agent, prd_agent, etc.)"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        comment="pending → running → completed/failed"
    )
    
    # Execution Tracking
    current_step: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Current execution step"
    )
    steps_completed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Number of steps finished"
    )
    total_steps: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Total steps planned"
    )
    
    # ReAct Loop Tracking
    react_iteration: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Current ReAct loop iteration"
    )
    last_thought: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Last reasoning output (THINK step)"
    )
    last_action: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Last action taken (ACT step)"
    )
    last_observation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Last observation (OBSERVE step)"
    )
    
    # Results
    output: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Agent output data"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error if failed"
    )
    
    # Performance Metrics
    duration_seconds: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Execution time"
    )
    llm_calls: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Number of LLM API calls"
    )
    cost_usd: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        comment="Cost in USD"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=utcnow
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Relationships
    goal: Mapped["ResearchGoal"] = relationship(back_populates="agent_states")
    
    def __repr__(self) -> str:
        return f"<AgentState(id={self.id}, agent={self.agent_name}, status={self.status})>"


class Checkpoint(Base):
    """
    Stores human-in-the-loop approval points.
    Agent pauses and waits for user decision.
    """
    __tablename__ = "checkpoints"
    
    # Primary Key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )
    
    # Foreign Key
    goal_id: Mapped[str] = mapped_column(
        ForeignKey("research_goals.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Checkpoint Details
    checkpoint_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of checkpoint (solution_options, final_approval, etc.)"
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Short checkpoint title"
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full checkpoint description"
    )
    
    # Options Presented
    options: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Available options for user to choose"
    )
    recommended_option: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Agent's recommended choice"
    )
    
    # User Response
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="waiting",
        comment="waiting → approved/rejected/modified"
    )
    user_decision: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User's decision/feedback"
    )
    selected_option: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Which option user selected"
    )
    
    # Context
    agent_reasoning: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Agent's reasoning for this checkpoint"
    )
    evidence: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Supporting evidence/data"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=utcnow
    )
    responded_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="When user responded"
    )
    
    # Relationships
    goal: Mapped["ResearchGoal"] = relationship(back_populates="checkpoints")
    
    def __repr__(self) -> str:
        return f"<Checkpoint(id={self.id}, type={self.checkpoint_type}, status={self.status})>"


# =====================
# Memory System Models
# =====================

class MemoryEntry(Base):
    """
    Episodic memory: stores every thought, action, and observation.
    Used for full reasoning trail and learning.
    """
    __tablename__ = "memory_entries"
    
    # Primary Key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )
    
    # Foreign Key
    goal_id: Mapped[str] = mapped_column(
        ForeignKey("research_goals.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Memory Type
    memory_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="working/episodic/semantic/procedural"
    )
    event_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="think/act/observe/learn/user_input"
    )
    
    # Content
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Memory content (thought, action, observation)"
    )
    entry_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional context (agent, tool, cost, etc.)"
    )
    
    # Importance & Confidence
    importance: Mapped[str] = mapped_column(
        String(10),
        default="medium",
        comment="low/medium/high importance"
    )
    confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Confidence score (0-1)"
    )
    
    # Vector Embedding (for semantic search)
    embedding: Mapped[Optional[bytes]] = mapped_column(
        nullable=True,
        comment="Vector embedding as bytes (for ChromaDB sync)"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=utcnow
    )
    
    # Relationships
    goal: Mapped["ResearchGoal"] = relationship(back_populates="memory_entries")
    
    def __repr__(self) -> str:
        return f"<MemoryEntry(id={self.id}, type={self.event_type}, importance={self.importance})>"


class Insight(Base):
    """
    Semantic memory: validated insights that persist across projects.
    Research vault for compound learning.
    """
    __tablename__ = "insights"
    
    # Primary Key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )
    
    # Insight Details
    insight_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="user_behavior/pain_point/solution_pattern/metric_correlation"
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Insight description"
    )
    
    # Validation
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Confidence score (0-1)"
    )
    evidence: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="Supporting evidence (projects, methods, sample sizes)"
    )
    validation_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="a_b_test/interviews/surveys/analytics"
    )
    
    # Context & Applicability
    tags: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="Tags for categorization (onboarding, B2B_SaaS, etc.)"
    )
    applicable_contexts: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="Where this insight applies"
    )
    
    # Impact
    effect_size: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Measured impact (e.g., '+47% activation')"
    )
    
    # Usage Tracking
    times_applied: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="How many times this insight was used"
    )
    success_rate: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Success rate when applied (0-1)"
    )
    
    # Vector Embedding
    embedding: Mapped[Optional[bytes]] = mapped_column(
        nullable=True,
        comment="Vector embedding for semantic search"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=utcnow
    )
    last_validated: Mapped[datetime] = mapped_column(
        nullable=False,
        default=utcnow,
        comment="Last time insight was revalidated"
    )
    
    def __repr__(self) -> str:
        return f"<Insight(id={self.id}, type={self.insight_type}, confidence={self.confidence})>"


# =====================
# Tool Execution Tracking
# =====================

class ToolExecution(Base):
    """
    Tracks every tool execution for monitoring and debugging.
    """
    __tablename__ = "tool_executions"
    
    # Primary Key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )
    
    # Tool Details
    tool_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Name of tool executed"
    )
    tool_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="data/analytics/communication/creation"
    )
    
    # Execution Context
    goal_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="Associated research goal"
    )
    agent_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Which agent called this tool"
    )
    
    # Input/Output
    input_params: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="Tool input parameters"
    )
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Tool output data"
    )
    
    # Execution Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        comment="pending → success/failed"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Number of retries attempted"
    )
    
    # Performance
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    def __repr__(self) -> str:
        return f"<ToolExecution(id={self.id}, tool={self.tool_name}, status={self.status})>"


# =====================
# User Management
# =====================

class User(Base):
    """Application users (auth + collaboration)."""
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )
    
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    oauth_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    oauth_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    preferences: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="User preferences (autonomy level, notifications, etc.)"
    )
    plan: Mapped[str] = mapped_column(
        String(20),
        default="free",
        comment="free/pro/team"
    )
    
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    workspaces_owned: Mapped[List["Workspace"]] = relationship(
        back_populates="owner",
    )
    workspace_memberships: Mapped[List["WorkspaceMember"]] = relationship(back_populates="user")
    projects: Mapped[List["Project"]] = relationship(back_populates="owner")
    shared_projects: Mapped[List["ProjectShare"]] = relationship(
        back_populates="user",
    )
    comments: Mapped[List["Comment"]] = relationship(back_populates="user")
    activities: Mapped[List["ActivityLog"]] = relationship(back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


# =====================
# Collaboration Models
# =====================

class Workspace(Base):
    """Team workspace."""
    __tablename__ = "workspaces"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    settings: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)
    
    owner: Mapped["User"] = relationship(back_populates="workspaces_owned")
    members: Mapped[List["WorkspaceMember"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    projects: Mapped[List["Project"]] = relationship(back_populates="workspace")
    activity_logs: Mapped[List["ActivityLog"]] = relationship(back_populates="workspace")
    
    def __repr__(self) -> str:
        return f"<Workspace(id={self.id}, name={self.name})>"


class WorkspaceMember(Base):
    """User membership in a workspace."""
    __tablename__ = "workspace_members"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),)
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="member", nullable=False)
    invited_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    joined_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    
    workspace: Mapped["Workspace"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="workspace_memberships")
    
    def __repr__(self) -> str:
        return f"<WorkspaceMember(workspace={self.workspace_id}, user={self.user_id}, role={self.role})>"


class Project(Base):
    """Workspace project."""
    __tablename__ = "projects"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    workspace_id: Mapped[Optional[str]] = mapped_column(ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    goal_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    content: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)
    
    workspace: Mapped[Optional["Workspace"]] = relationship(back_populates="projects")
    owner: Mapped["User"] = relationship(back_populates="projects")
    shares: Mapped[List["ProjectShare"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    comments: Mapped[List["Comment"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Project(id={self.id}, title={self.title})>"


class ProjectShare(Base):
    """Project sharing permissions."""
    __tablename__ = "project_shares"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_user_share"),)
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    permission: Mapped[str] = mapped_column(String(20), default="viewer", nullable=False)
    shared_by: Mapped[str] = mapped_column(String(36), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    
    project: Mapped["Project"] = relationship(back_populates="shares")
    user: Mapped["User"] = relationship(back_populates="shared_projects")
    
    def __repr__(self) -> str:
        return f"<ProjectShare(project={self.project_id}, user={self.user_id}, permission={self.permission})>"


class Comment(Base):
    """Threaded project comments."""
    __tablename__ = "comments"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[Optional[str]] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow, onupdate=utcnow)
    
    project: Mapped["Project"] = relationship(back_populates="comments")
    user: Mapped["User"] = relationship(back_populates="comments")
    
    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, project={self.project_id})>"


class ActivityLog(Base):
    """Workspace activity feed entry."""
    __tablename__ = "activity_logs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utcnow)
    
    workspace: Mapped["Workspace"] = relationship(back_populates="activity_logs")
    user: Mapped["User"] = relationship(back_populates="activities")
    
    def __repr__(self) -> str:
        return f"<ActivityLog(id={self.id}, action={self.action})>"
