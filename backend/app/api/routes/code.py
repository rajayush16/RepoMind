import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_workspace
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.indexing import CodeSymbol, IndexedFile
from app.models.repository import Repository
from app.models.workspace import Workspace
from app.schemas.code import FileContentOut, FileEntry, SymbolOut

router = APIRouter(prefix="/repositories/{repository_id}", tags=["code"])


async def _get_owned_repository(
    db: AsyncSession, workspace: Workspace, repository_id: uuid.UUID
) -> Repository:
    repository = await db.get(Repository, repository_id)
    if repository is None or repository.workspace_id != workspace.id:
        raise NotFoundError("Repository not found.")
    return repository


@router.get("/files", response_model=list[FileEntry])
async def list_files(
    repository_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> list[IndexedFile]:
    await _get_owned_repository(db, workspace, repository_id)

    result = await db.execute(
        select(IndexedFile)
        .where(IndexedFile.repository_id == repository_id)
        .order_by(IndexedFile.relative_path)
    )
    return list(result.scalars().all())


@router.get("/files/content", response_model=FileContentOut)
async def get_file_content(
    repository_id: uuid.UUID,
    path: str = Query(..., description="relative_path of a previously indexed file"),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> FileContentOut:
    await _get_owned_repository(db, workspace, repository_id)

    result = await db.execute(
        select(IndexedFile).where(
            IndexedFile.repository_id == repository_id, IndexedFile.relative_path == path
        )
    )
    indexed_file = result.scalar_one_or_none()
    if indexed_file is None or indexed_file.content is None:
        raise NotFoundError("File not found in this repository's index.")

    return FileContentOut(
        relative_path=indexed_file.relative_path,
        language=indexed_file.language,
        content=indexed_file.content,
    )


@router.get("/symbols", response_model=list[SymbolOut])
async def list_symbols(
    repository_id: uuid.UUID,
    file_path: str | None = Query(default=None),
    name: str | None = Query(default=None),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> list[SymbolOut]:
    await _get_owned_repository(db, workspace, repository_id)

    query = (
        select(CodeSymbol, IndexedFile.relative_path)
        .join(IndexedFile, CodeSymbol.indexed_file_id == IndexedFile.id)
        .where(CodeSymbol.repository_id == repository_id)
    )
    if file_path:
        query = query.where(IndexedFile.relative_path == file_path)
    if name:
        query = query.where(CodeSymbol.name.ilike(f"%{name}%"))

    result = await db.execute(query.order_by(CodeSymbol.start_line).limit(500))

    return [
        SymbolOut(
            id=symbol.id,
            name=symbol.name,
            symbol_type=symbol.symbol_type,
            parent_name=symbol.parent_name,
            start_line=symbol.start_line,
            end_line=symbol.end_line,
            signature=symbol.signature,
            file_path=path,
        )
        for symbol, path in result.all()
    ]
