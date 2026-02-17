from app.workers.langgraph_scheduler import generate_turn_schedule


def test_schedule_length_matches_max_turns() -> None:
    schedule = generate_turn_schedule(participant_count=3, max_turns=7)
    assert len(schedule) == 7


def test_schedule_rotates_participants() -> None:
    schedule = generate_turn_schedule(participant_count=2, max_turns=6)
    assert schedule == [0, 1, 0, 1, 0, 1]
