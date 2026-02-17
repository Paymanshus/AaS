from dataclasses import dataclass


@dataclass
class BadgeDecision:
    badge_key: str
    reason: str
    confidence: float


BADGE_RULES = {
    "mic_drop": "Sharp closer with quotable impact.",
    "receipt_slinger": "Brought concrete receipts when needed.",
    "calm_sniper": "Stayed cool while landing clean counters.",
    "combo_chain": "Built on previous points with momentum.",
}


def maybe_award_badge(
    *,
    turn_text: str,
    previous_turn_text: str | None,
    evidence_mode: str,
    composure: int,
    turn_index: int,
    cooldown_remaining: int,
    badges_so_far: int,
) -> BadgeDecision | None:
    if cooldown_remaining > 0 or badges_so_far >= 4:
        return None

    cleaned = turn_text.strip()
    lower = cleaned.lower()

    if evidence_mode == "RECEIPTS_PREFERRED" and any(key in lower for key in ("source", "data", "stat")):
        return BadgeDecision("receipt_slinger", BADGE_RULES["receipt_slinger"], 0.84)

    if len(cleaned) > 180 and cleaned.endswith(".") and composure < 45:
        return BadgeDecision("mic_drop", BADGE_RULES["mic_drop"], 0.78)

    if composure < 35 and "!" not in cleaned and "you" in lower:
        return BadgeDecision("calm_sniper", BADGE_RULES["calm_sniper"], 0.73)

    if previous_turn_text and any(w in lower for w in ("building on", "as you said", "exactly")):
        if turn_index > 2:
            return BadgeDecision("combo_chain", BADGE_RULES["combo_chain"], 0.69)

    return None
