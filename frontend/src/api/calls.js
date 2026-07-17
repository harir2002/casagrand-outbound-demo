/**
 * Shared API client for the Casagrand voice-agent demo.
 * Contract:
 *   GET  /health
 *   GET  /projects
 *   POST /session/start
 *   POST /session/turn
 *   POST /session/turn/stream  (NDJSON events)
 *   POST /session/reset
 *   GET  /session/state?session_id=
 */

import { playbackQueue } from "./audioQueue";
import { ApiError, request } from "./client";

const API_BASE = import.meta.env.VITE_API_BASE || "";

/**
 * Normalize CallView JSON into the shape UI panels already consume.
 */
export function callViewToSession(view) {
  if (!view) return null;
  return {
    session_id: view.session_id,
    call_id: view.call_id,
    project_id: view.active_project,
    language: view.active_language,
    flow_bucket: view.active_bucket,
    previous_bucket: view.previous_bucket || null,
    transcript: view.transcript || [],
    memory: view.memory_slots || {},
    last_intent: view.last_intent || null,
    last_faq_source: view.faq_source || null,
    needs_handoff: Boolean(view.needs_handoff),
    handoff_reason: view.handoff_reason || null,
    handoff_payload: view.handoff_payload || null,
    final_summary: view.summary || null,
    call_status: view.call_status || "active",
    is_interrupted: Boolean(view.is_interrupted),
    warning: view.warning || null,
    audio_base64: view.audio_base64 || null,
    audio_url: view.audio_url || null,
    audio_mime_type: view.audio_mime_type || null,
    stt_provider: view.stt_provider || null,
    tts_provider: view.tts_provider || null,
    llm_provider: view.llm_provider || null,
    provider_meta: view.provider_meta || {},
  };
}

function wrapCallView(result) {
  const view = result.data;
  return {
    data: {
      view,
      session: callViewToSession(view),
      reply: view.reply_text
        ? {
            text: view.reply_text,
            faq_source: view.faq_source,
            flow_bucket: view.active_bucket,
            language: view.active_language,
            intent: view.last_intent,
            needs_handoff: view.needs_handoff,
          }
        : null,
      latency_ms: view.latency_ms ?? result.latencyMs,
      warning: view.warning || null,
      error: view.error || null,
      streamMeta: result.streamMeta || null,
    },
    latencyMs: view.latency_ms ?? result.latencyMs,
  };
}

/** Queue a WAV/PCM chunk for sequential, non-overlapping playback. */
function playWavBase64(audioBase64, mimeType = "audio/wav", { reset = false } = {}) {
  if (reset) playbackQueue.clear();
  playbackQueue.enqueue(audioBase64, mimeType || "audio/wav");
}

export function getApiMode() {
  return "live";
}

export function checkHealth() {
  return request("/health");
}

export function listProjects() {
  return request("/projects");
}

/** POST /session/start */
export async function startSession({ projectId, language }) {
  const result = await request("/session/start", {
    method: "POST",
    body: JSON.stringify({
      project_id: projectId,
      language,
    }),
  });
  return wrapCallView(result);
}

/** POST /session/turn (aggregated compatibility path) */
export async function sendTurn({ sessionId, text, language, interrupt = false }) {
  const result = await request("/session/turn", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      text,
      language,
      interrupt,
    }),
  });
  if (result.data?.audio_base64) {
    playWavBase64(result.data.audio_base64, result.data.audio_mime_type || "audio/wav", {
      reset: true,
    });
  }
  return wrapCallView(result);
}

/**
 * Prefer NDJSON streaming turn; fall back to aggregated /session/turn.
 * onEvent receives raw stream events for UI updates.
 */
