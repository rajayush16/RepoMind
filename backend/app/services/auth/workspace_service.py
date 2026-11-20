import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "workspace"


async def _unique_slug(db: AsyncSession, base: str) -> str:
    slug = _slugify(base)
    candidate = slug
    suffix = 1
    while True:
        result = await db.execute(select(Workspace).where(Workspace.slug == candidate))
        if result.scalar_one_or_none() is None:
            return candidate
        suffix += 1
        candidate = f"{slug}-{suffix}"


async def create_personal_workspace(
    db: AsyncSession, user_id: uuid.UUID, display_name: str
) -> Workspace:
    slug = await _unique_slug(db, display_name)
    workspace = Workspace(name=f"{display_name}'s Workspace", slug=slug, is_personal=True)
    db.add(workspace)
    await db.flush()

    membership = WorkspaceMember(
        workspace_id=workspace.id, user_id=user_id, role=WorkspaceRole.OWNER
    )
    db.add(membership)
    await db.flush()
    return workspace


async def get_personal_workspace_for_user(
    db: AsyncSession, user_id: uuid.UUID
) -> Workspace | None:
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user_id, Workspace.is_personal.is_(True))
    )
    return result.scalars().first()


async def is_workspace_member(db: AsyncSession, workspace_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id
        )
    )
    return result.scalar_one_or_none() is not None
