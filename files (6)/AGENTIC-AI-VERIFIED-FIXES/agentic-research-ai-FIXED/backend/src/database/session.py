"""
Database Session Management
==========================

Async SQLAlchemy session factory and utilities:
- Connection pooling
- Session lifecycle management
- Database initialization
- Async context managers
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from sqlalchemy import text

from src.core.config import get_settings
from src.database.models import Base


settings = get_settings()


# =====================
# Engine Configuration
# =====================

def get_engine() -> AsyncEngine:
    """
    Create async database engine with appropriate configuration.
    
    Returns:
        AsyncEngine configured for SQLite or PostgreSQL
    """
    database_url = settings.get_active_database_url()
    
    # SQLite configuration
    if "sqlite" in database_url:
        # Ensure local SQLite directory exists.
        sqlite_path = database_url.replace("sqlite+aiosqlite:///", "", 1)
        if sqlite_path and not sqlite_path.startswith(":memory:"):
            Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)
        
        engine = create_async_engine(
            database_url,
            echo=settings.debug,
            poolclass=NullPool,  # SQLite doesn't support connection pooling
            connect_args={
                "check_same_thread": False,  # Allow multiple threads
                "timeout": 30,
            },
        )
    
    # PostgreSQL/Supabase configuration
    else:
        engine = create_async_engine(
            database_url,
            echo=settings.debug,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_pre_ping=True,  # Verify connections before use
        )
    
    return engine


# Create global engine instance
engine = get_engine()


# =====================
# Session Factory
# =====================

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autoflush=False,  # Manual flush control
    autocommit=False,  # Manual commit control
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.
    
    Usage:
        async with get_session() as session:
            result = await session.execute(select(ResearchGoal))
            goals = result.scalars().all()
    
    Yields:
        AsyncSession instance
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for FastAPI routes.
    
    Usage:
        @app.get("/goals")
        async def get_goals(session: AsyncSession = Depends(get_db)):
            result = await session.execute(select(ResearchGoal))
            return result.scalars().all()
    
    Yields:
        AsyncSession instance
    """
    async with get_session() as session:
        yield session


# =====================
# Database Initialization
# =====================

async def init_db() -> None:
    """
    Initialize database: create all tables.
    
    Called on application startup.
    """
    async with engine.begin() as conn:
        # Create all tables defined in models.py
        await conn.run_sync(Base.metadata.create_all)
    
    print(f"Database initialized: {settings.get_active_database_url()}")


async def drop_db() -> None:
    """
    Drop all database tables.
    
    ⚠️  Use with caution - this deletes all data!
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    print("Warning: database tables dropped")


async def reset_db() -> None:
    """
    Reset database: drop all tables and recreate.
    
    ⚠️  Use with caution - this deletes all data!
    """
    await drop_db()
    await init_db()
    print("Database reset complete")


# =====================
# Health Check
# =====================

async def check_db_connection() -> bool:
    """
    Check if database connection is healthy.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        async with get_session() as session:
            # Simple query to test connection
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


# =====================
# Utility Functions
# =====================

async def execute_raw_sql(sql: str) -> None:
    """
    Execute raw SQL query (for migrations, maintenance).
    
    Args:
        sql: SQL query string
    """
    async with engine.begin() as conn:
        await conn.execute(text(sql))


async def get_table_count(table_name: str) -> int:
    """
    Get row count for a specific table.
    
    Args:
        table_name: Name of the table
        
    Returns:
        int: Number of rows
    """
    async with get_session() as session:
        result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        count = result.scalar_one()
        return count


# =====================
# Context Manager for Transactions
# =====================

class Transaction:
    """
    Context manager for explicit transaction control.
    
    Usage:
        async with Transaction() as session:
            goal = ResearchGoal(description="Test")
            session.add(goal)
            # Automatic commit on success, rollback on exception
    """
    
    def __init__(self):
        self.session: Optional[AsyncSession] = None
    
    async def __aenter__(self) -> AsyncSession:
        self.session = AsyncSessionLocal()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Exception occurred, rollback
            await self.session.rollback()
        else:
            # Success, commit
            await self.session.commit()
        
        await self.session.close()


# =====================
# Session Cleanup
# =====================

async def close_db() -> None:
    """
    Close database engine and all connections.
    
    Called on application shutdown.
    """
    await engine.dispose()
    print("Database connections closed")


# =====================
# Migration Helper (For Alembic)
# =====================

def get_sync_engine():
    """
    Get synchronous engine for Alembic migrations.
    
    Alembic doesn't support async engines, so we provide sync version.
    """
    from sqlalchemy import create_engine
    
    sync_url = settings.database_url_sync
    
    if "sqlite" in sync_url:
        return create_engine(
            sync_url,
            echo=settings.debug,
            connect_args={"check_same_thread": False},
        )
    else:
        # Convert async PostgreSQL URL to sync
        sync_url = sync_url.replace("+asyncpg", "")
        return create_engine(
            sync_url,
            echo=settings.debug,
            pool_pre_ping=True,
        )


# =====================
# Export for convenience
# =====================

__all__ = [
    "engine",
    "AsyncSessionLocal",
    "get_session",
    "get_db",
    "init_db",
    "drop_db",
    "reset_db",
    "check_db_connection",
    "close_db",
    "Transaction",
]
