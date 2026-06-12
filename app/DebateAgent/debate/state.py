from typing import Annotated, Literal, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


# full state
class DebateState(TypedDict):
    topic: str
    messages: Annotated[list[BaseMessage], add_messages]
    turn_red: int
    turn_green: int
    phase: Literal["debating", "completed"]
    turn_messages: Annotated[list[BaseMessage], add_messages]
    active_speaker: Literal["Red", "Green"] | None
    pending_tool_query: str | None
    tool_loop_count: int
    wikipedia_turn_red: int | None
    wikipedia_turn_green: int | None


# optional fields since nodes return partial updates
class DebateStateUpdate(TypedDict, total=False):
    topic: str
    messages: Annotated[list[BaseMessage], add_messages]
    turn_red: int
    turn_green: int
    phase: Literal["debating", "completed"]
    turn_messages: Annotated[list[BaseMessage], add_messages]
    active_speaker: Literal["Red", "Green"] | None
    pending_tool_query: str | None
    tool_loop_count: int
    wikipedia_turn_red: int | None
    wikipedia_turn_green: int | None
