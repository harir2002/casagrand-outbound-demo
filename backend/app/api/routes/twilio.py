"""Twilio Voice webhooks + Media Streams WebSocket."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Form, HTTPException, Query, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse

from app.core.config import get_settings
from app.core.logging import get_logger
from app.integrations.twilio import call_registry
from app.integrations.twilio.client import validate_twilio_signature
from app.integrations.twilio.config import load_twilio_config, require_twilio_ready, validate_twilio_config
from app.integrations.twilio.schemas import OutboundCallRequest, OutboundCallResponse
from app.integrations.twilio.service import TwilioCallService
from app.integrations.twilio.twiml import build_media_stream_twiml, build_say_fallback_twiml
from app.models.session import Language
from app.services import call_service
from app.services.lead_filter import LeadBlockedError
from app.services.telephony_bridge import TelephonyBridge

logger = get_logger(__name__)
router = APIRouter(prefix="/twilio", tags=["twilio"])


def _check_signature(request: Request, form: dict[str, str]) -> None:
    settings = get_settings()
    cfg = load_twilio_config(settings)
    if not cfg.enabled or not cfg.validate_signatures:
        return
    if settings.is_test_provider_mode:
        return
    signature = request.headers.get("X-Twilio-Signature", "")
    # Reconstruct the public URL Twilio signed (prefer configured public base)
    path = request.url.path
    query = ("?" + request.url.query) if request.url.query else ""
    url = cfg.public_base_url.rstrip("/") + path + query
    if not validate_twilio_signature(
        auth_token=cfg.auth_token,
        signature=signature,
        url=url,
        params=form,
    ):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")


@router.get("/status")
def twilio_status() -> dict[str, Any]:
    cfg = load_twilio_config()
    problems = validate_twilio_config(cfg)
    return {
        "enabled": cfg.enabled,
        "ready": cfg.enabled and not problems,
        "problems": problems,
        "from_number_configured": bool(cfg.from_number),
        "public_base_url_configured": bool(cfg.public_base_url),
        "media_stream_path": cfg.media_stream_path,
        "voice_webhook_path": cfg.voice_webhook_path,
        "media_stream_wss_url": cfg.media_stream_wss_url if cfg.public_base_url else None,
    }


@router.post("/outbound-call", response_model=OutboundCallResponse)
async def outbound_call(payload: OutboundCallRequest) -> OutboundCallResponse:
    try:
        service = TwilioCallService()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    try:
        return await service.start_outbound_call(payload)
    except LeadBlockedError as exc:
        logger.warning("outbound_call_blocked lead=%s reasons=%s", exc.lead_id, exc.reasons)
        raise HTTPException(
            status_code=409,
            detail={
                "message": str(exc),
                "lead_id": exc.lead_id,
                "blocked": True,
                "reasons": [reason.model_dump() for reason in exc.reasons],
            },
        ) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("outbound_call_failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.api_route("/voice-webhook", methods=["GET", "POST"])
async def voice_webhook(
    request: Request,
    session_id: str | None = Query(None),
    project_id: str | None = Query(None),
    language: str | None = Query(None),
) -> Response:
    """Twilio hits this when the outbound call is answered; return Connect/Stream TwiML."""
    form: dict[str, str] = {}
    if request.method == "POST":
        form_data = await request.form()
        form = {str(k): str(v) for k, v in form_data.items()}
        _check_signature(request, form)
        session_id = session_id or form.get("session_id")
        project_id = project_id or form.get("project_id")
        language = language or form.get("language")

    settings = get_settings()
    cfg = load_twilio_config(settings)
    problems = validate_twilio_config(cfg)
    if not cfg.enabled or problems:
        msg = problems[0] if problems else "Twilio is not enabled"
        return Response(
            content=build_say_fallback_twiml(msg),
            media_type="application/xml",
        )

    sid = (session_id or "").strip()
    proj = (project_id or settings.default_project).strip()
    lang = (language or settings.default_language).strip()

    if sid:
        try:
            existing = call_service.get_session(sid)
            sid = existing.session.session_id
            proj = existing.session.project_id
            lang = existing.session.language.value
        except Exception:  # noqa: BLE001
            sid = ""

    if not sid:
        try:
            lang_enum = Language(lang)
        except ValueError:
            lang_enum = Language.EN
        created = call_service.create_session(
            __import__("app.models.session", fromlist=["CreateSessionRequest"]).CreateSessionRequest(
                project_id=proj, language=lang_enum
            )
        )
        sid = created.session.session_id
        proj = created.session.project_id
        lang = created.session.language.value

    twiml = build_media_stream_twiml(
        cfg.media_stream_wss_url,
        parameters={
            "session_id": sid,
            "project_id": proj,
            "language": lang,
        },
    )
    return Response(content=twiml, media_type="application/xml")


@router.api_route("/status-callback", methods=["GET", "POST"])
async def status_callback(request: Request) -> PlainTextResponse:
    if request.method == "POST":
        form_data = await request.form()
        form = {str(k): str(v) for k, v in form_data.items()}
        try:
            _check_signature(request, form)
        except HTTPException:
            # Status callbacks are best-effort in local demos
            logger.warning("twilio_status_callback_bad_signature")
        call_sid = form.get("CallSid") or ""
        call_status = form.get("CallStatus") or ""
        if call_sid and call_status:
            call_registry.update_status(
                call_sid, call_status, duration=form.get("CallDuration")
            )
        logger.info(
            "twilio_status call=%s status=%s duration=%s",
            call_sid,
            call_status,
            form.get("CallDuration"),
        )
    return PlainTextResponse("ok")


@router.get("/call-status")
def call_status(call_sid: str = Query(..., min_length=1)) -> dict[str, Any]:
    """Latest known status for an outbound call (fed by Twilio status callbacks)."""
    entry = call_registry.get_call(call_sid)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Unknown call SID: {call_sid}")
    entry["terminal"] = call_registry.is_terminal(entry.get("status"))
    return entry


class _WebSocketSender:
    def __init__(self, websocket: WebSocket) -> None:
        self.websocket = websocket

    async def send_json(self, data: dict[str, Any]) -> None:
        await self.websocket.send_json(data)


@router.websocket("/media-stream")
async def media_stream(websocket: WebSocket) -> None:
    """Twilio Media Streams WebSocket bridge into the voice-agent pipeline."""
    settings = get_settings()
    cfg = load_twilio_config(settings)
    if not cfg.enabled:
        await websocket.close(code=1013)
        return
    problems = validate_twilio_config(cfg)
    if problems:
        logger.error("twilio_media_stream_misconfigured: %s", problems)
        await websocket.close(code=1013)
        return

    await websocket.accept()
    bridge = TelephonyBridge(sender=_WebSocketSender(websocket), bidirectional=True)
    logger.info("twilio_media_stream_accepted")
    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
            text = message.get("text")
            data = message.get("bytes")
            if text is not None:
                await bridge.handle_raw_message(text)
            elif data is not None:
                await bridge.handle_raw_message(data)
    except WebSocketDisconnect:
        logger.info("twilio_media_stream_disconnected meta=%s", bridge.metadata())
    except Exception:  # noqa: BLE001
        logger.exception("twilio_media_stream_error meta=%s", bridge.metadata())
        try:
            await websocket.close(code=1011)
        except Exception:  # noqa: BLE001
            pass
