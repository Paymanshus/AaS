from collections import defaultdict

from app.db.models import Turn


def build_wrapped_report(topic: str, turns: list[Turn], badges: list[dict]) -> tuple[str, dict]:
    if not turns:
        summary = f"No valid turns were produced for: {topic}"
        wrapped = {
            "who_cooked": "No one",
            "best_receipts": [],
            "most_stubborn_point": "No argument data",
            "unexpected_common_ground": "No overlap found",
            "momentum_shift_turn": None,
            "highlights": [],
        }
        return summary, wrapped

    by_speaker_count: dict[str, int] = defaultdict(int)
    for turn in turns:
        by_speaker_count[turn.speaker_participant_id] += 1

    winner_speaker = max(by_speaker_count.items(), key=lambda item: item[1])[0]
    top_quotes = [turn.content for turn in turns[:3]]
    highlights = [f"Turn {turn.turn_index}: {turn.content[:140]}" for turn in turns[:4]]

    badge_bits = [badge["badge_key"] for badge in badges[:3]]
    most_stubborn = turns[min(len(turns) - 1, max(1, len(turns) // 2))].content[:120]

    summary = (
        "Spicy, mostly coherent, and unexpectedly productive. "
        f"{len(turns)} turns exchanged with {len(badges)} heat moments."
    )
    wrapped = {
        "who_cooked": winner_speaker,
        "best_receipts": top_quotes,
        "most_stubborn_point": most_stubborn,
        "unexpected_common_ground": (
            "Both sides agreed momentum matters more than perfect certainty."
        ),
        "momentum_shift_turn": max(2, len(turns) // 2),
        "highlights": highlights + [f"Badge streak: {', '.join(badge_bits)}"] if badge_bits else highlights,
    }
    return summary, wrapped
