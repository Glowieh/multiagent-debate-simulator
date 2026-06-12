from typing import Any

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from debate.agents.debater_green import DebaterGreen
from debate.agents.debater_red import DebaterRed
from debate.agents.summarizer import Summarizer


class RecordingChain:
    def __init__(self) -> None:
        self.last_input: dict[str, Any] | None = None

    def invoke(self, inputs: dict[str, Any]) -> str:
        self.last_input = inputs
        return "recorded response"


class RecordingToolModel:
    def __init__(self, responses: list[AIMessage] | None = None) -> None:
        self.responses = responses or [AIMessage(content="tool-aware response")]
        self.invoke_calls: list[list[Any]] = []
        self.bind_tools_called = False
        self._call_index = 0

    def bind_tools(self, tools: list[Any]) -> "RecordingToolModel":
        self.bind_tools_called = True
        return self

    def invoke(self, messages: list[Any]) -> AIMessage:
        self.invoke_calls.append(messages)
        response = self.responses[min(self._call_index, len(self.responses) - 1)]
        self._call_index += 1
        return response


@pytest.fixture
def recording_chains(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[RecordingChain, RecordingChain]:
    opening = RecordingChain()
    rebuttal = RecordingChain()

    def fake_build_chain(system_prompt: str, human_template: str) -> RecordingChain:
        if "opening statement" in human_template:
            return opening
        return rebuttal

    monkeypatch.setattr("debate.agents.base.BaseAgent._build_chain", fake_build_chain)
    return opening, rebuttal


@pytest.fixture
def recording_default_chain(monkeypatch: pytest.MonkeyPatch) -> RecordingChain:
    default = RecordingChain()

    def fake_build_chain(system_prompt: str, human_template: str) -> RecordingChain:
        return default

    monkeypatch.setattr("debate.agents.base.BaseAgent._build_chain", fake_build_chain)
    return default


@pytest.fixture
def recording_tool_model(monkeypatch: pytest.MonkeyPatch) -> RecordingToolModel:
    model = RecordingToolModel()

    def fake_load_model() -> RecordingToolModel:
        return model

    monkeypatch.setattr("debate.agents.base.load_model", fake_load_model)
    return model


def test_debater_red_build_turn_messages_uses_opening_template() -> None:
    agent = DebaterRed()
    messages = agent.build_turn_messages(
        "Topic", "Context", turn=1, is_opening=True
    )

    assert len(messages) == 2
    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[1], HumanMessage)
    assert "opening statement" in str(messages[1].content)


def test_debater_red_build_turn_messages_appends_wikipedia_available_instruction() -> None:
    agent = DebaterRed()
    messages = agent.build_turn_messages(
        "Topic", "Context", turn=2, is_opening=False
    )

    assert "save your Wikipedia lookup for a later turn" in str(messages[1].content)


def test_debater_red_build_turn_messages_appends_wikipedia_exhausted_instruction() -> None:
    agent = DebaterRed()
    messages = agent.build_turn_messages(
        "Topic", "Context", turn=3, is_opening=False, wikipedia_turn=1
    )

    assert "already used your Wikipedia lookup" in str(messages[1].content)


def test_debater_red_build_turn_messages_uses_rebuttal_on_turn_three() -> None:
    agent = DebaterRed()
    messages = agent.build_turn_messages(
        "Topic", "Context", turn=3, is_opening=False, wikipedia_turn=3
    )

    assert "Respond directly to your opponent" in str(messages[1].content)
    assert "already used your Wikipedia lookup" not in str(messages[1].content)


def test_invoke_turn_returns_ai_message(
    recording_tool_model: RecordingToolModel,
) -> None:
    agent = DebaterRed()
    turn_update, response = agent.invoke_turn(
        [],
        topic="Topic",
        context="Context",
        turn=1,
        is_opening=True,
        first_call=True,
    )

    assert isinstance(response, AIMessage)
    assert response.content == "tool-aware response"
    assert recording_tool_model.bind_tools_called is True
    assert len(recording_tool_model.invoke_calls) == 1
    assert len(turn_update) == 3
    assert isinstance(turn_update[0], SystemMessage)
    assert isinstance(turn_update[1], HumanMessage)
    assert isinstance(turn_update[2], AIMessage)


def test_invoke_turn_skips_tool_binding_when_wikipedia_exhausted(
    recording_tool_model: RecordingToolModel,
) -> None:
    agent = DebaterRed()
    agent.invoke_turn(
        [],
        topic="Topic",
        context="Context",
        turn=3,
        is_opening=False,
        first_call=True,
        wikipedia_turn=1,
    )

    assert recording_tool_model.bind_tools_called is False


def test_invoke_turn_reuses_existing_turn_messages_on_reentry(
    recording_tool_model: RecordingToolModel,
) -> None:
    agent = DebaterGreen()
    prior = [
        SystemMessage(content=agent.system_prompt),
        HumanMessage(content="turn prompt"),
        AIMessage(content="prior"),
        HumanMessage(content="tool result"),
    ]

    agent.invoke_turn(
        prior,
        topic="Topic",
        context="Context",
        turn=2,
        is_opening=False,
        first_call=False,
        wikipedia_turn=2,
    )

    assert recording_tool_model.invoke_calls[0] == prior


def test_invoke_turn_prepends_system_prompt_after_tool_on_reentry(
    recording_tool_model: RecordingToolModel,
) -> None:
    agent = DebaterRed()
    prior = [
        AIMessage(content="", tool_calls=[{"name": "wikipedia_search", "args": {}, "id": "1"}]),
        HumanMessage(content="Wikipedia summary"),
    ]

    agent.invoke_turn(
        prior,
        topic="Topic",
        context="Context",
        turn=2,
        is_opening=False,
        first_call=False,
        wikipedia_turn=2,
    )

    sent = recording_tool_model.invoke_calls[0]
    assert isinstance(sent[0], SystemMessage)
    assert agent.system_prompt in str(sent[0].content)
    assert isinstance(sent[1], HumanMessage)
    assert "Respond directly to your opponent" in str(sent[1].content)
    assert sent[2:] == prior


def test_summarizer_uses_default_chain(recording_default_chain: RecordingChain) -> None:
    agent = Summarizer()
    agent.respond("Topic", "Transcript")

    assert recording_default_chain.last_input == {
        "topic": "Topic",
        "context": "Transcript",
        "turn": 0,
    }
