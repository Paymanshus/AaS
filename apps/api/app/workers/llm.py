from openai import AsyncOpenAI

from app.core.config import get_settings
from app.db.models import ArgumentPhase

settings = get_settings()
_client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None


def build_turn_text(
    *,
    speaker_handle: str,
    stance: str,
    chosen_point: str,
    opponent_last_turn: str | None,
    win_condition: str,
    phase: ArgumentPhase,
    evidence_mode: str,
    turn_index: int,
    max_turns: int,
    done_hint: bool,
) -> str:
    phase_prefix = {
        ArgumentPhase.OPENING: "Opening salvo",
        ArgumentPhase.ESCALATION: "Pressure phase",
        ArgumentPhase.RESOLUTION: "Closing move",
    }[phase]

    opponent_line = (
        "You made one fair point, but it still misses the core issue."
        if opponent_last_turn
        else "Setting the frame before this gets chaotic."
    )

    win_line = {
        "BE_RIGHT": "Goal: expose the flaw, not just talk louder.",
        "FIND_OVERLAP": "Goal: lock one concrete overlap before this ends.",
        "EXPOSE_WEAK_POINTS": "Goal: test weak links and keep receipts.",
        "UNDERSTAND_OTHER_SIDE": "Goal: translate their logic before countering.",
    }.get(win_condition, "Goal: stay coherent and land clean points.")

    evidence_line = (
        "I am anchoring this on a concrete claim and outcome signal."
        if evidence_mode == "RECEIPTS_PREFERRED"
        else "I am focusing on argument logic over citation format."
    )

    end_line = "I have nothing meaningfully new after this turn." if done_hint else ""

    return (
        f"[{phase_prefix}] {speaker_handle}: {opponent_line} "
        f"My stance is {stance}. Core point: {chosen_point}. "
        f"{win_line} {evidence_line} "
        f"Turn {turn_index}/{max_turns}. {end_line}"
    ).strip()


async def generate_turn_text(
    *,
    speaker_handle: str,
    stance: str,
    chosen_point: str,
    opponent_last_turn: str | None,
    win_condition: str,
    phase: ArgumentPhase,
    evidence_mode: str,
    turn_index: int,
    max_turns: int,
    done_hint: bool,
) -> str:
    fallback = build_turn_text(
        speaker_handle=speaker_handle,
        stance=stance,
        chosen_point=chosen_point,
        opponent_last_turn=opponent_last_turn,
        win_condition=win_condition,
        phase=phase,
        evidence_mode=evidence_mode,
        turn_index=turn_index,
        max_turns=max_turns,
        done_hint=done_hint,
    )

    if _client is None:
        return fallback

    system_prompt = (
        "You are an argument agent in AaS. Stay concise, witty, and useful. "
        "No personal attacks. Keep claims tight and respond directly."
    )
    user_prompt = (
        f"Speaker: {speaker_handle}\n"
        f"Stance: {stance}\n"
        f"Point to defend: {chosen_point}\n"
        f"Opponent last turn: {opponent_last_turn or 'N/A'}\n"
        f"Phase: {phase.value}\n"
        f"Win condition: {win_condition}\n"
        f"Evidence mode: {evidence_mode}\n"
        f"Turn {turn_index} of {max_turns}.\n"
        f"If truly done, end with: I have nothing meaningfully new after this turn."
    )

    try:
        response = await _client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=320,
            temperature=0.9,
        )
        content = (response.choices[0].message.content or "").strip()
        return content or fallback
    except Exception:
        return fallback
