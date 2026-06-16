from langchain_core.messages import AIMessage, BaseMessage

from debate.nodes.message_utils import final_text_from_message


def _speaker_label(message: BaseMessage) -> str | None:
    if not isinstance(message, AIMessage):
        return None
    name = message.name
    # Message names use PascalCase ("Summarizer"); stream events use "summarizer".
    if name in {"Red", "Green", "Summarizer"}:
        return name
    return "Unknown"


def format_debate_transcript(messages: list[BaseMessage]) -> str:
    speaker_turn_counts: dict[str, int] = {}
    transcript_lines: list[str] = []

    for message in messages:
        speaker = _speaker_label(message)
        if speaker is None:
            continue
        speaker_turn_counts[speaker] = speaker_turn_counts.get(speaker, 0) + 1
        turn = speaker_turn_counts[speaker]
        transcript_lines.append(
            f"{speaker} (turn {turn}): {final_text_from_message(message)}"
        )

    if transcript_lines:
        return "\n".join(transcript_lines)
    return "(no prior arguments yet)"
