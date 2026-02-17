from collections.abc import Callable
from typing import TypedDict

try:
    from langgraph.graph import END, StateGraph
except Exception:  # pragma: no cover
    END = "__end__"
    StateGraph = None


class ScheduleState(TypedDict):
    turn_index: int
    max_turns: int
    speaker_order: list[int]


def _fallback_schedule(participant_count: int, max_turns: int) -> list[int]:
    return [idx % participant_count for idx in range(max_turns)]


def _make_node(participant_idx: int) -> Callable[[ScheduleState], ScheduleState]:
    def _node(state: ScheduleState) -> ScheduleState:
        return {
            "turn_index": state["turn_index"] + 1,
            "max_turns": state["max_turns"],
            "speaker_order": [*state["speaker_order"], participant_idx],
        }

    return _node


def generate_turn_schedule(participant_count: int, max_turns: int) -> list[int]:
    if participant_count < 1:
        return []
    if StateGraph is None:
        return _fallback_schedule(participant_count, max_turns)

    graph = StateGraph(ScheduleState)
    node_names = [f"participant_{idx}" for idx in range(participant_count)]

    for idx, node_name in enumerate(node_names):
        graph.add_node(node_name, _make_node(idx))

    for idx, node_name in enumerate(node_names):
        next_node = node_names[(idx + 1) % participant_count]

        def _route(state: ScheduleState, _next: str = next_node) -> str:
            return END if state["turn_index"] >= state["max_turns"] else _next

        graph.add_conditional_edges(node_name, _route, {next_node: next_node, END: END})

    graph.set_entry_point(node_names[0])
    compiled = graph.compile()
    output = compiled.invoke({"turn_index": 0, "max_turns": max_turns, "speaker_order": []})
    return output["speaker_order"]
