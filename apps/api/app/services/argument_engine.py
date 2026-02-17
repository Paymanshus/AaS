from collections import Counter
import math

from app.db.models import ArgumentPhase, ArgumentShape

SHAPE_DEFAULTS: dict[str, dict[str, int]] = {
    ArgumentShape.QUICK_SKIRMISH.value: {"max_turns": 8, "min_tokens": 80, "max_tokens": 140},
    ArgumentShape.PROPER_THROWDOWN.value: {"max_turns": 14, "min_tokens": 120, "max_tokens": 180},
    ArgumentShape.SLOW_BURN.value: {"max_turns": 10, "min_tokens": 180, "max_tokens": 300},
}

PACE_DELAYS = {
    "FAST": 0.01,
    "NORMAL": 0.03,
    "DRAMATIC": 0.06,
}


def shape_config(shape: str) -> dict[str, int]:
    return SHAPE_DEFAULTS.get(shape, SHAPE_DEFAULTS[ArgumentShape.QUICK_SKIRMISH.value])


def compute_phase(turn_index: int, max_turns: int) -> ArgumentPhase:
    if turn_index <= max(2, max_turns // 3):
        return ArgumentPhase.OPENING
    if turn_index <= max_turns - 2:
        return ArgumentPhase.ESCALATION
    return ArgumentPhase.RESOLUTION


def cosine_similarity(a: str, b: str) -> float:
    if not a.strip() or not b.strip():
        return 0.0
    a_counter = Counter(a.lower().split())
    b_counter = Counter(b.lower().split())

    keys = set(a_counter) | set(b_counter)
    dot = sum(a_counter.get(k, 0) * b_counter.get(k, 0) for k in keys)
    norm_a = math.sqrt(sum(v * v for v in a_counter.values()))
    norm_b = math.sqrt(sum(v * v for v in b_counter.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)
