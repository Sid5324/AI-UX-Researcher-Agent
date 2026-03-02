"""
Authentication API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional
from src.auth.service import auth_service, get_current_user
from src.database.session import get_db

auth_router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@auth_router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, session = Depends(get_db)):
    """Register new user."""
    result = await auth_service.register_user(
        session,
        email=request.email,
        password=request.password,
        name=request.name,
    )
    return result


@auth_router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, session = Depends(get_db)):
    """Login user."""
    result = await auth_service.login(
        session,
        email=request.email,
        password=request.password,
    )
    return result


@auth_router.post("/refresh")
async def refresh_token(
    request: RefreshTokenRequest,
    session = Depends(get_db),
):
    """Refresh access token."""
    result = await auth_service.refresh_access_token(session, request.refresh_token)
    return result


@auth_router.get("/me")
async def get_current_user_info(user = Depends(get_current_user)):
    """Get current authenticated user."""
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
    }


@auth_router.post("/oauth/google")
async def oauth_google(google_token: str, session = Depends(get_db)):
    """Login with Google OAuth."""
    result = await auth_service.oauth_google(session, google_token)
    return result


# =================================================================
