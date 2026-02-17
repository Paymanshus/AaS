import asyncio
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user
from app.core.config import get_settings
from app.db.models import (
    Argument,
    ArgumentInvite,
    ArgumentParticipant,
    ArgumentReport,
    ArgumentStatus,
    AudienceReaction,
    RoleKind,
    Turn,
    TurnEvent,
)
from app.db.session import get_session
from app.schemas.argument import (
    ArgumentListItem,
    ArgumentView,
    CreateArgumentRequest,
    CreateInviteRequest,
    InviteResponse,
    JoinRequest,
    MyArgumentsResponse,
    ParticipantView,
    PersonaSnapshot,
    ReactionRequest,
    StartArgumentRequest,
    StartResponse,
    TurnEventView,
    TurnView,
)
from app.schemas.report import ArgumentReportView, WrappedReport
from app.services.argument_engine import shape_config
from app.services.credits import consume_start_credit, ensure_user, get_credit_balance
from app.services.events import persist_event
from app.workers.actors import run_argument_actor
from app.workers.runtime import run_argument, run_postprocess

settings = get_settings()
router = APIRouter(prefix="/v1", tags=["arguments"])


def _as_utc(dt: datetime) -> datetime:
    # SQLite may deserialize timezone columns as naive datetimes.
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


async def _get_argument_or_404(session: AsyncSession, argument_id: str) -> Argument:
    argument = await session.get(Argument, argument_id)
    if not argument:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Argument not found")
    return argument


async def _get_participants(session: AsyncSession, argument_id: str) -> list[ArgumentParticipant]:
    rows = await session.execute(
        select(ArgumentParticipant)
        .where(ArgumentParticipant.argument_id == argument_id)
        .order_by(ArgumentParticipant.seat_order.asc())
    )
    return list(rows.scalars().all())


async def _is_participant(session: AsyncSession, argument_id: str, user_id: str) -> bool:
    row = await session.execute(
        select(ArgumentParticipant.id).where(
            and_(ArgumentParticipant.argument_id == argument_id, ArgumentParticipant.user_id == user_id)
        )
    )
    return row.scalar_one_or_none() is not None


async def _is_valid_spectator_token(
    session: AsyncSession, argument_id: str, audience_token: str | None
) -> bool:
    if not audience_token:
        return False
    row = await session.execute(
        select(ArgumentInvite.id).where(
            and_(
                ArgumentInvite.argument_id == argument_id,
                ArgumentInvite.token == audience_token,
                ArgumentInvite.role == RoleKind.SPECTATOR,
                ArgumentInvite.expires_at >= datetime.now(UTC),
            )
        )
    )
    return row.scalar_one_or_none() is not None


def _argument_to_view(argument: Argument, participants: list[ArgumentParticipant]) -> ArgumentView:
    return ArgumentView(
        id=argument.id,
        topic=argument.topic,
        creator_user_id=argument.creator_user_id,
        status=argument.status,
        phase=argument.phase,
        controls=argument.controls,
        turn_count=argument.turn_count,
        audience_mode=argument.audience_mode,
        created_at=argument.created_at,
        started_at=argument.started_at,
        ended_at=argument.ended_at,
        participants=[
            ParticipantView(
                id=participant.id,
                user_id=participant.user_id,
                seat_order=participant.seat_order,
                ready=participant.ready,
                persona_snapshot=participant.persona_snapshot,
            )
            for participant in participants
        ],
    )


