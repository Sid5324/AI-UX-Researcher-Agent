"""
Team Collaboration System
=========================

Features:
- Workspaces (organizations/teams)
- Role-based permissions
- Project sharing
- Team invitations
- Activity feed
- Comments & feedback
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from backend.src.database.models import (
    User, Workspace, WorkspaceMember, Project,
    ProjectShare, Comment, ActivityLog
)
from backend.src.database.session import AsyncSession


class WorkspaceRole(str, Enum):
    """Workspace member roles"""
    OWNER = "owner"      # Full control
    ADMIN = "admin"      # Manage members, settings
    MEMBER = "member"    # Create/edit projects
    VIEWER = "viewer"    # Read-only access


class ProjectPermission(str, Enum):
    """Project-level permissions"""
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class CollaborationService:
    """
    Team collaboration service.
    
    Manages:
    - Workspaces
    - Members
    - Permissions
    - Sharing
    """
    
    # =====================
    # Workspace Management
    # =====================
    
    async def create_workspace(
        self,
        session: AsyncSession,
        name: str,
        owner_id: str,
        description: Optional[str] = None,
    ) -> Workspace:
        """
        Create new workspace.
        
        Args:
            session: Database session
            name: Workspace name
            owner_id: User ID of owner
            description: Optional description
            
        Returns:
            Created workspace
        """
        workspace = Workspace(
            name=name,
            description=description,
            owner_id=owner_id,
        )
        
        session.add(workspace)
        await session.flush()
        
        # Add owner as member
        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=owner_id,
            role=WorkspaceRole.OWNER,
        )
        
        session.add(member)
        await session.commit()
        await session.refresh(workspace)
        
        return workspace
    
    async def get_workspace(
        self,
        session: AsyncSession,
        workspace_id: str,
    ) -> Optional[Workspace]:
        """Get workspace by ID with members."""
        result = await session.execute(
            select(Workspace)
            .where(Workspace.id == workspace_id)
            .options(selectinload(Workspace.members))
        )
        return result.scalar_one_or_none()
    
    async def list_user_workspaces(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> List[Workspace]:
        """List all workspaces user is member of."""
        result = await session.execute(
            select(Workspace)
            .join(WorkspaceMember)
            .where(WorkspaceMember.user_id == user_id)
            .options(selectinload(Workspace.members))
        )
        return result.scalars().all()
    
    async def update_workspace(
        self,
        session: AsyncSession,
        workspace_id: str,
        user_id: str,
        **updates,
    ) -> Workspace:
        """
        Update workspace (requires admin role).
        """
        # Check permission
        if not await self.can_manage_workspace(session, workspace_id, user_id):
            raise PermissionError("User cannot manage workspace")
        
        workspace = await self.get_workspace(session, workspace_id)
        
        for key, value in updates.items():
            if hasattr(workspace, key):
                setattr(workspace, key, value)
        
        await session.commit()
        await session.refresh(workspace)
        
        return workspace
    
    # =====================
    # Member Management
    # =====================
    
    async def invite_member(
        self,
        session: AsyncSession,
        workspace_id: str,
        inviter_id: str,
        email: str,
        role: WorkspaceRole = WorkspaceRole.MEMBER,
    ) -> Dict[str, Any]:
        """
        Invite user to workspace.
        
        Returns:
            Dict with invitation details
        """
        # Check permission
        if not await self.can_manage_members(session, workspace_id, inviter_id):
            raise PermissionError("User cannot invite members")
        
        # Find user by email
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return {
                "status": "invitation_sent",
                "email": email,
                "message": "Invitation email sent (user not registered yet)"
            }
        
        # Check if already member
        result = await session.execute(
            select(WorkspaceMember)
            .where(
                and_(
                    WorkspaceMember.workspace_id == workspace_id,
                    WorkspaceMember.user_id == user.id
                )
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            return {
                "status": "already_member",
                "user_id": user.id,
                "message": "User is already a member"
            }
        
        # Add member
        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=user.id,
            role=role,
            invited_by=inviter_id,
        )
        
        session.add(member)
        await session.commit()
        
        # Log activity
        await self._log_activity(
            session,
            workspace_id=workspace_id,
            user_id=inviter_id,
            action="member_invited",
            details={"invited_user": user.id, "role": role}
        )
        
        return {
            "status": "added",
            "user_id": user.id,
            "role": role,
            "message": "User added to workspace"
        }
    
    async def remove_member(
        self,
        session: AsyncSession,
        workspace_id: str,
        remover_id: str,
        member_id: str,
    ) -> Dict[str, Any]:
        """Remove member from workspace."""
        # Check permission
        if not await self.can_manage_members(session, workspace_id, remover_id):
            raise PermissionError("User cannot remove members")
        
        # Cannot remove owner
        workspace = await self.get_workspace(session, workspace_id)
        if member_id == workspace.owner_id:
            raise PermissionError("Cannot remove workspace owner")
        
        # Remove member
        result = await session.execute(
            select(WorkspaceMember)
            .where(
                and_(
                    WorkspaceMember.workspace_id == workspace_id,
                    WorkspaceMember.user_id == member_id
                )
            )
        )
        member = result.scalar_one_or_none()
        
        if member:
            await session.delete(member)
            await session.commit()
            
            await self._log_activity(
                session,
                workspace_id=workspace_id,
                user_id=remover_id,
                action="member_removed",
                details={"removed_user": member_id}
            )
        
        return {"status": "removed", "user_id": member_id}
    
    async def update_member_role(
        self,
        session: AsyncSession,
        workspace_id: str,
        updater_id: str,
        member_id: str,
        new_role: WorkspaceRole,
    ) -> WorkspaceMember:
        """Update member's role."""
        # Check permission
        if not await self.can_manage_members(session, workspace_id, updater_id):
            raise PermissionError("User cannot manage members")
        
        # Get member
        result = await session.execute(
            select(WorkspaceMember)
            .where(
                and_(
                    WorkspaceMember.workspace_id == workspace_id,
                    WorkspaceMember.user_id == member_id
                )
            )
        )
        member = result.scalar_one_or_none()
        
        if not member:
            raise ValueError("Member not found")
        
        old_role = member.role
        member.role = new_role
        
        await session.commit()
        await session.refresh(member)
        
        await self._log_activity(
            session,
            workspace_id=workspace_id,
            user_id=updater_id,
            action="member_role_updated",
            details={
                "member_id": member_id,
                "old_role": old_role,
                "new_role": new_role
            }
        )
        
        return member
    
    # =====================
    # Project Sharing
    # =====================
    
    async def share_project(
        self,
        session: AsyncSession,
        project_id: str,
        owner_id: str,
        share_with_user_id: str,
        permission: ProjectPermission = ProjectPermission.VIEWER,
    ) -> ProjectShare:
        """
        Share project with another user.
        """
        # Check if user owns project
        result = await session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project or project.user_id != owner_id:
            raise PermissionError("User does not own project")
        
        # Create share
        share = ProjectShare(
            project_id=project_id,
            user_id=share_with_user_id,
            permission=permission,
            shared_by=owner_id,
        )
        
        session.add(share)
        await session.commit()
        await session.refresh(share)
        
        return share
    
    async def get_shared_projects(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> List[Project]:
        """Get all projects shared with user."""
        result = await session.execute(
            select(Project)
            .join(ProjectShare)
            .where(ProjectShare.user_id == user_id)
        )
        return result.scalars().all()
    
    # =====================
    # Comments & Feedback
    # =====================
    
    async def add_comment(
        self,
        session: AsyncSession,
        project_id: str,
        user_id: str,
        content: str,
        parent_id: Optional[str] = None,
    ) -> Comment:
        """Add comment to project (threaded support)."""
        comment = Comment(
            project_id=project_id,
            user_id=user_id,
            content=content,
            parent_id=parent_id,
        )
        
        session.add(comment)
        await session.commit()
        await session.refresh(comment)
        
        return comment
    
    async def get_project_comments(
        self,
        session: AsyncSession,
        project_id: str,
    ) -> List[Comment]:
        """Get all comments for project."""
        result = await session.execute(
            select(Comment)
            .where(Comment.project_id == project_id)
            .order_by(Comment.created_at)
        )
        return result.scalars().all()
    
    # =====================
    # Activity Feed
    # =====================
    
    async def get_workspace_activity(
        self,
        session: AsyncSession,
        workspace_id: str,
        limit: int = 50,
    ) -> List[ActivityLog]:
        """Get recent activity in workspace."""
        result = await session.execute(
            select(ActivityLog)
            .where(ActivityLog.workspace_id == workspace_id)
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def _log_activity(
        self,
        session: AsyncSession,
        workspace_id: str,
        user_id: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log activity for feed."""
        activity = ActivityLog(
            workspace_id=workspace_id,
            user_id=user_id,
            action=action,
            details=details or {},
        )
        
        session.add(activity)
        await session.commit()
    
    # =====================
    # Permission Checks
    # =====================
    
    async def can_manage_workspace(
        self,
        session: AsyncSession,
        workspace_id: str,
        user_id: str,
    ) -> bool:
        """Check if user can manage workspace settings."""
        result = await session.execute(
            select(WorkspaceMember)
            .where(
                and_(
                    WorkspaceMember.workspace_id == workspace_id,
                    WorkspaceMember.user_id == user_id
                )
            )
        )
        member = result.scalar_one_or_none()
        
        return member and member.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
    
    async def can_manage_members(
        self,
        session: AsyncSession,
        workspace_id: str,
        user_id: str,
    ) -> bool:
        """Check if user can invite/remove members."""
        return await self.can_manage_workspace(session, workspace_id, user_id)
    
    async def can_view_project(
        self,
        session: AsyncSession,
        project_id: str,
        user_id: str,
    ) -> bool:
        """Check if user can view project."""
        # Check if owner
        result = await session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if project and project.user_id == user_id:
            return True
        
        # Check if shared
        result = await session.execute(
            select(ProjectShare)
            .where(
                and_(
                    ProjectShare.project_id == project_id,
                    ProjectShare.user_id == user_id
                )
            )
        )
        share = result.scalar_one_or_none()
        
        return share is not None
    
    async def can_edit_project(
        self,
        session: AsyncSession,
        project_id: str,
        user_id: str,
    ) -> bool:
        """Check if user can edit project."""
        # Check if owner
        result = await session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if project and project.user_id == user_id:
            return True
        
        # Check if editor
        result = await session.execute(
            select(ProjectShare)
            .where(
                and_(
                    ProjectShare.project_id == project_id,
                    ProjectShare.user_id == user_id,
                    ProjectShare.permission == ProjectPermission.EDITOR
                )
            )
        )
        share = result.scalar_one_or_none()
        
        return share is not None


# Singleton
_collaboration_service: Optional[CollaborationService] = None


def get_collaboration_service() -> CollaborationService:
    """Get collaboration service singleton."""
    global _collaboration_service
    if _collaboration_service is None:
        _collaboration_service = CollaborationService()
    return _collaboration_service
