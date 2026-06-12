from typing import Any

import pytest
from langchain_core.messages import AIMessage, RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES

from debate.initial_state import build_initial_state
from debate.nodes.debater_green import (
    debater_green_agent_node,
)
from debate.nodes.debater_red import debater_red_agent_node, debater_red_finish_node
from debate.nodes.message_utils import message_text
from debate.nodes.summarizer import summarizer_node
from debate.state import DebateState


class RecordingAgent:
    def __init__(self, responses: list[AIMessage] | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.respond_calls: list[dict[str, Any]] = []
        self.responses = responses or [
            AIMessage(content="agent response", name="Red"),
        ]
        self._call_index = 0

    def invoke_turn(
        self, turn_messages: list[Any], **kwargs: Any
    ) -> tuple[list[AIMessage], AIMessage]:
        self.calls.append({"turn_messages": turn_messages, "kwargs": kwargs})
        response = self.responses[min(self._call_index, len(self.responses) - 1)]
        self._call_index += 1
        return [response], response

    def respond(self, *args: Any, **kwargs: Any) -> str:
        self.respond_calls.append({"args": args, "kwargs": kwargs})
        return "agent response"


@pytest.fixture
def recording_agents(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[RecordingAgent, RecordingAgent, RecordingAgent]:
    red = RecordingAgent()
    green = RecordingAgent([AIMessage(content="agent response", name="Green")])
    summarizer = RecordingAgent([AIMessage(content="summary", name="Summarizer")])

    monkeypatch.setattr("debate.nodes.debater_red.get_debater_red", lambda: red)
    monkeypatch.setattr("debate.nodes.debater_green.get_debater_green", lambda: green)
    monkeypatch.setattr("debate.nodes.summarizer.get_summarizer", lambda: summarizer)

    return red, green, summarizer


def test_debater_red_agent_node_seeds_turn_messages(
    recording_agents: tuple[RecordingAgent, RecordingAgent, RecordingAgent],
) -> None:
    red, _, _ = recording_agents
    state = build_initial_state("Test topic")

    update = debater_red_agent_node(state)

    assert update.get("active_speaker") == "Red"
    assert update.get("tool_loop_count") == 0
    turn_messages = update.get("turn_messages")
    assert turn_messages is not None
    assert len(turn_messages) == 1
    message = turn_messages[0]
    assert isinstance(message, AIMessage)
    assert message_text(message) == "agent response"
    assert red.calls == [
        {
            "turn_messages": [],
            "kwargs": {
                "topic": "Test topic",
                "context": "(no prior arguments yet)",
                "turn": 1,
                "is_opening": True,
                "first_call": True,
                "wikipedia_turn": None,
            },
        }
    ]


def test_debater_red_finish_node_commits_message_and_clears_turn_state(
    recording_agents: tuple[RecordingAgent, RecordingAgent, RecordingAgent],
) -> None:
    state: DebateState = {
        **build_initial_state("Test topic"),
        "turn_messages": [AIMessage(content="final turn text")],
        "active_speaker": "Red",
        "tool_loop_count": 1,
        "pending_tool_query": "renewable energy",
    }

    update = debater_red_finish_node(state)

    assert update.get("turn_red") == 1
    cleared_turn_messages = update.get("turn_messages")
    assert cleared_turn_messages is not None
    assert len(cleared_turn_messages) == 1
    assert isinstance(cleared_turn_messages[0], RemoveMessage)
    assert cleared_turn_messages[0].id == REMOVE_ALL_MESSAGES
    assert update.get("tool_loop_count") == 0
    assert update.get("pending_tool_query") is None
    assert update.get("active_speaker") is None
    messages = update.get("messages")
    assert messages is not None
    message = messages[0]
    assert isinstance(message, AIMessage)
    assert message.name == "Red"
    assert message_text(message) == "final turn text"


def test_debater_green_agent_node_uses_rebuttal_on_first_turn(
    recording_agents: tuple[RecordingAgent, RecordingAgent, RecordingAgent],
) -> None:
    _, green, _ = recording_agents
    state: DebateState = {
        **build_initial_state("Test topic"),
        "messages": [AIMessage(content="Red opening.", name="Red")],
        "turn_red": 1,
    }

    update = debater_green_agent_node(state)

    assert update.get("active_speaker") == "Green"
    assert green.calls == [
        {
            "turn_messages": [],
            "kwargs": {
                "topic": "Test topic",
                "context": "Red (turn 1): Red opening.",
                "turn": 1,
                "is_opening": False,
                "first_call": True,
                "wikipedia_turn": None,
            },
        }
    ]


def test_debater_red_agent_node_sets_wikipedia_turn_on_first_tool_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool_response = AIMessage(
        content="",
        tool_calls=[
            {"name": "wikipedia_search", "args": {"query": "climate change"}, "id": "1"}
        ],
    )
    red = RecordingAgent([tool_response])
    monkeypatch.setattr("debate.nodes.debater_red.get_debater_red", lambda: red)

    update = debater_red_agent_node(build_initial_state("Test topic"))

    assert update.get("pending_tool_query") == "climate change"
    assert update.get("wikipedia_turn_red") == 1


def test_debater_red_agent_node_passes_wikipedia_turn_to_invoke(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    red = RecordingAgent([AIMessage(content="after prior wiki use")])
    monkeypatch.setattr("debate.nodes.debater_red.get_debater_red", lambda: red)
    state: DebateState = {
        **build_initial_state("Test topic"),
        "turn_red": 2,
        "wikipedia_turn_red": 1,
    }

    debater_red_agent_node(state)

    assert red.calls[0]["kwargs"]["wikipedia_turn"] == 1
    assert red.calls[0]["kwargs"]["turn"] == 3


def test_debater_red_agent_node_sets_pending_tool_query_for_tool_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool_response = AIMessage(
        content="",
        tool_calls=[
            {"name": "wikipedia_search", "args": {"query": "climate change"}, "id": "1"}
        ],
    )
    red = RecordingAgent([tool_response])
    monkeypatch.setattr("debate.nodes.debater_red.get_debater_red", lambda: red)
    state: DebateState = {
        **build_initial_state("Test topic"),
        "wikipedia_turn_red": 1,
    }

    update = debater_red_agent_node(state)

    assert update.get("pending_tool_query") == "climate change"
    assert "wikipedia_turn_red" not in update


def test_debater_red_agent_node_increments_tool_loop_on_reentry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    red = RecordingAgent([AIMessage(content="after tool")])
    monkeypatch.setattr("debate.nodes.debater_red.get_debater_red", lambda: red)
    state: DebateState = {
        **build_initial_state("Test topic"),
        "turn_messages": [AIMessage(content="tool call")],
        "tool_loop_count": 1,
    }

    update = debater_red_agent_node(state)

    assert update.get("tool_loop_count") == 2


def test_summarizer_node_sets_completed_phase(
    recording_agents: tuple[RecordingAgent, RecordingAgent, RecordingAgent],
) -> None:
    _, _, summarizer = recording_agents
    state: DebateState = {
        **build_initial_state("Test topic"),
        "messages": [
            AIMessage(content="Red point.", name="Red"),
            AIMessage(content="Green point.", name="Green"),
        ],
        "turn_red": 1,
        "turn_green": 1,
    }

    update = summarizer_node(state)

    assert update.get("phase") == "completed"
    messages = update.get("messages")
    assert messages is not None
    message = messages[0]
    assert isinstance(message, AIMessage)
    assert message.name == "Summarizer"
    assert summarizer.respond_calls == [
        {
            "args": (
                "Test topic",
                "Red (turn 1): Red point.\nGreen (turn 1): Green point.",
            ),
            "kwargs": {},
        }
    ]
