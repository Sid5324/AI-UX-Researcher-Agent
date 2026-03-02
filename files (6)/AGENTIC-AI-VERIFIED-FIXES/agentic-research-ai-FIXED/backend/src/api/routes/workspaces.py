"""
Workspace/Collaboration API Routes
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from src.auth.service import get_current_user
from src.database.session import get_db

collaboration_router = APIRouter(prefix="/workspaces", tags=["collaboration"])


class CreateWorkspaceRequest(BaseModel):
    name: str
    description: Optional[str] = None


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: str = "member"


def _workspace_to_dict(workspace) -> dict:
    return {
        "id": workspace.id,
        "name": workspace.name,
        "description": workspace.description,
        "owner_id": workspace.owner_id,
        "created_at": workspace.created_at.isoformat() if workspace.created_at else None,
        "updated_at": workspace.updated_at.isoformat() if workspace.updated_at else None,
    }


@collaboration_router.post("/")
async def create_workspace(
    request: CreateWorkspaceRequest,
    user = Depends(get_current_user),
    session = Depends(get_db),
):
    """Create new workspace."""
    from src.collaboration.service import get_collaboration_service
    
    collab = get_collaboration_service()
    workspace = await collab.create_workspace(
        session,
        name=request.name,
        owner_id=user.id,
        description=request.description,
    )
    
    return _workspace_to_dict(workspace)


@collaboration_router.get("/")
async def list_workspaces(
    user = Depends(get_current_user),
    session = Depends(get_db),
):
    """List user's workspaces."""
    from src.collaboration.service import get_collaboration_service
    
    collab = get_collaboration_service()
    workspaces = await collab.list_user_workspaces(session, user.id)
    
    return [_workspace_to_dict(w) for w in workspaces]


@collaboration_router.post("/{workspace_id}/members")
async def invite_member(
    workspace_id: str,
    request: InviteMemberRequest,
    user = Depends(get_current_user),
    session = Depends(get_db),
):
    """Invite member to workspace."""
    from src.collaboration.service import get_collaboration_service
    
    collab = get_collaboration_service()
    result = await collab.invite_member(
        session,
        workspace_id=workspace_id,
        inviter_id=user.id,
        email=request.email,
        role=request.role,
    )
    
    return result


# =================================================================
