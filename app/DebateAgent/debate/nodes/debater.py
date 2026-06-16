from collections.abc import Callable
from typing import Literal, cast

from langchain_core.messages import AIMessage

from debate.agents.base import DebaterAgent
from debate.context import format_debate_transcript
from debate.nodes.message_utils import (
    clear_turn_messages,
    final_text_from_message,
    final_turn_content,
)
from debate.settings import get_settings
from debate.state import DebateState, DebateStateUpdate


def make_debater_nodes(
    speaker: Literal["Red", "Green"],
    get_agent: Callable[[], DebaterAgent],
    turn_key: Literal["turn_red", "turn_green"],
    wikipedia_key: Literal["wikipedia_turn_red", "wikipedia_turn_green"],
) -> tuple[
    Callable[[DebateState], DebateStateUpdate],
    Callable[[DebateState], DebateStateUpdate],
]:
    def agent_node(state: DebateState) -> DebateStateUpdate:
        turn = state[turn_key] + 1
        first_call = len(state["turn_messages"]) == 0
        transcript = format_debate_transcript(state["messages"])
        is_debate_opening = len(state["messages"]) == 0
        force_final = False
        if not first_call and state["turn_messages"]:
            last = state["turn_messages"][-1]
            force_final = (
                isinstance(last, AIMessage)
                and bool(last.tool_calls)
                and not final_text_from_message(last).strip()
                and state["tool_loop_count"] >= get_settings().max_tool_loops
            )
        turn_update, _response = get_agent().invoke_turn(
            state["turn_messages"],
            topic=state["topic"],
            context=transcript,
            turn=turn,
            is_debate_opening=is_debate_opening,
            first_call=first_call,
            wikipedia_turn=state[wikipedia_key],
            force_final=force_final,
        )
        update: DebateStateUpdate = {
            "turn_messages": turn_update,
            "active_speaker": speaker,
            "tool_loop_count": state["tool_loop_count"] + (0 if first_call else 1),
        }
        last = turn_update[-1] if turn_update else None
        if (
            isinstance(last, AIMessage)
            and last.tool_calls
            and state[wikipedia_key] is None
        ):
            update[wikipedia_key] = turn
        return update

    def finish_node(state: DebateState) -> DebateStateUpdate:
        content = final_turn_content(state["turn_messages"])
        return cast(
            DebateStateUpdate,
            {
                "messages": [AIMessage(content=content, name=speaker)],
                turn_key: state[turn_key] + 1,
                "turn_messages": clear_turn_messages(),
                "tool_loop_count": 0,
                "active_speaker": None,
            },
        )

    return agent_node, finish_node
