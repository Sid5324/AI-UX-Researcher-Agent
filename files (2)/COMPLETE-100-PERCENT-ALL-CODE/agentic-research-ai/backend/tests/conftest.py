"""
Test Configuration & Fixtures
==============================

Global test setup, fixtures, and utilities for pytest.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from backend.src.core.config import get_settings
from backend.src.database.session import get_session, AsyncSessionLocal
from backend.src.database.models import Base, User, ResearchGoal, Workspace
from backend.src.auth.service import AuthService


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Override settings for testing
settings = get_settings()
settings.database_url = TEST_DATABASE_URL
settings.app_mode = "demo"  # Use demo mode for tests


# =====================
# Event Loop Fixture
# =====================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =====================
# Database Fixtures
# =====================

@pytest_asyncio.fixture(scope="function")
async def test_db():
    """
    Create test database for each test.
    
    Database is created before test and dropped after.
    """
    # Create engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(test_db) -> AsyncGenerator[AsyncSession, None]:
    """
    Create database session for each test.
    
    Session is committed after test if successful, rolled back on error.
    """
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


# =====================
# User Fixtures
# =====================

@pytest_asyncio.fixture
async def test_user(session: AsyncSession) -> User:
    """Create test user."""
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash="$2b$12$test_hash",  # Mock hash
        role="user",
        email_verified=True,
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def test_admin(session: AsyncSession) -> User:
    """Create test admin user."""
    admin = User(
        email="admin@example.com",
        name="Admin User",
        password_hash="$2b$12$admin_hash",
        role="admin",
        email_verified=True,
    )
    
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    
    return admin


@pytest_asyncio.fixture
async def multiple_users(session: AsyncSession) -> list[User]:
    """Create multiple test users."""
    users = []
    
    for i in range(3):
        user = User(
            email=f"user{i}@example.com",
            name=f"User {i}",
            password_hash=f"$2b$12$hash_{i}",
            role="user",
            email_verified=True,
        )
        session.add(user)
        users.append(user)
    
    await session.commit()
    
    for user in users:
        await session.refresh(user)
    
    return users


# =====================
# Auth Fixtures
# =====================

@pytest.fixture
def auth_service() -> AuthService:
    """Create auth service instance."""
    return AuthService()


@pytest_asyncio.fixture
async def authenticated_user(session: AsyncSession, test_user: User, auth_service: AuthService):
    """Create authenticated user with tokens."""
    access_token = auth_service.create_access_token(
        user_id=test_user.id,
        email=test_user.email,
        role=test_user.role,
    )
    
    refresh_token = auth_service.create_refresh_token(test_user.id)
    
    return {
        "user": test_user,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


# =====================
# Workspace Fixtures
# =====================

@pytest_asyncio.fixture
async def test_workspace(session: AsyncSession, test_user: User) -> Workspace:
    """Create test workspace."""
    workspace = Workspace(
        name="Test Workspace",
        description="Test workspace description",
        owner_id=test_user.id,
    )
    
    session.add(workspace)
    await session.commit()
    await session.refresh(workspace)
    
    return workspace


# =====================
# Goal Fixtures
# =====================

@pytest_asyncio.fixture
async def test_goal(session: AsyncSession, test_user: User) -> ResearchGoal:
    """Create test research goal."""
    goal = ResearchGoal(
        description="Test research goal",
        mode="demo",
        user_id=test_user.id,
        status="pending",
        budget_usd=1000.0,
        timeline_days=7,
    )
    
    session.add(goal)
    await session.commit()
    await session.refresh(goal)
    
    return goal


@pytest_asyncio.fixture
async def completed_goal(session: AsyncSession, test_user: User) -> ResearchGoal:
    """Create completed research goal with results."""
    goal = ResearchGoal(
        description="Completed research goal",
        mode="demo",
        user_id=test_user.id,
        status="completed",
        progress_percent=100.0,
        budget_usd=1000.0,
        budget_spent=250.0,
        timeline_days=7,
        findings={
            "data_agent": {"insights": ["Finding 1", "Finding 2"]},
            "prd_agent": {"requirements": ["Req 1", "Req 2"]},
        },
        final_output={
            "summary": "Research completed successfully",
            "confidence": 0.95,
        }
    )
    
    session.add(goal)
    await session.commit()
    await session.refresh(goal)
    
    return goal


# =====================
# API Client Fixtures
# =====================

@pytest.fixture
def api_client():
    """Create FastAPI test client."""
    from fastapi.testclient import TestClient
    from backend.src.api.main import app
    
    return TestClient(app)


@pytest.fixture
def authenticated_client(api_client, authenticated_user):
    """Create authenticated API client."""
    token = authenticated_user["access_token"]
    api_client.headers = {
        **api_client.headers,
        "Authorization": f"Bearer {token}"
    }
    return api_client


# =====================
# Mock Fixtures
# =====================

@pytest.fixture
def mock_llm_response():
    """Mock LLM response."""
    return {
        "content": "This is a test response from the LLM.",
        "model": "test-model",
        "provider": "test-provider",
        "cost": 0.0,
        "tokens": {"prompt": 10, "completion": 20}
    }


@pytest.fixture
def mock_posthog_data():
    """Mock PostHog analytics data."""
    return {
        "success": True,
        "events": [
            {
                "event": "page_view",
                "timestamp": "2024-01-01T00:00:00Z",
                "properties": {"path": "/home"}
            },
            {
                "event": "button_click",
                "timestamp": "2024-01-01T00:01:00Z",
                "properties": {"button_id": "cta"}
            }
        ],
        "count": 2
    }


@pytest.fixture
def mock_kaggle_dataset():
    """Mock Kaggle dataset."""
    return {
        "ref": "user/dataset-name",
        "title": "Test Dataset",
        "size_mb": 45,
        "rows": 10000,
        "columns": 12,
    }


# =====================
# Time Travel Fixtures
# =====================

@pytest.fixture
def freeze_time():
    """Freeze time for testing."""
    from unittest.mock import patch
    from datetime import datetime
    
    frozen_time = datetime(2024, 1, 1, 12, 0, 0)
    
    with patch('backend.src.database.models.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = frozen_time
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        yield frozen_time


# =====================
# File Fixtures
# =====================

@pytest.fixture
def temp_csv_file(tmp_path):
    """Create temporary CSV file."""
    import csv
    
    csv_file = tmp_path / "test_data.csv"
    
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "value"])
        writer.writerow([1, "Item 1", 100])
        writer.writerow([2, "Item 2", 200])
        writer.writerow([3, "Item 3", 300])
    
    return csv_file


@pytest.fixture
def temp_json_file(tmp_path):
    """Create temporary JSON file."""
    import json
    
    json_file = tmp_path / "test_data.json"
    
    data = {
        "items": [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
        ]
    }
    
    with open(json_file, 'w') as f:
        json.dump(data, f)
    
    return json_file


# =====================
# Cleanup Fixtures
# =====================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test."""
    yield
    # Cleanup code runs after test
    # Clear caches, close connections, etc.
    pass


# =====================
# Test Utilities
# =====================

class TestHelpers:
    """Helper methods for tests."""
    
    @staticmethod
    async def create_test_user(session: AsyncSession, email: str, **kwargs) -> User:
        """Create a test user with custom attributes."""
        user = User(
            email=email,
            name=kwargs.get("name", "Test User"),
            password_hash=kwargs.get("password_hash", "$2b$12$test"),
            role=kwargs.get("role", "user"),
            email_verified=kwargs.get("email_verified", True),
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        return user
    
    @staticmethod
    async def create_test_goal(session: AsyncSession, user_id: str, **kwargs) -> ResearchGoal:
        """Create a test research goal."""
        goal = ResearchGoal(
            description=kwargs.get("description", "Test goal"),
            mode=kwargs.get("mode", "demo"),
            user_id=user_id,
            status=kwargs.get("status", "pending"),
            **kwargs
        )
        
        session.add(goal)
        await session.commit()
        await session.refresh(goal)
        
        return goal


@pytest.fixture
def test_helpers():
    """Provide test helper methods."""
    return TestHelpers


# =====================
# Markers
# =====================

# Custom pytest markers
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (>1 second)"
    )
    config.addinivalue_line(
        "markers", "requires_api: Tests requiring external APIs"
    )
