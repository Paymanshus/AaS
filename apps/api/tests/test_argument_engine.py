from app.services.argument_engine import compute_phase, cosine_similarity, shape_config


def test_shape_defaults_quick_skirmish() -> None:
    shape = shape_config("QUICK_SKIRMISH")
    assert shape["max_turns"] == 8
    assert shape["min_tokens"] == 80
    assert shape["max_tokens"] == 140


def test_phase_progression() -> None:
    assert compute_phase(1, 8).value == "opening"
    assert compute_phase(4, 8).value == "escalation"
    assert compute_phase(8, 8).value == "resolution"


def test_similarity_basic_order() -> None:
    near = cosine_similarity("same words here", "same words here")
    far = cosine_similarity("cats and dogs", "binary tree sorting")
    assert near > far
