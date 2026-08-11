from debate.initial_state import build_initial_state


def test_build_initial_state() -> None:
    state = build_initial_state("Climate policy debate")
    assert state["topic"] == "Climate policy debate"
    assert state["messages"] == []
    assert state["turn_red"] == 0
    assert state["turn_green"] == 0
    assert state["turn_messages"] == []
    assert state["active_speaker"] is None
    assert state["tool_loop_count"] == 0
    assert state["wikipedia_turn_red"] is None
    assert state["wikipedia_turn_green"] is None
