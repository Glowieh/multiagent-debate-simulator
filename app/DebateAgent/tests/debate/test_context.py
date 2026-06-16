from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from debate.context import format_debate_transcript
from debate.initial_state import build_initial_state


def test_format_debate_transcript_empty() -> None:
    result = format_debate_transcript([])
    assert result == "(no prior arguments yet)"


def test_format_debate_transcript_labeled_messages_with_turn_numbers() -> None:
    messages: list[BaseMessage] = [
        AIMessage(content="Against argument one.", name="Red"),
        AIMessage(content="For argument one.", name="Green"),
        AIMessage(content="Against rebuttal.", name="Red"),
    ]
    result = format_debate_transcript(messages)
    assert result == (
        "Red (turn 1): Against argument one.\n"
        "Green (turn 1): For argument one.\n"
        "Red (turn 2): Against rebuttal."
    )


def test_format_debate_transcript_skips_unlabeled_messages() -> None:
    messages: list[BaseMessage] = [
        HumanMessage(content="Should AI replace teachers?"),
        AIMessage(content="Against argument one.", name="Red"),
    ]
    result = format_debate_transcript(messages)
    assert "human:" not in result
    assert result == "Red (turn 1): Against argument one."


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
