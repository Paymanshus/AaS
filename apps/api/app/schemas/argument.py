from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.db.models import ArgumentPhase, ArgumentShape, ArgumentStatus, EvidenceMode, PaceMode, RoleKind, WinCondition


class Guardrails(BaseModel):
    no_personal_attacks: bool = True
    no_moral_absolutism: bool = False
    no_hypotheticals: bool = False
    steelman_before_rebuttal: bool = False
    stay_on_topic: bool = True


class ArgumentControls(BaseModel):
    argument_composure: int = Field(default=45, ge=0, le=100)
    argument_shape: ArgumentShape = ArgumentShape.QUICK_SKIRMISH
    win_condition: WinCondition = WinCondition.BE_RIGHT
    guardrails: Guardrails = Field(default_factory=Guardrails)
    audience_mode: bool = False
    pace_mode: PaceMode = PaceMode.NORMAL
    evidence_mode: EvidenceMode = EvidenceMode.FREEFORM


class CreateArgumentRequest(BaseModel):
    topic: str = Field(min_length=5, max_length=300)
    controls: ArgumentControls = Field(default_factory=ArgumentControls)


class CreateInviteRequest(BaseModel):
    role: RoleKind
    expires_in_minutes: int = Field(default=120, ge=5, le=24 * 60)


class JoinRequest(BaseModel):
    token: str = Field(min_length=8, max_length=200)


class PersonaSnapshot(BaseModel):
    stance: str = Field(min_length=2, max_length=200)
    defend_points: list[str] = Field(min_length=3, max_length=3)
    red_lines: list[str] = Field(default_factory=list, max_length=5)

    @field_validator("defend_points")
    @classmethod
    def validate_points(cls, value: list[str]) -> list[str]:
        normalized = [item.strip() for item in value if item.strip()]
        if len(normalized) != 3:
            raise ValueError("exactly 3 defend points are required")
        return normalized


class StartArgumentRequest(BaseModel):
    idempotency_key: str | None = Field(default=None, max_length=120)


class ReactionRequest(BaseModel):
    emoji: str = Field(min_length=1, max_length=8)
    turn_index: int | None = Field(default=None, ge=1)


class InviteResponse(BaseModel):
    token: str
    role: RoleKind
    url: str
    expires_at: datetime


class ParticipantView(BaseModel):
    id: str
    user_id: str
    seat_order: int
    ready: bool
    persona_snapshot: dict | None = None


class ArgumentView(BaseModel):
    id: str
    topic: str
    creator_user_id: str
    status: ArgumentStatus
    phase: ArgumentPhase
    controls: dict
    turn_count: int
    audience_mode: bool
    created_at: datetime
    started_at: datetime | None = None
    ended_at: datetime | None = None
    participants: list[ParticipantView]


class TurnView(BaseModel):
    id: str
    turn_index: int
    speaker_participant_id: str
    phase: ArgumentPhase
    content: str
    metrics: dict
    model_metadata: dict
    created_at: datetime


class TurnEventView(BaseModel):
    id: int
    turn_index: int | None
    event_type: str
    payload: dict
    created_at: datetime


class ArgumentListItem(BaseModel):
    id: str
    topic: str
    status: ArgumentStatus
    phase: ArgumentPhase
    created_at: datetime
    started_at: datetime | None = None
    ended_at: datetime | None = None


class MyArgumentsResponse(BaseModel):
    active: list[ArgumentListItem]
    past: list[ArgumentListItem]
    credits_balance: int


class StartResponse(BaseModel):
    argument_id: str
    status: Literal["started", "already_started"]
