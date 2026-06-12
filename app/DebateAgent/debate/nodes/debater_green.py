from langchain_core.messages import AIMessage

from debate.agents.instances import get_debater_green
from debate.context import format_debate_transcript
from debate.nodes.debater_red import _clear_turn_messages, _extract_query, _final_text
from debate.state import DebateState, DebateStateUpdate


def debater_green_agent_node(state: DebateState) -> DebateStateUpdate:
    turn = state["turn_green"] + 1
    first_call = len(state["turn_messages"]) == 0
    transcript = format_debate_transcript(state["messages"])
    is_opening = len(state["messages"]) == 0
    turn_update, response = get_debater_green().invoke_turn(
        state["turn_messages"],
        topic=state["topic"],
        context=transcript,
        turn=turn,
        is_opening=is_opening,
        first_call=first_call,
        wikipedia_turn=state["wikipedia_turn_green"],
    )
    update: DebateStateUpdate = {
        "turn_messages": turn_update,
        "active_speaker": "Green",
        "tool_loop_count": state["tool_loop_count"] + (0 if first_call else 1),
    }
    if response.tool_calls:
        update["pending_tool_query"] = _extract_query(response.tool_calls[0])
        if state["wikipedia_turn_green"] is None:
            update["wikipedia_turn_green"] = turn
    return update


def debater_green_finish_node(state: DebateState) -> DebateStateUpdate:
    content = _final_text(state["turn_messages"][-1])
    return {
        "messages": [AIMessage(content=content, name="Green")],
        "turn_green": state["turn_green"] + 1,
        "turn_messages": _clear_turn_messages(),
        "tool_loop_count": 0,
        "pending_tool_query": None,
        "active_speaker": None,
    }
