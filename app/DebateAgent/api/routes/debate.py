from fastapi import APIRouter, Request
from sse_starlette import EventSourceResponse

from api.schemas.debate import DebateRequest
from api.streaming.debate_stream import debate_event_generator

router = APIRouter()


@router.post("/api/debate/stream")
async def stream_debate(request: Request, body: DebateRequest) -> EventSourceResponse:
    return EventSourceResponse(
        debate_event_generator(request, body.topic),
        ping=15,
        sep="\n",
    )
