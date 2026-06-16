from typing import Literal

from pydantic import BaseModel, Field, field_validator

from debate.topic import MAX_TOPIC_LENGTH, TopicValidationError, normalize_topic


class DebateRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=MAX_TOPIC_LENGTH)

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, value: str) -> str:
        try:
            return normalize_topic(value)
        except TopicValidationError as exc:
            raise ValueError(str(exc)) from exc


class DebateStartedEvent(BaseModel):
    type: Literal["debate_started"] = "debate_started"
    topic: str


class TurnStartedEvent(BaseModel):
    type: Literal["turn_started"] = "turn_started"
    speaker: Literal["Red", "Green"]
    turn: int


class MessageChunkEvent(BaseModel):
    type: Literal["message_chunk"] = "message_chunk"
    speaker: Literal["Red", "Green", "summarizer"]
    content: str


class TurnCompletedEvent(BaseModel):
    type: Literal["turn_completed"] = "turn_completed"
    speaker: Literal["Red", "Green"]
    turn: int


class ToolCallStartedEvent(BaseModel):
    type: Literal["tool_call_started"] = "tool_call_started"
    speaker: Literal["Red", "Green"]
    tool: Literal["wikipedia_search"] = "wikipedia_search"
    query: str


class ToolCallCompletedEvent(BaseModel):
    type: Literal["tool_call_completed"] = "tool_call_completed"
    speaker: Literal["Red", "Green"]
    tool: Literal["wikipedia_search"] = "wikipedia_search"
    query: str


class SummaryEvent(BaseModel):
    type: Literal["summary"] = "summary"
    content: str


class DebateCompletedEvent(BaseModel):
    type: Literal["debate_completed"] = "debate_completed"


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str


DebateEvent = (
    DebateStartedEvent
    | TurnStartedEvent
    | MessageChunkEvent
    | TurnCompletedEvent
    | ToolCallStartedEvent
    | ToolCallCompletedEvent
    | SummaryEvent
    | DebateCompletedEvent
    | ErrorEvent
)
