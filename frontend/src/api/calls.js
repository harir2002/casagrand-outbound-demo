/**
 * Shared API client for the Casagrand voice-agent demo.
 * Contract:
 *   GET  /health
 *   GET  /projects
 *   POST /session/start
 *   POST /session/turn
 *   POST /session/reset
 *   GET  /session/state?session_id=
 */

import { request } from "./client";

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
    },
    latencyMs: view.latency_ms ?? result.latencyMs,
  };
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

/** POST /session/turn */
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
  return wrapCallView(result);
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
