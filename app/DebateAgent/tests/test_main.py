import asyncio
from collections.abc import AsyncIterator, Callable
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.schemas.debate import DebateCompletedEvent, DebateStartedEvent


async def _collect_events(
    payload: dict[str, Any],
    *,
    request: object | None = None,
) -> list[dict[str, Any]]:
    import main

    context = MagicMock()
    context.request = request

    invoke = cast(
        Callable[
            [dict[str, Any], object],
            AsyncIterator[dict[str, Any]],
        ],
        main.invoke,  # pyright: ignore[reportUnknownMemberType]
    )

    events: list[dict[str, Any]] = []
    async for event in invoke(payload, context):
        events.append(event)
    return events


@pytest.mark.asyncio
async def test_invoke_empty_topic_yields_error_and_completed() -> None:
    events = await _collect_events({"topic": "   "})

    assert events == [
        {"type": "error", "message": "Topic cannot be empty"},
        {"type": "debate_completed"},
    ]


@pytest.mark.asyncio
async def test_invoke_valid_topic_yields_mocked_events() -> None:
    async def mock_iter(
        topic: str,
        is_disconnected: object | None = None,
    ) -> AsyncIterator[DebateStartedEvent | DebateCompletedEvent]:
        yield DebateStartedEvent(topic=topic)
        yield DebateCompletedEvent()

    with patch("main.iter_debate_events", side_effect=mock_iter):
        events = await _collect_events({"topic": "Should AI replace teachers?"})

    assert events == [
        {"type": "debate_started", "topic": "Should AI replace teachers?"},
        {"type": "debate_completed"},
    ]


@pytest.mark.asyncio
async def test_invoke_passes_disconnect_callback_when_request_set() -> None:
    captured: dict[str, object] = {}

    async def mock_iter(
        topic: str,
        is_disconnected: object | None = None,
    ) -> AsyncIterator[DebateCompletedEvent]:
        captured["topic"] = topic
        captured["is_disconnected"] = is_disconnected
        yield DebateCompletedEvent()

    request = MagicMock()
    request.is_disconnected = AsyncMock(return_value=False)

    with patch("main.iter_debate_events", side_effect=mock_iter):
        await _collect_events({"topic": "Disconnect wiring"}, request=request)

    assert captured["topic"] == "Disconnect wiring"
    assert captured["is_disconnected"] is request.is_disconnected


@pytest.mark.asyncio
async def test_invoke_re_raises_cancelled_error() -> None:
    async def mock_iter(
        topic: str,
        is_disconnected: object | None = None,
    ) -> AsyncIterator[DebateStartedEvent]:
        yield DebateStartedEvent(topic=topic)
        raise asyncio.CancelledError

    with patch("main.iter_debate_events", side_effect=mock_iter):
        with pytest.raises(asyncio.CancelledError):
            await _collect_events({"topic": "Cancel case"})
