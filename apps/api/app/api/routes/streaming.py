from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import orjson
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, select

from app.api.deps import CurrentUser, get_optional_user
from app.core.config import get_settings
from app.db.models import Argument, ArgumentInvite, ArgumentParticipant, RoleKind, TurnEvent
from app.db.session import SessionLocal
from app.services.events import get_event_bus

settings = get_settings()
router = APIRouter(prefix="/v1", tags=["streaming"])


async def _can_access(
    argument_id: str,
    *,
    user_id: str | None,
    audience_token: str | None,
) -> bool:
    async with SessionLocal() as session:
        argument = await session.get(Argument, argument_id)
        if not argument:
            return False

        if user_id:
            participant = await session.execute(
                select(ArgumentParticipant.id).where(
                    and_(
                        ArgumentParticipant.argument_id == argument_id,
                        ArgumentParticipant.user_id == user_id,
                    )
                )
            )
            if participant.scalar_one_or_none():
                return True

        if argument.audience_mode and audience_token:
            invite = await session.execute(
                select(ArgumentInvite.id).where(
                    and_(
                        ArgumentInvite.argument_id == argument_id,
                        ArgumentInvite.token == audience_token,
                        ArgumentInvite.role == RoleKind.SPECTATOR,
                        ArgumentInvite.expires_at >= datetime.now(UTC),
                    )
                )
            )
            if invite.scalar_one_or_none():
                return True

        return False


@router.websocket("/arguments/{argument_id}/stream")
async def stream_argument(
    websocket: WebSocket,
    argument_id: str,
) -> None:
    user_id = websocket.query_params.get("userId")
    audience_token = websocket.query_params.get("audienceToken")
    if not await _can_access(argument_id, user_id=user_id, audience_token=audience_token):
        await websocket.close(code=4403)
        return

    await websocket.accept()

    try:
        async with SessionLocal() as session:
            history = await session.execute(
                select(TurnEvent)
                .where(TurnEvent.argument_id == argument_id)
                .order_by(TurnEvent.id.asc())
                .limit(500)
            )
            for event in history.scalars().all():
                await websocket.send_json(
                    {
                        "id": event.id,
                        "argument_id": argument_id,
                        "event_type": event.event_type,
                        "payload": event.payload,
                        "turn_index": event.turn_index,
                        "created_at": event.created_at.isoformat(),
                    }
                )

        async for event in get_event_bus().subscribe(argument_id):
            await websocket.send_json(event)
    except WebSocketDisconnect:
        return


@router.get("/arguments/{argument_id}/spectate")
async def spectate_argument_sse(
    argument_id: str,
    audience_token: str = Query(default=""),
    current_user: CurrentUser | None = Depends(get_optional_user),
) -> StreamingResponse:
    if not settings.spectator_sse_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SSE disabled")

    user_id = current_user.user_id if current_user else None
    if not await _can_access(argument_id, user_id=user_id, audience_token=audience_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    async def event_stream() -> AsyncGenerator[str, None]:
        async with SessionLocal() as session:
            history = await session.execute(
                select(TurnEvent)
                .where(TurnEvent.argument_id == argument_id)
                .order_by(TurnEvent.id.asc())
                .limit(500)
            )
            for event in history.scalars().all():
                payload = {
                    "id": event.id,
                    "argument_id": argument_id,
                    "event_type": event.event_type,
                    "payload": event.payload,
                    "turn_index": event.turn_index,
                    "created_at": event.created_at.isoformat(),
                }
                yield f"data: {orjson.dumps(payload).decode('utf-8')}\n\n"

        async for event in get_event_bus().subscribe(argument_id):
            yield f"data: {orjson.dumps(event).decode('utf-8')}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
