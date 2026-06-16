import asyncio
from typing import Any

from bedrock_agentcore.runtime import BedrockAgentCoreApp, RequestContext

from api.streaming.iter_debate_events import iter_debate_events
from debate.topic import TopicValidationError, normalize_topic
from runtime_env import configure_runtime_env

configure_runtime_env()

app = BedrockAgentCoreApp()
log = app.logger


@app.entrypoint  # pyright: ignore[reportUnknownMemberType]
async def invoke(payload: dict[str, Any], context: RequestContext):
    log.info("Invoking debate agent (streaming)")

    raw_topic = payload.get("topic") or payload.get("prompt", "")
    try:
        topic = normalize_topic(raw_topic)
    except TopicValidationError as exc:
        yield {"type": "error", "message": str(exc)}
        yield {"type": "debate_completed"}
        return

    is_disconnected = None
    if context.request is not None:
        is_disconnected = context.request.is_disconnected

    try:
        async for event in iter_debate_events(topic, is_disconnected=is_disconnected):
            yield event.model_dump()
    except asyncio.CancelledError:
        log.info("Debate stream cancelled by client disconnect")
        raise


if __name__ == "__main__":
    app.run()  # pyright: ignore[reportUnknownMemberType]
