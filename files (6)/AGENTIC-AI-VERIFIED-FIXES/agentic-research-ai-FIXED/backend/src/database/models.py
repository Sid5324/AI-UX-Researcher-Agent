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

from src.core.config import get_settings


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
        default=lambda: get_settings().app_mode,
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
        nullable=True
    )
    progress_percent: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )
    
    # Project Context
    workspace_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("workspaces.id"),
        nullable=True
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=True
    )
    
    # Resources
    budget_usd: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    budget_spent: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )
    timeline_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    meta_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    
    # Results
    findings: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    final_output: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        default=utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=utcnow,
        onupdate=utcnow,
        nullable=False
    )
    
    # Relationships
    agents: Mapped[List["AgentState"]] = relationship(
        back_populates="goal",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    checkpoints: Mapped[List["Checkpoint"]] = relationship(
        back_populates="goal",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    workspace: Mapped[Optional["Workspace"]] = relationship(
        back_populates="goals"
    )


class AgentState(Base):
    """
    Tracks state and progress for a single agent working on a goal.
    """
    __tablename__ = "agent_states"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )
    goal_id: Mapped[str] = mapped_column(
        ForeignKey("research_goals.id", ondelete="CASCADE"),
        nullable=False
    )
    agent_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending"
    )
    current_step: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    steps_completed: Mapped[int] = mapped_column(
        Integer,
        default=0
    )
    
    # Metrics
    llm_calls: Mapped[int] = mapped_column(
        Integer,
        default=0
    )
    tool_calls: Mapped[int] = mapped_column(
        Integer,
        default=0
    )
    cost_usd: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )
    duration_seconds: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )
    
    # Results
    output: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True
    )
    
    # Relationships
    goal: Mapped["ResearchGoal"] = relationship(
        back_populates="agents"
    )


class Checkpoint(Base):
    """
    A point in the execution where the agent requires user validation or approval.
    """
    __tablename__ = "checkpoints"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )
    goal_id: Mapped[str] = mapped_column(
        ForeignKey("research_goals.id", ondelete="CASCADE"),
        nullable=False
    )
    agent_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    
    # Details
    checkpoint_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="approval, decision, budget_warning, notification"
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    options: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True
    )
    agent_reasoning: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # State
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        comment="pending → approved → rejected → ignored"
    )
    response_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        default=utcnow,
        nullable=False
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True
    )
    
    # Relationships
    goal: Mapped["ResearchGoal"] = relationship(
        back_populates="checkpoints"
    )


# =====================
# Memory Models
# =====================

class MemoryEntry(Base):
    """
    Short-term working memory stored in database.
    """
    __tablename__ = "memory_entries"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )
    goal_id: Mapped[str] = mapped_column(
        ForeignKey("research_goals.id", ondelete="CASCADE"),
        nullable=False
    )
    agent_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    
    key: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    value: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        default=utcnow,
        nullable=False
    )


class Insight(Base):
    """
    Long-term cross-project insights stored in vector memory.
    """
    __tablename__ = "insights"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    insight_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )
    
    # Metadata
    evidence: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict
    )
    tags: Mapped[List[str]] = mapped_column(
        JSON,
        default=list
    )
    effect_size: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    
    # Hierarchy
    parent_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("insights.id"),
        nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        default=utcnow,
        nullable=False
    )


# =====================
# Workflow Models
# =====================

class ToolExecution(Base):
    """
    Log of all tool executions for audit and cost tracking.
    """
    __tablename__ = "tool_executions"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )
    tool_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    tool_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    
    # Details
    goal_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("research_goals.id", ondelete="SET NULL"),
        nullable=True
    )
    agent_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    
    # Data
    input_params: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict
    )
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    
    # Performance
    status: Mapped[str] = mapped_column(
        String(20),
        default="success"
    )
    duration_seconds: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )
    cost_usd: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        default=utcnow,
        nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True
    )


# =====================
# User & Org Models
# =====================

class Workspace(Base):
    """
    Top-level organizational unit.
    """
    __tablename__ = "workspaces"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        default=utcnow,
        nullable=False
    )
    
    # Relationships
    goals: Mapped[List["ResearchGoal"]] = relationship(
        back_populates="workspace"
    )
    members: Mapped[List["User"]] = relationship(
        secondary="workspace_members",
        back_populates="workspaces"
    )


class User(Base):
    """
    User account for authentication and access control.
    """
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(50),
        default="user"
    )
    
    # State
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        default=utcnow,
        nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        nullable=True
    )
    
    # Relationships
    workspaces: Mapped[List["Workspace"]] = relationship(
        secondary="workspace_members",
        back_populates="members"
    )


class WorkspaceMember(Base):
    """
    Association table linking users to workspaces with roles.
    """
    __tablename__ = "workspace_members"
    
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    role: Mapped[str] = mapped_column(
        String(50),
        default="member"
    )
    
    # Timestamps
    joined_at: Mapped[datetime] = mapped_column(
        default=utcnow,
        nullable=False
    )
    
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),
    )