export async function sendTurnStreaming({
  sessionId,
  text,
  language,
  interrupt = false,
  onEvent,
}) {
  const started = performance.now();
  // New turn: drop any still-playing / queued audio from the previous reply.
  playbackQueue.clear();
  let response;
  try {
    response = await fetch(`${API_BASE}/session/turn/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        text,
        language,
        interrupt,
      }),
    });
  } catch {
    return sendTurn({ sessionId, text, language, interrupt });
  }

  if (!response.ok || !response.body) {
    return sendTurn({ sessionId, text, language, interrupt });
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let callView = null;
  let streamMeta = {
    first_audio_ms: null,
    total_ms: null,
    transport: null,
    fallback_used: false,
    streaming: true,
  };
  let firstAudioAt = null;
  let replyText = "";
  let audioChunkCount = 0;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (!line.trim()) continue;
      let event;
      try {
        event = JSON.parse(line);
      } catch {
        continue;
      }
      if (typeof onEvent === "function") onEvent(event);

      if (event.event === "text_delta" && event.text) {
        replyText += event.text;
      } else if (event.event === "audio_chunk" && event.audio_base64) {
        if (firstAudioAt == null) {
          firstAudioAt = Math.round(performance.now() - started);
          streamMeta.first_audio_ms = firstAudioAt;
        }
        streamMeta.transport = event.transport || streamMeta.transport;
        streamMeta.fallback_used = Boolean(event.fallback_used);
        audioChunkCount += 1;
        // Queue in arrival order; player drains sequentially (no overlap).
        playWavBase64(event.audio_base64, event.mime_type || "audio/wav");
      } else if (event.event === "stream_end") {
        callView = event.call_view || null;
        streamMeta = {
          ...streamMeta,
          ...(event.timings || {}),
          transport: event.transport ?? streamMeta.transport,
          fallback_used: Boolean(event.fallback_used),
          total_ms: event.timings?.total_ms ?? Math.round(performance.now() - started),
          first_audio_ms:
            event.timings?.first_audio_ms ?? streamMeta.first_audio_ms ?? firstAudioAt,
          audio_chunks: audioChunkCount,
        };
      } else if (event.event === "error") {
        throw new ApiError(event.message || "Stream error", {
          status: event.code || 500,
          latencyMs: Math.round(performance.now() - started),
        });
      }
    }
  }

  if (!callView) {
    return sendTurn({ sessionId, text, language, interrupt });
  }

  if (!callView.reply_text && replyText) {
    callView.reply_text = replyText;
  }

  return wrapCallView({
    data: callView,
    latencyMs: streamMeta.total_ms ?? Math.round(performance.now() - started),
    streamMeta,
  });
}

/** GET /twilio/status — telephony readiness (enabled + configured). */
export function getTelephonyStatus() {
  return request("/twilio/status");
}

/** POST /twilio/outbound-call — dial an E.164 number or a filtered demo lead. */
export function startOutboundCall({
  to,
  leadId,
  customerName,
  sessionId,
  projectId,
  language,
}) {
  return request("/twilio/outbound-call", {
    method: "POST",
    body: JSON.stringify({
      to: to || null,
      lead_id: leadId || null,
      customer_name: customerName || null,
      session_id: sessionId || null,
      project_id: projectId || null,
      language: language || null,
    }),
  });
}

/** GET /leads — full demo lead list. */
export function listLeads() {
  return request("/leads");
}

/** POST /leads/filter — apply demo eligibility filters before calling. */
export function filterLeads({
  projectId,
  language,
  statuses,
  requireConsent = true,
  excludeDnc = true,
  respectCallWindow = true,
} = {}) {
  return request("/leads/filter", {
    method: "POST",
    body: JSON.stringify({
      project_id: projectId || null,
      language: language || null,
      statuses: statuses?.length ? statuses : null,
      require_consent: requireConsent,
      exclude_dnc: excludeDnc,
      respect_call_window: respectCallWindow,
    }),
  });
}

/** GET /twilio/call-status — latest status for a call SID. */
export function getCallStatus(callSid) {
  return request(`/twilio/call-status?call_sid=${encodeURIComponent(callSid)}`);
}

/** POST /campaigns — snapshot filtered leads into a new campaign. */
export function createCampaign(filters = {}) {
  return request("/campaigns", {
    method: "POST",
    body: JSON.stringify({
      filters: {
        project_id: filters.projectId || null,
        language: filters.language || null,
        statuses: filters.statuses?.length ? filters.statuses : null,
        require_consent: filters.requireConsent ?? true,
        exclude_dnc: filters.excludeDnc ?? true,
        respect_call_window: filters.respectCallWindow ?? true,
      },
    }),
  });
}

/** POST /campaigns/{id}/start — begin the sequential dial run. */
export function startCampaign(campaignId, options = {}) {
  return request(`/campaigns/${encodeURIComponent(campaignId)}/start`, {
    method: "POST",
    body: JSON.stringify(options),
  });
}

/** GET /campaigns/{id} — live campaign progress + summary. */
export function getCampaign(campaignId) {
  return request(`/campaigns/${encodeURIComponent(campaignId)}`);
}

/** POST /campaigns/{id}/cancel */
export function cancelCampaign(campaignId) {
  return request(`/campaigns/${encodeURIComponent(campaignId)}/cancel`, {
    method: "POST",
  });
}

/** POST /session/reset */
export async function resetSession({ sessionId }) {
  const result = await request("/session/reset", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId }),
  });
  return wrapCallView(result);
}

/** GET /session/state */
export async function getSessionState({ sessionId }) {
  const result = await request(
    `/session/state?session_id=${encodeURIComponent(sessionId)}`
  );
  return wrapCallView(result);
}
