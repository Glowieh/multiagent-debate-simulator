from functools import partial
from typing import Literal

from langchain_core.messages import AIMessage

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from debate.nodes.debater_green import debater_green_agent_node, debater_green_finish_node
from debate.nodes.debater_red import debater_red_agent_node, debater_red_finish_node
from debate.nodes.summarizer import summarizer_node
from debate.nodes.wikipedia_tool import wikipedia_tool_node
from debate.settings import get_settings
from debate.state import DebateState
from debate.wikipedia_limits import wikipedia_allowed

_graph: CompiledStateGraph[DebateState, None, DebateState, DebateState] | None = None


def _debate_complete(state: DebateState) -> bool:
    max_turns = get_settings().max_turns_per_debater
    return state["turn_red"] >= max_turns and state["turn_green"] >= max_turns


def _route_after_agent(
    state: DebateState,
    speaker: Literal["Red", "Green"],
) -> Literal["wikipedia_tool", "debater_red_finish", "debater_green_finish"]:
    last = state["turn_messages"][-1]
    max_loops = get_settings().max_tool_loops
    turn_key = "turn_red" if speaker == "Red" else "turn_green"
    current_turn = state[turn_key] + 1
    if (
        isinstance(last, AIMessage)
        and last.tool_calls
        and state["tool_loop_count"] < max_loops
        and wikipedia_allowed(state, speaker, current_turn)
    ):
        return "wikipedia_tool"
    finish_node = (
        "debater_red_finish" if speaker == "Red" else "debater_green_finish"
    )
    return finish_node


def _route_after_tool(
    state: DebateState,
) -> Literal["debater_red_agent", "debater_green_agent"]:
    if state["active_speaker"] == "Red":
        return "debater_red_agent"
    return "debater_green_agent"


def _route_after_finish(
    state: DebateState,
    from_speaker: Literal["red", "green"],
) -> Literal["debater_red_agent", "debater_green_agent", "summarizer"]:
    if _debate_complete(state):
        return "summarizer"
    return "debater_green_agent" if from_speaker == "red" else "debater_red_agent"


def build_debate_graph() -> CompiledStateGraph[
    DebateState, None, DebateState, DebateState
]:
    workflow = StateGraph(DebateState)
    workflow.add_node("debater_red_agent", debater_red_agent_node)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
    workflow.add_node("debater_red_finish", debater_red_finish_node)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
    workflow.add_node("debater_green_agent", debater_green_agent_node)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
    workflow.add_node("debater_green_finish", debater_green_finish_node)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
    workflow.add_node("wikipedia_tool", wikipedia_tool_node)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
    workflow.add_node("summarizer", summarizer_node)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]

    workflow.add_edge(START, "debater_red_agent")
    workflow.add_conditional_edges(
        "debater_red_agent", partial(_route_after_agent, speaker="Red")
    )
    workflow.add_conditional_edges(
        "debater_green_agent", partial(_route_after_agent, speaker="Green")
    )
    workflow.add_conditional_edges("wikipedia_tool", _route_after_tool)
    workflow.add_conditional_edges(
        "debater_red_finish", partial(_route_after_finish, from_speaker="red")
    )
    workflow.add_conditional_edges(
        "debater_green_finish", partial(_route_after_finish, from_speaker="green")
    )
    workflow.add_edge("summarizer", END)

    return workflow.compile()  # pyright: ignore[reportUnknownMemberType]


def get_graph() -> CompiledStateGraph[DebateState, None, DebateState, DebateState]:
    global _graph
    if _graph is None:
        _graph = build_debate_graph()
    return _graph
