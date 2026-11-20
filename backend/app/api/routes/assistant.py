import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import get_current_user, get_current_workspace
from app.core.config import Settings, get_settings
from app.core.database import get_db, get_session_factory
from app.core.exceptions import NotFoundError, ValidationError
from app.models.conversation import Conversation, Message
from app.models.repository import Repository
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.conversation import (
    AskRequest,
    ConversationOut,
    CreateConversationRequest,
    MessageOut,
)
from app.services.assistant.orchestrator import stream_answer
from app.services.llm.registry import NoProviderConfiguredError, get_llm_provider

router = APIRouter(tags=["assistant"])


async def _get_owned_repository(db: AsyncSession, workspace: Workspace, repository_id: uuid.UUID) -> Repository:
    repository = await db.get(Repository, repository_id)
    if repository is None or repository.workspace_id != workspace.id:
        raise NotFoundError("Repository not found.")
    return repository


async def _get_owned_conversation(
    db: AsyncSession, workspace: Workspace, conversation_id: uuid.UUID
) -> Conversation:
    conversation = await db.get(Conversation, conversation_id)
    if conversation is None:
        raise NotFoundError("Conversation not found.")
    await _get_owned_repository(db, workspace, conversation.repository_id)
    return conversation


@router.post(
    "/repositories/{repository_id}/conversations", response_model=ConversationOut, status_code=201
)
async def create_conversation(
    repository_id: uuid.UUID,
    body: CreateConversationRequest,
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> Conversation:
    await _get_owned_repository(db, workspace, repository_id)

    conversation = Conversation(
        repository_id=repository_id, user_id=user.id, title=body.title or "New conversation"
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


@router.get("/repositories/{repository_id}/conversations", response_model=list[ConversationOut])
async def list_conversations(
    repository_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> list[Conversation]:
    await _get_owned_repository(db, workspace, repository_id)

    result = await db.execute(
        select(Conversation)
        .where(Conversation.repository_id == repository_id)
        .order_by(Conversation.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
async def list_messages(
    conversation_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> list[Message]:
    await _get_owned_conversation(db, workspace, conversation_id)

    result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
    )
    return list(result.scalars().all())


@router.post("/conversations/{conversation_id}/messages")
async def ask(
    conversation_id: uuid.UUID,
    body: AskRequest,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> StreamingResponse:
    conversation = await _get_owned_conversation(db, workspace, conversation_id)

    if not body.question.strip():
        raise ValidationError("Question must not be empty.")

    try:
        provider = get_llm_provider(settings)
    except NoProviderConfiguredError as exc:
        raise ValidationError(f"No LLM provider configured: {exc}")

    return StreamingResponse(
        stream_answer(
            session_factory, settings, provider, conversation.repository_id, conversation.id, body.question
        ),
        media_type="text/event-stream",
    )
