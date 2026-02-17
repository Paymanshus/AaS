from app.services.badges import maybe_award_badge


def test_badge_respects_cooldown() -> None:
    badge = maybe_award_badge(
        turn_text="source data stat proof",
        previous_turn_text=None,
        evidence_mode="RECEIPTS_PREFERRED",
        composure=20,
        turn_index=4,
        cooldown_remaining=1,
        badges_so_far=0,
    )
    assert badge is None


def test_badge_awards_receipt_slinger() -> None:
    badge = maybe_award_badge(
        turn_text="I have source backed data and a stat to prove this",
        previous_turn_text=None,
        evidence_mode="RECEIPTS_PREFERRED",
        composure=55,
        turn_index=2,
        cooldown_remaining=0,
        badges_so_far=0,
    )
    assert badge is not None
    assert badge.badge_key == "receipt_slinger"
