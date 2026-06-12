from typing import cast

from langchain_core.messages import AIMessage

from debate.agents.instances import get_debater_red
from debate.context import format_debate_transcript
from debate.nodes.message_utils import (
    clear_turn_messages,
    extract_query_from_tool_call,
    final_text_from_message,
)
from debate.state import DebateState, DebateStateUpdate


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
        update["pending_tool_query"] = extract_query_from_tool_call(
            response.tool_calls[0]
        )
        if state["wikipedia_turn_red"] is None:
            update["wikipedia_turn_red"] = turn
    return update


def debater_red_finish_node(state: DebateState) -> DebateStateUpdate:
    content = final_text_from_message(state["turn_messages"][-1])
    return cast(
        DebateStateUpdate,
        {
            "messages": [AIMessage(content=content, name="Red")],
            "turn_red": state["turn_red"] + 1,
            "turn_messages": clear_turn_messages(),
            "tool_loop_count": 0,
            "pending_tool_query": None,
            "active_speaker": None,
        },
    )
