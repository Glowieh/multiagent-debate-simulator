from collections.abc import AsyncIterator

from fastapi import Request
from sse_starlette import JSONServerSentEvent

from api.schemas.debate import DebateEvent
from api.streaming.iter_debate_events import iter_debate_events

__all__ = ["debate_event_generator", "iter_debate_events"]


def _to_sse(event: DebateEvent, event_id: int) -> JSONServerSentEvent:
    return JSONServerSentEvent(data=event.model_dump(), id=str(event_id), sep="\n")


async def debate_event_generator(
    request: Request, topic: str
) -> AsyncIterator[JSONServerSentEvent]:
    event_id = 0
    async for debate_event in iter_debate_events(
        topic, is_disconnected=request.is_disconnected
    ):
        event_id += 1
        yield _to_sse(debate_event, event_id)
