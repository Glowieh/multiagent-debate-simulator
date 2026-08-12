from langchain_core.messages import AIMessage

from debate.agents import instances
from debate.state import DebateState, DebateStateUpdate
from debate.transcript import format_debate_transcript


def summarizer_node(state: DebateState) -> DebateStateUpdate:
    transcript = format_debate_transcript(state["messages"])
    content = instances.get_summarizer().invoke_summary(state["topic"], transcript)
    return {
        "messages": [AIMessage(content=content, name="Summarizer")],
    }
