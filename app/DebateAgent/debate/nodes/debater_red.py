from typing import Any

from langchain_core.messages import AIMessage, RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES, BaseMessage

from debate.agents.instances import get_debater_red
from debate.context import format_debate_transcript
from debate.state import DebateState, DebateStateUpdate


def _extract_query(tool_call: dict[str, Any]) -> str:
    args = tool_call.get("args", {})
    if isinstance(args, dict):
        query = args.get("query")
        if query is not None:
            return str(query)
    return ""


def _final_text(message: BaseMessage) -> str:
    if isinstance(message, AIMessage):
        content = message.content
        if isinstance(content, str):
            return content
    return str(getattr(message, "content", ""))


def debater_red_agent_node(state: DebateState) -> DebateStateUpdate:
    turn = state["turn_red"] + 1
    first_call = len(state["turn_messages"]) == 0
    transcript = format_debate_transcript(state["messages"])
    is_opening = len(state["messages"]) == 0
    turn_update, response = get_debater_red().invoke_turn(
        state["turn_messages"],
        topic=state["topic"],
        context=transcript,
        turn=turn,
        is_opening=is_opening,
        first_call=first_call,
        wikipedia_turn=state["wikipedia_turn_red"],
    )
    update: DebateStateUpdate = {
        "turn_messages": turn_update,
        "active_speaker": "Red",
        "tool_loop_count": state["tool_loop_count"] + (0 if first_call else 1),
    }
    if response.tool_calls:
        update["pending_tool_query"] = _extract_query(response.tool_calls[0])
        if state["wikipedia_turn_red"] is None:
            update["wikipedia_turn_red"] = turn
    return update


def _clear_turn_messages() -> list[RemoveMessage]:
    return [RemoveMessage(id=REMOVE_ALL_MESSAGES)]


def debater_red_finish_node(state: DebateState) -> DebateStateUpdate:
    content = _final_text(state["turn_messages"][-1])
    return {
        "messages": [AIMessage(content=content, name="Red")],
        "turn_red": state["turn_red"] + 1,
        "turn_messages": _clear_turn_messages(),
        "tool_loop_count": 0,
        "pending_tool_query": None,
        "active_speaker": None,
    }
