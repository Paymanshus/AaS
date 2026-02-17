import asyncio
from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Argument, ArgumentParticipant, ArgumentPhase, ArgumentReport, ArgumentStatus, BadgeAward, Turn
from app.db.session import SessionLocal
from app.services.argument_engine import PACE_DELAYS, compute_phase, cosine_similarity
from app.services.badges import maybe_award_badge
from app.services.events import persist_event
from app.services.moderation import moderate_text
from app.services.reporting import build_wrapped_report
from app.workers.langgraph_scheduler import generate_turn_schedule
from app.workers.llm import generate_turn_text


def _extract_points(snapshot: dict | None) -> list[str]:
    if not snapshot:
        return ["I refuse to yield this ground", "This tradeoff is unacceptable", "The burden of proof is unmet"]
    points = snapshot.get("defend_points") or []
    cleaned = [str(item).strip() for item in points if str(item).strip()]
    if len(cleaned) < 3:
        cleaned.extend(["This is still unresolved"] * (3 - len(cleaned)))
    return cleaned[:3]


def _extract_stance(snapshot: dict | None) -> str:
    if not snapshot:
        return "I stand by my position"
    return str(snapshot.get("stance") or "I stand by my position")


async def run_argument(argument_id: str) -> None:
    async with SessionLocal() as session:
        argument = await session.get(Argument, argument_id)
        if not argument or argument.status != ArgumentStatus.RUNNING:
            return

        result = await session.execute(
            select(ArgumentParticipant)
            .where(ArgumentParticipant.argument_id == argument_id)
            .where(ArgumentParticipant.ready.is_(True))
            .order_by(ArgumentParticipant.seat_order.asc())
        )
        participants = list(result.scalars().all())
        if len(participants) < 2:
            argument.status = ArgumentStatus.FAILED
            await persist_event(
                session,
                argument_id=argument_id,
                event_type="error",
                payload={"message": "Not enough ready participants"},
            )
            await session.commit()
            return

        controls = argument.controls or {}
        composure = int(controls.get("argument_composure", 45))
        pace_mode = controls.get("pace_mode", "NORMAL")
        evidence_mode = controls.get("evidence_mode", "FREEFORM")
        win_condition = controls.get("win_condition", "BE_RIGHT")

        delay = PACE_DELAYS.get(pace_mode, 0.03)
        max_turns = int(argument.max_turns)
        turn_schedule = generate_turn_schedule(len(participants), max_turns)

        claim_usage: dict[str, set[int]] = defaultdict(set)
        done_streak: dict[str, int] = defaultdict(int)
        previous_turn_text: str | None = None
        stagnation_hits = 0
        badge_cooldown = 0
        badges_so_far = 0

        await persist_event(
            session,
            argument_id=argument_id,
            event_type="phase.changed",
            payload={"phase": argument.phase.value},
        )
        await session.commit()

        for turn_index, speaker_idx in enumerate(turn_schedule, start=1):
            speaker = participants[speaker_idx]
            phase = compute_phase(turn_index, max_turns)
            if argument.phase != phase:
                argument.phase = phase
                await persist_event(
                    session,
                    argument_id=argument_id,
                    event_type="phase.changed",
                    payload={"phase": argument.phase.value},
                    turn_index=turn_index,
                )
                await session.commit()

            points = _extract_points(speaker.persona_snapshot)
            stance = _extract_stance(speaker.persona_snapshot)

            unused_claim_idx = next((idx for idx in range(len(points)) if idx not in claim_usage[speaker.id]), None)
            if unused_claim_idx is None:
                chosen_idx = (turn_index + speaker.seat_order) % len(points)
                done_hint = turn_index > int(max_turns * 0.6)
            else:
                chosen_idx = unused_claim_idx
                done_hint = False

            chosen_point = points[chosen_idx]
            is_new_claim = chosen_idx not in claim_usage[speaker.id]
            claim_usage[speaker.id].add(chosen_idx)

            generated = await generate_turn_text(
                speaker_handle=speaker.user_id,
                stance=stance,
                chosen_point=chosen_point,
                opponent_last_turn=previous_turn_text,
                win_condition=win_condition,
                phase=phase,
                evidence_mode=evidence_mode,
                turn_index=turn_index,
                max_turns=max_turns,
                done_hint=done_hint,
            )
            moderated_text, was_flagged = moderate_text(generated)

            await persist_event(
                session,
                argument_id=argument_id,
                event_type="turn.meta",
                payload={"speaker_participant_id": speaker.id, "state": "thinking"},
                turn_index=turn_index,
            )
            await session.commit()

            token_buffer = []
            for token in moderated_text.split():
                token_buffer.append(token)
                await persist_event(
                    session,
                    argument_id=argument_id,
                    event_type="turn.token",
                    payload={
                        "speaker_participant_id": speaker.id,
                        "token": f"{token} ",
                    },
                    turn_index=turn_index,
                )
                await session.commit()
                await asyncio.sleep(delay)

            final_text = " ".join(token_buffer).strip()
            similarity = cosine_similarity(previous_turn_text or "", final_text)
            if similarity > 0.9 and not is_new_claim:
                stagnation_hits += 1
            else:
                stagnation_hits = max(0, stagnation_hits - 1)

            if done_hint and not is_new_claim:
                done_streak[speaker.id] += 1
            else:
                done_streak[speaker.id] = 0

            turn = Turn(
                argument_id=argument_id,
                turn_index=turn_index,
                speaker_participant_id=speaker.id,
                phase=phase,
                content=final_text,
                metrics={
                    "similarity_to_previous": similarity,
                    "is_new_claim": is_new_claim,
                    "was_flagged": was_flagged,
                },
                model_metadata={"provider": "template_llm", "mode": "mvp"},
            )
            session.add(turn)
            argument.turn_count = turn_index
            await session.flush()

            await persist_event(
                session,
                argument_id=argument_id,
                event_type="turn.final",
                payload={
                    "turn_id": turn.id,
                    "speaker_participant_id": speaker.id,
                    "content": final_text,
                    "phase": phase.value,
                },
                turn_index=turn_index,
            )

            badge = maybe_award_badge(
                turn_text=final_text,
                previous_turn_text=previous_turn_text,
                evidence_mode=evidence_mode,
                composure=composure,
                turn_index=turn_index,
                cooldown_remaining=badge_cooldown,
                badges_so_far=badges_so_far,
            )
            if badge and badge.confidence >= 0.68:
                badge_row = BadgeAward(
                    argument_id=argument_id,
                    turn_id=turn.id,
                    badge_key=badge.badge_key,
                    reason=badge.reason,
                    confidence=badge.confidence,
                )
                session.add(badge_row)
                badges_so_far += 1
                badge_cooldown = 2
                await session.flush()
                await persist_event(
                    session,
                    argument_id=argument_id,
                    event_type="badge.awarded",
                    payload={
                        "turn_id": turn.id,
                        "turn_index": turn_index,
                        "badge_key": badge.badge_key,
                        "reason": badge.reason,
                        "confidence": badge.confidence,
                    },
                    turn_index=turn_index,
                )
            else:
                badge_cooldown = max(0, badge_cooldown - 1)

            previous_turn_text = final_text
            await session.commit()

            everyone_done = all(done_streak[p.id] >= 2 for p in participants)
            if everyone_done or stagnation_hits >= 2:
                break

        argument.status = ArgumentStatus.COMPLETED
        argument.ended_at = datetime.now(UTC)
        await persist_event(
            session,
            argument_id=argument_id,
            event_type="argument.completed",
            payload={"turn_count": argument.turn_count, "reason": "natural_stop"},
            turn_index=argument.turn_count,
        )
        await session.commit()


