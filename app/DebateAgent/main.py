from typing import Any

from bedrock_agentcore.runtime import BedrockAgentCoreApp, RequestContext

from debate.graph import get_graph
from debate.initial_state import build_initial_state

app = BedrockAgentCoreApp()
log = app.logger


@app.entrypoint  # pyright: ignore[reportUnknownMemberType]
async def invoke(payload: dict[str, Any], context: RequestContext) -> dict[str, Any]:
    log.info("Invoking debate agent")

    topic = payload.get("topic") or payload.get("prompt", "")
    if not topic.strip():
        return {"error": "Topic cannot be empty"}

    graph = get_graph()
    result = await graph.ainvoke(build_initial_state(topic))  # pyright: ignore[reportUnknownMemberType]

    last_message = result["messages"][-1]
    output = (
        last_message.content if hasattr(last_message, "content") else str(last_message)
    )
    log.info("Debate agent output: %s", output)
    return {"result": output, "topic": topic}


if __name__ == "__main__":
    app.run()  # pyright: ignore[reportUnknownMemberType]
