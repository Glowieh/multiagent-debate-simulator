from typing import Any

from bedrock_agentcore.runtime import BedrockAgentCoreApp, RequestContext

from api.streaming.debate_stream import iter_debate_events

app = BedrockAgentCoreApp()
log = app.logger


@app.entrypoint  # pyright: ignore[reportUnknownMemberType]
async def invoke(payload: dict[str, Any], _context: RequestContext):
    log.info("Invoking debate agent (streaming)")

    topic = payload.get("topic") or payload.get("prompt", "")
    if not isinstance(topic, str) or not topic.strip():
        yield {"type": "error", "message": "Topic cannot be empty"}
        return

    async for event in iter_debate_events(topic.strip()):
        yield event.model_dump()


if __name__ == "__main__":
    app.run()  # pyright: ignore[reportUnknownMemberType]
