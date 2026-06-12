from typing import Literal

from debate.state import DebateState


def wikipedia_allowed(
    state: DebateState, speaker: Literal["Red", "Green"], current_turn: int
) -> bool:
    key = "wikipedia_turn_red" if speaker == "Red" else "wikipedia_turn_green"
    used_turn = state.get(key)
    return used_turn is None or used_turn == current_turn
