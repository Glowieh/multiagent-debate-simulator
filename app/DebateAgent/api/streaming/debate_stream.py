import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any, cast

from fastapi import Request
from sse_starlette import JSONServerSentEvent

from api.schemas.debate import DebateEvent
from api.streaming.event_mapper import DebateEventMapper
from debate.graph import get_graph
from debate.initial_state import build_initial_state

logger = logging.getLogger(__name__)


def _to_sse(event: DebateEvent, event_id: int) -> JSONServerSentEvent:
    return JSONServerSentEvent(data=event.model_dump(), id=str(event_id), sep="\n")


async def iter_debate_events(
    topic: str,
    is_disconnected: Callable[[], Awaitable[bool]] | None = None,
) -> AsyncIterator[DebateEvent]:
    mapper = DebateEventMapper(topic=topic)
    graph = get_graph()
    initial_state = build_initial_state(topic)

    stream = graph.astream_events(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        initial_state,
        version="v2",
    )
    completed_normally = False

    try:
        async for graph_event in stream:
            if is_disconnected is not None and await is_disconnected():
                logger.info("Client disconnected from debate stream")
                break

            for debate_event in mapper.map_langgraph_event(
                cast(dict[str, Any], graph_event)
            ):
                yield debate_event
        else:
            completed_normally = True
    except Exception:
        logger.exception("Debate stream failed")
        for debate_event in mapper.error_events("Debate stream failed"):
            yield debate_event
    finally:
        close = getattr(stream, "aclose", None)
        if close is not None:
            await close()

    if completed_normally:
        for debate_event in mapper.completion_events():
            yield debate_event


async def debate_event_generator(
    request: Request, topic: str
) -> AsyncIterator[JSONServerSentEvent]:
    event_id = 0
    async for debate_event in iter_debate_events(
        topic, is_disconnected=request.is_disconnected
    ):
        event_id += 1
        yield _to_sse(debate_event, event_id)
