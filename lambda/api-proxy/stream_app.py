"""POST /api/debate/stream — JWT gate + AgentCore SSE proxy (Lambda Web Adapter)."""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import AsyncIterator, Iterator
from typing import Any

import boto3
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route

from auth import extract_bearer_token, required_env, verify_access_token


def _agentcore_client() -> Any:
    region = os.environ.get("AWS_REGION", "eu-west-1")
    return boto3.client("bedrock-agentcore", region_name=region)


def _iter_agentcore_sse(topic: str) -> Iterator[bytes]:
    runtime_arn = required_env("AGENT_RUNTIME_ARN")
    payload = json.dumps({"topic": topic}).encode("utf-8")

    response = _agentcore_client().invoke_agent_runtime(
        agentRuntimeArn=runtime_arn,
        runtimeSessionId=str(uuid.uuid4()),
        qualifier="DEFAULT",
        payload=payload,
    )

    stream = response.get("response")
    if stream is None:
        yield b'data: {"type":"error","message":"Empty AgentCore response"}\n\n'
        return

    for chunk in stream.iter_chunks():
        if chunk:
            yield chunk


async def stream_debate(request: Request) -> StreamingResponse | JSONResponse:
    token = extract_bearer_token(request.headers.get("authorization"))
    if not verify_access_token(token):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    try:
        body = await request.json()
    except json.JSONDecodeError:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    topic = body.get("topic") if isinstance(body, dict) else None
    if not isinstance(topic, str) or not topic.strip():
        return JSONResponse({"error": "Topic cannot be empty"}, status_code=400)

    async def event_stream() -> AsyncIterator[bytes]:
        for chunk in _iter_agentcore_sse(topic.strip()):
            yield chunk

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


app = Starlette(
    routes=[
        Route("/api/debate/stream", stream_debate, methods=["POST"]),
        Route("/{stage}/api/debate/stream", stream_debate, methods=["POST"]),
    ],
)
