"""Bridge Twilio Media Streams ↔ existing STT/LLM/TTS orchestrator."""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.integrations.twilio import audio_codec
from app.integrations.twilio.media_streams import (
    StreamEventType,
    StreamMessage,
    build_clear_message,
    build_mark_message,
    build_media_out_message,
    chunk_mulaw,
    parse_stream_message,
)
from app.models.call_view import TurnRequest
from app.models.session import CreateSessionRequest, Language
from app.services import call_service
from app.services.conversation_orchestrator import (
    ConversationOrchestrator,
    get_orchestrator,
)

logger = get_logger(__name__)


class MediaSender(Protocol):
    async def send_json(self, data: dict[str, Any]) -> None: ...


@dataclass
class BridgeTimings:
    connected_ms: float | None = None
    start_ms: float | None = None
    first_media_ms: float | None = None
    last_turn_total_ms: float | None = None
    last_turn_first_audio_ms: float | None = None
    turns: int = 0


@dataclass
class TelephonyBridgeSession:
    session_id: str
    project_id: str
    language: Language
    call_sid: str | None = None
    stream_sid: str | None = None
    account_sid: str | None = None
    inbound_mulaw: bytearray = field(default_factory=bytearray)
    speech_started: bool = False
    silence_frames: int = 0
    processing: bool = False
    started_at: float = field(default_factory=time.perf_counter)
    timings: BridgeTimings = field(default_factory=BridgeTimings)
    last_reply_text: str | None = None
    closed: bool = False


