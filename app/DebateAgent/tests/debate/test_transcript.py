from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from debate.transcript import format_debate_transcript


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


def test_format_debate_transcript_skips_unknown_speaker_names() -> None:
    messages: list[BaseMessage] = [
        AIMessage(content="Orphan tool reply.", name="tool"),
        AIMessage(content="Against argument one.", name="Red"),
        AIMessage(content="Nameless AI."),
    ]
    result = format_debate_transcript(messages)
    assert result == "Red (turn 1): Against argument one."
