from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.data.projects import list_projects
from app.models.call_view import (
    CallViewResponse,
    ResetRequest,
    StartSessionRequest,
    TurnRequest,
)
from app.models.project import ProjectSummary
from app.models.session import CreateSessionRequest
from app.services import call_service
from app.services.call_view import to_call_view
from app.services.conversation_orchestrator import get_orchestrator

router = APIRouter(tags=["call"])


@router.get("/projects", response_model=list[ProjectSummary])
def projects() -> list[ProjectSummary]:
    return list_projects()


@router.post("/session/start", response_model=CallViewResponse)
def start_session(payload: StartSessionRequest) -> CallViewResponse:
    result = call_service.create_session(
        CreateSessionRequest(project_id=payload.project_id, language=payload.language)
    )
    return to_call_view(result)


@router.post("/session/turn", response_model=CallViewResponse)
async def turn(payload: TurnRequest) -> CallViewResponse:
    if not (payload.text and payload.text.strip()) and not payload.audio_base64:
        raise HTTPException(
            status_code=400,
            detail="Provide text or audio_base64 for /session/turn",
        )
    return await get_orchestrator().handle_turn(payload)


@router.post("/session/turn/stream")
async def turn_stream(payload: TurnRequest) -> StreamingResponse:
    """NDJSON event stream: stream_start, text_delta, audio_chunk, stream_end, error."""
    if not (payload.text and payload.text.strip()) and not payload.audio_base64:
        raise HTTPException(
            status_code=400,
            detail="Provide text or audio_base64 for /session/turn/stream",
        )

    import json

    async def event_bytes():
        async for event in get_orchestrator().handle_turn_stream(payload):
            yield (json.dumps(event, default=str) + "\n").encode("utf-8")

    return StreamingResponse(
        event_bytes(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/session/reset", response_model=CallViewResponse)
def reset_session(payload: ResetRequest) -> CallViewResponse:
    result = call_service.reset_session(payload.session_id)
    return to_call_view(result)


@router.get("/session/state", response_model=CallViewResponse)
def session_state(session_id: str = Query(..., min_length=1)) -> CallViewResponse:
    result = call_service.get_session(session_id)
    return to_call_view(result)
