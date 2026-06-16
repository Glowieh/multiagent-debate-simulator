import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any, cast

from api.schemas.debate import DebateEvent
from api.streaming.event_mapper import DebateEventMapper
from debate.graph import get_graph
from debate.initial_state import build_initial_state

logger = logging.getLogger(__name__)


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
