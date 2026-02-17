import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RoleKind(str, enum.Enum):
    PARTICIPANT = "participant"
    SPECTATOR = "spectator"


class ArgumentStatus(str, enum.Enum):
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ArgumentPhase(str, enum.Enum):
    OPENING = "opening"
    ESCALATION = "escalation"
    RESOLUTION = "resolution"


class ArgumentShape(str, enum.Enum):
    QUICK_SKIRMISH = "QUICK_SKIRMISH"
    PROPER_THROWDOWN = "PROPER_THROWDOWN"
    SLOW_BURN = "SLOW_BURN"


class WinCondition(str, enum.Enum):
    BE_RIGHT = "BE_RIGHT"
    FIND_OVERLAP = "FIND_OVERLAP"
    EXPOSE_WEAK_POINTS = "EXPOSE_WEAK_POINTS"
    UNDERSTAND_OTHER_SIDE = "UNDERSTAND_OTHER_SIDE"


class PaceMode(str, enum.Enum):
    FAST = "FAST"
    NORMAL = "NORMAL"
    DRAMATIC = "DRAMATIC"


class EvidenceMode(str, enum.Enum):
    FREEFORM = "FREEFORM"
    RECEIPTS_PREFERRED = "RECEIPTS_PREFERRED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    handle: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class Persona(Base):
    __tablename__ = "personas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    stance_style: Mapped[str] = mapped_column(String(240), nullable=False)
    points_default: Mapped[list[str]] = mapped_column(JSON, default=list)
    red_lines_default: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class Argument(Base):
    __tablename__ = "arguments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    creator_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    topic: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[ArgumentStatus] = mapped_column(
        Enum(ArgumentStatus), nullable=False, default=ArgumentStatus.WAITING
    )
    phase: Mapped[ArgumentPhase] = mapped_column(
        Enum(ArgumentPhase), nullable=False, default=ArgumentPhase.OPENING
    )
    controls: Mapped[dict] = mapped_column(JSON, default=dict)
    max_turns: Mapped[int] = mapped_column(Integer, default=8)
    target_min_tokens: Mapped[int] = mapped_column(Integer, default=80)
    target_max_tokens: Mapped[int] = mapped_column(Integer, default=140)
    audience_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    turn_count: Mapped[int] = mapped_column(Integer, default=0)
    start_idempotency_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    started_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ArgumentParticipant(Base):
    __tablename__ = "argument_participants"
    __table_args__ = (
        UniqueConstraint("argument_id", "user_id", name="uq_argument_participant_user"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    argument_id: Mapped[str] = mapped_column(ForeignKey("arguments.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    seat_order: Mapped[int] = mapped_column(Integer, nullable=False)
    ready: Mapped[bool] = mapped_column(Boolean, default=False)
    persona_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ArgumentInvite(Base):
    __tablename__ = "argument_invites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    argument_id: Mapped[str] = mapped_column(ForeignKey("arguments.id", ondelete="CASCADE"), index=True)
    role: Mapped[RoleKind] = mapped_column(Enum(RoleKind), nullable=False)
    token: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class Turn(Base):
    __tablename__ = "turns"
    __table_args__ = (UniqueConstraint("argument_id", "turn_index", name="uq_turn_argument_index"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    argument_id: Mapped[str] = mapped_column(ForeignKey("arguments.id", ondelete="CASCADE"), index=True)
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    speaker_participant_id: Mapped[str] = mapped_column(
        ForeignKey("argument_participants.id", ondelete="CASCADE"), index=True
    )
    phase: Mapped[ArgumentPhase] = mapped_column(Enum(ArgumentPhase), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    model_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class TurnEvent(Base):
    __tablename__ = "turn_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    argument_id: Mapped[str] = mapped_column(ForeignKey("arguments.id", ondelete="CASCADE"), index=True)
    turn_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class BadgeAward(Base):
    __tablename__ = "badges_awarded"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    argument_id: Mapped[str] = mapped_column(ForeignKey("arguments.id", ondelete="CASCADE"), index=True)
    turn_id: Mapped[str] = mapped_column(ForeignKey("turns.id", ondelete="CASCADE"), index=True)
    badge_key: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str] = mapped_column(String(300), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ArgumentReport(Base):
    __tablename__ = "argument_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    argument_id: Mapped[str] = mapped_column(
        ForeignKey("arguments.id", ondelete="CASCADE"), index=True, unique=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    report_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class CreditLedger(Base):
    __tablename__ = "credit_ledger"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(120), nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class AudienceReaction(Base):
    __tablename__ = "audience_reactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    argument_id: Mapped[str] = mapped_column(ForeignKey("arguments.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    emoji: Mapped[str] = mapped_column(String(8), nullable=False)
    turn_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