class TelephonyBridge:
    """Owns one Media Stream connection and drives voice turns."""

    # ~20ms frames; 25 frames ≈ 500ms silence to end utterance
    SILENCE_FRAMES_TO_COMMIT = 25
    MIN_SPEECH_BYTES = 1600  # ~200ms
    MAX_UTTERANCE_BYTES = 8 * 8000  # ~8s μ-law

    def __init__(
        self,
        *,
        sender: MediaSender,
        orchestrator: ConversationOrchestrator | None = None,
        settings: Settings | None = None,
        bidirectional: bool = True,
        tts_sample_rate: int | None = None,
    ) -> None:
        self.sender = sender
        self.orchestrator = orchestrator or get_orchestrator()
        self.settings = settings or get_settings()
        self.bidirectional = bidirectional
        self.tts_sample_rate = tts_sample_rate or self.settings.sarvam_tts_sample_rate
        self.state: TelephonyBridgeSession | None = None

    async def handle_raw_message(self, data: str | bytes) -> None:
        message = parse_stream_message(data)
        await self.handle_message(message)

    async def handle_message(self, message: StreamMessage) -> None:
        if message.event == StreamEventType.CONNECTED:
            await self._on_connected(message)
        elif message.event == StreamEventType.START:
            await self._on_start(message)
        elif message.event == StreamEventType.MEDIA:
            await self._on_media(message)
        elif message.event == StreamEventType.DTMF:
            logger.info("twilio_dtmf digit=%s stream=%s", message.dtmf_digit, message.stream_sid)
        elif message.event == StreamEventType.STOP:
            await self._on_stop(message)
        else:
            logger.debug("twilio_stream_unhandled event=%s", message.event)

    async def _on_connected(self, message: StreamMessage) -> None:
        logger.info("twilio_stream_connected protocol=%s", (message.raw.get("protocol") or ""))
        # Session is created on start (has custom parameters)

    async def _on_start(self, message: StreamMessage) -> None:
        params = message.custom_parameters or {}
        session_id = (params.get("session_id") or "").strip()
        project_id = (params.get("project_id") or self.settings.default_project).strip()
        lang_raw = (params.get("language") or self.settings.default_language).strip()
        try:
            language = Language(lang_raw)
        except ValueError:
            language = Language.EN

        if session_id:
            try:
                existing = call_service.get_session(session_id)
                session_id = existing.session.session_id
                project_id = existing.session.project_id
                language = existing.session.language
            except Exception:  # noqa: BLE001
                logger.warning("twilio_session_missing id=%s; creating new", session_id)
                session_id = ""

        if not session_id:
            created = call_service.create_session(
                CreateSessionRequest(project_id=project_id, language=language)
            )
            session_id = created.session.session_id

        now = time.perf_counter()
        self.state = TelephonyBridgeSession(
            session_id=session_id,
            project_id=project_id,
            language=language,
            call_sid=message.call_sid,
            stream_sid=message.stream_sid,
            account_sid=message.account_sid,
            started_at=now,
            timings=BridgeTimings(
                connected_ms=0.0,
                start_ms=0.0,
            ),
        )
        logger.info(
            "twilio_stream_start call=%s stream=%s session=%s project=%s",
            message.call_sid,
            message.stream_sid,
            session_id,
            project_id,
        )

        # Play intro greeting through the existing pipeline (text turn).
        await self._run_turn(text="hello", interrupt=False)

    async def _on_media(self, message: StreamMessage) -> None:
        if not self.state or self.state.closed or self.state.processing:
            return
        if message.media_track and message.media_track not in ("inbound", "inbound_track"):
            # Ignore outbound loopback if Twilio sends both tracks
            if message.media_track in ("outbound", "outbound_track"):
                return

        payload = message.media_payload or b""
        if not payload:
            return

        state = self.state
        if state.timings.first_media_ms is None:
            state.timings.first_media_ms = round(
                (time.perf_counter() - state.started_at) * 1000, 2
            )

        quiet = audio_codec.is_mostly_silence_mulaw(payload)
        if not quiet:
            state.speech_started = True
            state.silence_frames = 0
            state.inbound_mulaw.extend(payload)
        elif state.speech_started:
            state.silence_frames += 1
            state.inbound_mulaw.extend(payload)

        if len(state.inbound_mulaw) >= self.MAX_UTTERANCE_BYTES:
            await self._commit_utterance()
            return

        if (
            state.speech_started
            and state.silence_frames >= self.SILENCE_FRAMES_TO_COMMIT
            and len(state.inbound_mulaw) >= self.MIN_SPEECH_BYTES
        ):
            await self._commit_utterance()

    async def _on_stop(self, message: StreamMessage) -> None:
        logger.info(
            "twilio_stream_stop call=%s stream=%s",
            message.call_sid or (self.state.call_sid if self.state else None),
            message.stream_sid or (self.state.stream_sid if self.state else None),
        )
        if self.state and self.state.speech_started and len(self.state.inbound_mulaw) >= self.MIN_SPEECH_BYTES:
            await self._commit_utterance()
        if self.state:
            self.state.closed = True

    async def _commit_utterance(self) -> None:
        if not self.state or self.state.processing:
            return
        mulaw = bytes(self.state.inbound_mulaw)
        self.state.inbound_mulaw.clear()
        self.state.speech_started = False
        self.state.silence_frames = 0
        if len(mulaw) < self.MIN_SPEECH_BYTES:
            return
        await self._run_turn(audio_mulaw=mulaw, interrupt=True)

    async def _run_turn(
        self,
        *,
        text: str | None = None,
        audio_mulaw: bytes | None = None,
        interrupt: bool = False,
    ) -> None:
        if not self.state or self.state.processing:
            return
        state = self.state
        state.processing = True
        started = time.perf_counter()
        try:
            audio_b64 = None
            mime = "audio/wav"
            if audio_mulaw:
                wav = audio_codec.mulaw_frames_to_wav(audio_mulaw)
                audio_b64 = base64.b64encode(wav).decode("ascii")

            view = await self.orchestrator.handle_turn(
                TurnRequest(
                    session_id=state.session_id,
                    text=text,
                    language=state.language,
                    interrupt=interrupt,
                    audio_base64=audio_b64,
                    audio_mime_type=mime,
                )
            )
            state.last_reply_text = view.reply_text
            state.timings.turns += 1
            timings = (view.provider_meta or {}).get("timings") or {}
            state.timings.last_turn_total_ms = timings.get("total_ms")
            state.timings.last_turn_first_audio_ms = timings.get("first_audio_ms")

            if self.bidirectional and state.stream_sid and view.audio_base64:
                await self._play_agent_audio(state.stream_sid, view.audio_base64)
            elif not self.bidirectional:
                logger.info(
                    "twilio_bridge_receive_only session=%s reply_chars=%s",
                    state.session_id,
                    len(view.reply_text or ""),
                )
        except Exception as exc:  # noqa: BLE001
            logger.exception("twilio_bridge_turn_failed error=%s", exc)
        finally:
            state.processing = False
            elapsed = round((time.perf_counter() - started) * 1000, 2)
            logger.info(
                "twilio_bridge_turn_done session=%s wall_ms=%s turns=%s",
                state.session_id,
                elapsed,
                state.timings.turns,
            )

    async def _play_agent_audio(self, stream_sid: str, audio_base64: str) -> None:
        try:
            raw = base64.b64decode(audio_base64)
        except Exception:  # noqa: BLE001
            return
        mulaw = audio_codec.pcm_or_wav_to_mulaw(
            raw,
            src_sample_rate=self.tts_sample_rate,
            is_wav=True,
        )
        if not mulaw:
            return
        await self.sender.send_json(build_clear_message(stream_sid))
        for frame in chunk_mulaw(mulaw):
            await self.sender.send_json(build_media_out_message(stream_sid, frame))
        await self.sender.send_json(build_mark_message(stream_sid, "agent_done"))

    def metadata(self) -> dict[str, Any]:
        if not self.state:
            return {"active": False}
        t = self.state.timings
        return {
            "active": not self.state.closed,
            "session_id": self.state.session_id,
            "call_sid": self.state.call_sid,
            "stream_sid": self.state.stream_sid,
            "project_id": self.state.project_id,
            "language": self.state.language.value,
            "bidirectional": self.bidirectional,
            "timings": {
                "first_media_ms": t.first_media_ms,
                "last_turn_total_ms": t.last_turn_total_ms,
                "last_turn_first_audio_ms": t.last_turn_first_audio_ms,
                "turns": t.turns,
            },
            "last_reply_text": self.state.last_reply_text,
        }
