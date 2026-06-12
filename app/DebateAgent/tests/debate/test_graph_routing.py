from functools import partial
from typing import Literal

from langchain_core.messages import AIMessage

from debate.graph import (
    _route_after_agent,
    _route_after_finish,
    _route_after_tool,
    build_debate_graph,
)
from debate.initial_state import build_initial_state
from debate.state import DebateState


def _state(
    turn_red: int = 0,
    turn_green: int = 0,
    topic: str = "Test topic",
    *,
    turn_messages: list | None = None,
    active_speaker: Literal["Red", "Green"] | None = None,
    tool_loop_count: int = 0,
    wikipedia_turn_red: int | None = None,
    wikipedia_turn_green: int | None = None,
) -> DebateState:
    state = {
        **build_initial_state(topic),
        "turn_red": turn_red,
        "turn_green": turn_green,
        "tool_loop_count": tool_loop_count,
    }
    if turn_messages is not None:
        state["turn_messages"] = turn_messages
    if active_speaker is not None:
        state["active_speaker"] = active_speaker
    if wikipedia_turn_red is not None:
        state["wikipedia_turn_red"] = wikipedia_turn_red
    if wikipedia_turn_green is not None:
        state["wikipedia_turn_green"] = wikipedia_turn_green
    return state


def test_route_after_agent_with_tool_calls_goes_to_wikipedia_tool() -> None:
    route = partial(_route_after_agent, speaker="Red")
    ai_with_tools = AIMessage(
        content="",
        tool_calls=[{"name": "wikipedia_search", "args": {"query": "AI"}, "id": "1"}],
    )
    assert route(_state(turn_messages=[ai_with_tools])) == "wikipedia_tool"


def test_route_after_agent_with_final_text_goes_to_finish() -> None:
    route = partial(_route_after_agent, speaker="Red")
    ai_text = AIMessage(content="Final argument.")
    assert route(_state(turn_messages=[ai_text])) == "debater_red_finish"


def test_route_after_agent_respects_loop_cap() -> None:
    route = partial(_route_after_agent, speaker="Green")
    ai_with_tools = AIMessage(
        content="",
        tool_calls=[{"name": "wikipedia_search", "args": {"query": "AI"}, "id": "1"}],
    )
    state = _state(turn_messages=[ai_with_tools], tool_loop_count=3)
    assert route(state) == "debater_green_finish"


def test_route_after_agent_blocks_wikipedia_on_later_turn() -> None:
    route = partial(_route_after_agent, speaker="Red")
    ai_with_tools = AIMessage(
        content="",
        tool_calls=[{"name": "wikipedia_search", "args": {"query": "AI"}, "id": "1"}],
    )
    state = _state(
        turn_red=1,
        turn_messages=[ai_with_tools],
        wikipedia_turn_red=1,
    )
    assert route(state) == "debater_red_finish"


def test_route_after_agent_allows_wikipedia_on_chosen_turn() -> None:
    route = partial(_route_after_agent, speaker="Red")
    ai_with_tools = AIMessage(
        content="",
        tool_calls=[{"name": "wikipedia_search", "args": {"query": "AI"}, "id": "1"}],
    )
    state = _state(
        turn_red=1,
        turn_messages=[ai_with_tools],
        wikipedia_turn_red=2,
        tool_loop_count=1,
    )
    assert route(state) == "wikipedia_tool"


def test_route_after_tool_returns_active_speaker_agent() -> None:
    assert (
        _route_after_tool(_state(active_speaker="Red"))
        == "debater_red_agent"
    )
    assert (
        _route_after_tool(_state(active_speaker="Green"))
        == "debater_green_agent"
    )


def test_route_after_red_finish_alternates_to_green() -> None:
    route = partial(_route_after_finish, from_speaker="red")
    assert route(_state(turn_red=1, turn_green=0)) == "debater_green_agent"


def test_route_after_green_finish_alternates_to_red() -> None:
    route = partial(_route_after_finish, from_speaker="green")
    assert route(_state(turn_red=1, turn_green=1)) == "debater_red_agent"


def test_route_to_summarizer_when_both_debaters_finished() -> None:
    red_route = partial(_route_after_finish, from_speaker="red")
    green_route = partial(_route_after_finish, from_speaker="green")
    finished = _state(turn_red=3, turn_green=3)
    assert red_route(finished) == "summarizer"
    assert green_route(finished) == "summarizer"


def test_graph_invoke_produces_seven_ai_messages() -> None:
    graph = build_debate_graph()
    result = graph.invoke(build_initial_state("Should AI replace teachers?"))

    assert result["turn_red"] == 3
    assert result["turn_green"] == 3
    assert result["phase"] == "completed"
    assert result["turn_messages"] == []
    assert result["active_speaker"] is None
    assert result["pending_tool_query"] is None
    assert result["tool_loop_count"] == 0

    messages = result["messages"]
    assert len(messages) == 7

    speakers: list[str | None] = [
        msg.name if isinstance(msg, AIMessage) else None for msg in messages
    ]
    assert speakers == ["Red", "Green", "Red", "Green", "Red", "Green", "Summarizer"]

    expected_order: list[Literal["Red", "Green", "Summarizer"]] = [
        "Red",
        "Green",
        "Red",
        "Green",
        "Red",
        "Green",
        "Summarizer",
    ]
    for message, expected in zip(messages, expected_order, strict=True):
        assert isinstance(message, AIMessage)
        assert message.name == expected
