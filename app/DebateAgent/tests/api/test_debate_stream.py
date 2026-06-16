import json
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

import api.streaming.iter_debate_events as iter_debate_events_module
from api.server import app


def _parse_sse_payloads(body: str) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for block in body.split("\n\n"):
        for line in block.split("\n"):
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
    return events


@pytest.mark.asyncio
async def test_stream_emits_full_debate_lifecycle() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream(
            "POST",
            "/api/debate/stream",
            json={"topic": "Should AI replace teachers?"},
        ) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")
            body = await response.aread()

    events = _parse_sse_payloads(body.decode())
    types = [event["type"] for event in events]

    assert types[0] == "debate_started"
    assert types.count("turn_started") == 6
    assert types.count("turn_completed") == 6
    assert types.count("message_chunk") > 0
    assert "summary" in types
    assert types[-1] == "debate_completed"


@pytest.mark.asyncio
async def test_stream_emits_error_event_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingGraph:
        async def astream_events(
            self, *args: object, **kwargs: object
        ) -> AsyncIterator[object]:
            raise RuntimeError("forced failure")
            yield  # pragma: no cover

    monkeypatch.setattr(iter_debate_events_module, "get_graph", lambda: FailingGraph())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/debate/stream",
            json={"topic": "Failure case"},
        )

    events = _parse_sse_payloads(response.text)
    assert [event["type"] for event in events] == ["error", "debate_completed"]


@pytest.mark.asyncio
async def test_stream_stops_without_completion_on_client_disconnect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from fastapi import Request

    class SlowGraph:
        async def astream_events(
            self, *args: object, **kwargs: object
        ) -> AsyncIterator[dict[str, object]]:
            empty_turn_state: dict[str, int | list[object]] = {
                "turn_red": 0,
                "turn_green": 0,
                "turn_messages": [],
            }
            yield {
                "event": "on_chain_start",
                "name": "debater_red_agent",
                "metadata": {},
                "data": {"input": empty_turn_state},
            }
            yield {
                "event": "on_chain_start",
                "name": "debater_red_agent",
                "metadata": {},
                "data": {"input": empty_turn_state},
            }

    disconnect_checks = 0

    async def mock_is_disconnected(self: Request) -> bool:
        nonlocal disconnect_checks
        disconnect_checks += 1
        return disconnect_checks > 1

    monkeypatch.setattr(iter_debate_events_module, "get_graph", lambda: SlowGraph())
    monkeypatch.setattr(Request, "is_disconnected", mock_is_disconnected)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/debate/stream",
            json={"topic": "Disconnect case"},
        )

    events = _parse_sse_payloads(response.text)
    types = [event["type"] for event in events]

    assert types[0] == "debate_started"
    assert "debate_completed" not in types


@pytest.mark.asyncio
async def test_stream_rejects_whitespace_only_topic() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/debate/stream",
            json={"topic": "   "},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_stream_rejects_over_limit_topic() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/debate/stream",
            json={"topic": "x" * 501},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