async def run_postprocess(argument_id: str) -> None:
    async with SessionLocal() as session:
        argument = await session.get(Argument, argument_id)
        if not argument:
            return

        turn_rows = await session.execute(
            select(Turn)
            .where(Turn.argument_id == argument_id)
            .order_by(Turn.turn_index.asc())
        )
        turns = list(turn_rows.scalars().all())

        badge_rows = await session.execute(
            select(BadgeAward)
            .where(BadgeAward.argument_id == argument_id)
            .order_by(BadgeAward.created_at.asc())
        )
        badges = [
            {"badge_key": row.badge_key, "reason": row.reason, "confidence": row.confidence}
            for row in badge_rows.scalars().all()
        ]

        summary, wrapped = build_wrapped_report(argument.topic, turns, badges)

        existing_report_row = await session.execute(
            select(ArgumentReport).where(ArgumentReport.argument_id == argument_id)
        )
        existing_report = existing_report_row.scalar_one_or_none()
        if existing_report:
            existing_report.summary = summary
            existing_report.report_json = wrapped
        else:
            report = ArgumentReport(argument_id=argument_id, summary=summary, report_json=wrapped)
            session.add(report)

        await persist_event(
            session,
            argument_id=argument_id,
            event_type="turn.meta",
            payload={"state": "report_ready"},
            turn_index=argument.turn_count,
        )
        await session.commit()