@router.get("/me/arguments", response_model=MyArgumentsResponse)
async def my_arguments(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MyArgumentsResponse:
    await ensure_user(session, current_user.user_id, current_user.handle)
    rows = await session.execute(
        select(Argument)
        .join(ArgumentParticipant, ArgumentParticipant.argument_id == Argument.id)
        .where(ArgumentParticipant.user_id == current_user.user_id)
        .order_by(Argument.created_at.desc())
    )
    all_arguments = list(rows.scalars().all())

    active = [
        ArgumentListItem(
            id=argument.id,
            topic=argument.topic,
            status=argument.status,
            phase=argument.phase,
            created_at=argument.created_at,
            started_at=argument.started_at,
            ended_at=argument.ended_at,
        )
        for argument in all_arguments
        if argument.status in {ArgumentStatus.WAITING, ArgumentStatus.RUNNING}
    ]
    past = [
        ArgumentListItem(
            id=argument.id,
            topic=argument.topic,
            status=argument.status,
            phase=argument.phase,
            created_at=argument.created_at,
            started_at=argument.started_at,
            ended_at=argument.ended_at,
        )
        for argument in all_arguments
        if argument.status in {ArgumentStatus.COMPLETED, ArgumentStatus.FAILED}
    ]
    balance = await get_credit_balance(session, current_user.user_id)
    await session.commit()
    return MyArgumentsResponse(active=active, past=past, credits_balance=balance)


@router.post("/arguments", response_model=ArgumentView)
async def create_argument(
    payload: CreateArgumentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ArgumentView:
    await ensure_user(session, current_user.user_id, current_user.handle)
    shape = shape_config(payload.controls.argument_shape.value)

    argument = Argument(
        creator_user_id=current_user.user_id,
        topic=payload.topic,
        controls=payload.controls.model_dump(mode="json"),
        max_turns=shape["max_turns"],
        target_min_tokens=shape["min_tokens"],
        target_max_tokens=shape["max_tokens"],
        audience_mode=payload.controls.audience_mode,
    )
    session.add(argument)
    await session.flush()

    participant = ArgumentParticipant(
        argument_id=argument.id,
        user_id=current_user.user_id,
        seat_order=0,
        ready=False,
        persona_snapshot=None,
    )
    session.add(participant)
    await session.commit()

    participants = await _get_participants(session, argument.id)
    return _argument_to_view(argument, participants)


@router.get("/arguments/{argument_id}", response_model=ArgumentView)
async def get_argument(
    argument_id: str,
    audience_token: str | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ArgumentView:
    argument = await _get_argument_or_404(session, argument_id)
    is_member = await _is_participant(session, argument_id, current_user.user_id)
    can_spectate = argument.audience_mode and await _is_valid_spectator_token(
        session, argument_id, audience_token
    )
    if not is_member and not can_spectate:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    participants = await _get_participants(session, argument_id)
    return _argument_to_view(argument, participants)


@router.post("/arguments/{argument_id}/invites", response_model=InviteResponse)
async def create_invite(
    argument_id: str,
    payload: CreateInviteRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> InviteResponse:
    argument = await _get_argument_or_404(session, argument_id)
    if argument.creator_user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only creator can issue invites")

    token = secrets.token_urlsafe(24)
    expires_at = datetime.now(UTC) + timedelta(minutes=payload.expires_in_minutes)
    invite = ArgumentInvite(
        argument_id=argument_id,
        role=payload.role,
        token=token,
        expires_at=expires_at,
    )
    session.add(invite)
    await session.commit()

    if payload.role == RoleKind.PARTICIPANT:
        url = f"{settings.web_base_url}/join/{argument_id}?token={token}"
    else:
        url = f"{settings.web_base_url}/arguments/{argument_id}?audienceToken={token}"

    return InviteResponse(token=token, role=payload.role, url=url, expires_at=expires_at)


@router.post("/arguments/{argument_id}/join")
async def join_argument(
    argument_id: str,
    payload: JoinRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await ensure_user(session, current_user.user_id, current_user.handle)
    argument = await _get_argument_or_404(session, argument_id)

    invite_query = await session.execute(
        select(ArgumentInvite).where(
            and_(ArgumentInvite.argument_id == argument_id, ArgumentInvite.token == payload.token)
        )
    )
    invite = invite_query.scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite token")
    if _as_utc(invite.expires_at) < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invite expired")

    role = invite.role
    if role == RoleKind.PARTICIPANT:
        if invite.used_by_user_id and invite.used_by_user_id != current_user.user_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invite already consumed")

        participant_row = await session.execute(
            select(ArgumentParticipant).where(
                and_(
                    ArgumentParticipant.argument_id == argument_id,
                    ArgumentParticipant.user_id == current_user.user_id,
                )
            )
        )
        participant = participant_row.scalar_one_or_none()
        if participant is None:
            seat_count_result = await session.execute(
                select(func.count(ArgumentParticipant.id)).where(ArgumentParticipant.argument_id == argument_id)
            )
            seat_count = int(seat_count_result.scalar_one())
            if seat_count >= settings.max_participants:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Argument already has max participants ({settings.max_participants})",
                )
            participant = ArgumentParticipant(
                argument_id=argument.id,
                user_id=current_user.user_id,
                seat_order=seat_count,
                ready=False,
            )
            session.add(participant)

        invite.used_by_user_id = current_user.user_id
        invite.used_at = datetime.now(UTC)

    await session.commit()
    return {"argument_id": argument_id, "role": role.value}


@router.put("/arguments/{argument_id}/participants/me/persona")
async def update_persona_snapshot(
    argument_id: str,
    payload: PersonaSnapshot,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    argument = await _get_argument_or_404(session, argument_id)
    if argument.status != ArgumentStatus.WAITING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Persona is locked after start")

    participant_row = await session.execute(
        select(ArgumentParticipant).where(
            and_(
                ArgumentParticipant.argument_id == argument_id,
                ArgumentParticipant.user_id == current_user.user_id,
            )
        )
    )
    participant = participant_row.scalar_one_or_none()
    if not participant:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant")

    participant.persona_snapshot = payload.model_dump(mode="json")
    participant.ready = False
    await session.commit()
    return {"ok": True}


@router.post("/arguments/{argument_id}/ready")
async def mark_ready(
    argument_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    argument = await _get_argument_or_404(session, argument_id)
    if argument.status != ArgumentStatus.WAITING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Argument already started")

    participant_row = await session.execute(
        select(ArgumentParticipant).where(
            and_(
                ArgumentParticipant.argument_id == argument_id,
                ArgumentParticipant.user_id == current_user.user_id,
            )
        )
    )
    participant = participant_row.scalar_one_or_none()
    if not participant:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant")
    if not participant.persona_snapshot:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Set persona before ready")

    participant.ready = True
    await session.commit()
    return {"ok": True}


async def _run_inline(argument_id: str) -> None:
    await run_argument(argument_id)
    await run_postprocess(argument_id)


@router.post("/arguments/{argument_id}/start", response_model=StartResponse)
async def start_argument(
    argument_id: str,
    payload: StartArgumentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> StartResponse:
    argument = await _get_argument_or_404(session, argument_id)
    if argument.creator_user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only initiator can start")

    if argument.status != ArgumentStatus.WAITING:
        if (
            payload.idempotency_key
            and argument.start_idempotency_key
            and payload.idempotency_key == argument.start_idempotency_key
        ):
            return StartResponse(argument_id=argument.id, status="already_started")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Argument is not startable")

    participants = await _get_participants(session, argument_id)
    ready = [participant for participant in participants if participant.ready]
    if len(ready) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least 2 ready participants")
    if any(not participant.persona_snapshot for participant in ready):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ready participants need persona")

    try:
        await consume_start_credit(session, current_user.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc

    argument.status = ArgumentStatus.RUNNING
    argument.started_at = datetime.now(UTC)
    argument.started_by_user_id = current_user.user_id
    if payload.idempotency_key:
        argument.start_idempotency_key = payload.idempotency_key

    await persist_event(
        session,
        argument_id=argument.id,
        event_type="turn.meta",
        payload={"state": "starting", "topic": argument.topic},
    )
    await session.commit()

    if settings.inline_debate_runner:
        asyncio.create_task(_run_inline(argument.id))
    else:
        try:
            run_argument_actor.send(argument.id)
        except Exception:
            # Local fallback when broker is unavailable.
            asyncio.create_task(_run_inline(argument.id))

    return StartResponse(argument_id=argument.id, status="started")


@router.get("/arguments/{argument_id}/turns")
async def get_turns(
    argument_id: str,
    audience_token: str | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    argument = await _get_argument_or_404(session, argument_id)
    is_member = await _is_participant(session, argument_id, current_user.user_id)
    can_spectate = argument.audience_mode and await _is_valid_spectator_token(
        session, argument_id, audience_token
    )
    if not is_member and not can_spectate:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    turns_result = await session.execute(
        select(Turn).where(Turn.argument_id == argument_id).order_by(Turn.turn_index.asc())
    )
    events_result = await session.execute(
        select(TurnEvent).where(TurnEvent.argument_id == argument_id).order_by(TurnEvent.id.asc())
    )

    turns = [
        TurnView(
            id=turn.id,
            turn_index=turn.turn_index,
            speaker_participant_id=turn.speaker_participant_id,
            phase=turn.phase,
            content=turn.content,
            metrics=turn.metrics,
            model_metadata=turn.model_metadata,
            created_at=turn.created_at,
        )
        for turn in turns_result.scalars().all()
    ]
    events = [
        TurnEventView(
            id=event.id,
            turn_index=event.turn_index,
            event_type=event.event_type,
            payload=event.payload,
            created_at=event.created_at,
        )
        for event in events_result.scalars().all()
    ]

    return {"turns": turns, "events": events}


@router.post("/arguments/{argument_id}/reactions")
async def add_reaction(
    argument_id: str,
    payload: ReactionRequest,
    audience_token: str | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    argument = await _get_argument_or_404(session, argument_id)
    if not argument.audience_mode:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audience mode is disabled")

    is_member = await _is_participant(session, argument_id, current_user.user_id)
    can_spectate = await _is_valid_spectator_token(session, argument_id, audience_token)
    if not is_member and not can_spectate:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    reaction = AudienceReaction(
        argument_id=argument_id,
        user_id=current_user.user_id,
        emoji=payload.emoji,
        turn_index=payload.turn_index,
    )
    session.add(reaction)
    await session.flush()
    await persist_event(
        session,
        argument_id=argument_id,
        event_type="reaction.added",
        payload={
            "emoji": payload.emoji,
            "turn_index": payload.turn_index,
            "user_id": current_user.user_id,
        },
        turn_index=payload.turn_index,
    )
    await session.commit()
    return {"ok": True}


@router.get("/arguments/{argument_id}/report", response_model=ArgumentReportView)
async def get_report(
    argument_id: str,
    audience_token: str | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ArgumentReportView:
    argument = await _get_argument_or_404(session, argument_id)
    is_member = await _is_participant(session, argument_id, current_user.user_id)
    can_spectate = argument.audience_mode and await _is_valid_spectator_token(
        session, argument_id, audience_token
    )
    if not is_member and not can_spectate:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    report_result = await session.execute(
        select(ArgumentReport).where(ArgumentReport.argument_id == argument_id)
    )
    report = report_result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not ready")

    return ArgumentReportView(
        argument_id=argument_id,
        summary=report.summary,
        report=WrappedReport(**report.report_json),
        created_at=report.created_at,
    )
