/**
 * Framework-agnostic outbound-call controller (testable in Node).
 * Owns validation, call start, and status polling until a terminal state.
 */

import { normalizePhone, phoneValidationError } from "../api/phone.js";

export const TERMINAL_STATUSES = new Set([
  "completed",
  "failed",
  "busy",
  "no-answer",
  "canceled",
]);

export function isTerminalStatus(status) {
  return TERMINAL_STATUSES.has((status || "").toLowerCase());
}

export function createCallController({
  startCall,
  fetchStatus,
  onChange,
  pollMs = 3000,
  setIntervalFn = (...args) => setInterval(...args),
  clearIntervalFn = (id) => clearInterval(id),
}) {
  let state = {
    phase: "idle", // idle | calling | active | done | error
    call: null,
    error: null,
    phoneError: null,
  };
  let pollId = null;

  function emit(patch) {
    state = { ...state, ...patch };
    if (typeof onChange === "function") onChange(state);
    return state;
  }

  function stopPolling() {
    if (pollId != null) {
      clearIntervalFn(pollId);
      pollId = null;
    }
  }

  function startPolling(callSid) {
    stopPolling();
    pollId = setIntervalFn(async () => {
      try {
        const { data } = await fetchStatus(callSid);
        const done = data.terminal || isTerminalStatus(data.status);
        emit({
          call: { ...(state.call || {}), ...data },
          phase: done ? "done" : "active",
        });
        if (done) stopPolling();
      } catch {
        // Registry entry may lag the call; keep polling until terminal/dispose
      }
    }, pollMs);
  }

  async function startAndTrack(body) {
    emit({ phase: "calling", error: null, call: null, phoneError: null });
    try {
      const { data } = await startCall(body);
      emit({ phase: "active", call: data });
      if (data.call_sid) startPolling(data.call_sid);
    } catch (err) {
      emit({ phase: "error", error: err.message || "Call failed" });
    }
    return state;
  }

  return {
    get state() {
      return state;
    },

    /** Validate + start an outbound call to a raw number. Returns final state. */
    async dial(rawPhone, context = {}) {
      const validation = phoneValidationError(rawPhone);
      if (validation) {
        return emit({ phoneError: validation });
      }
      return startAndTrack({ to: normalizePhone(rawPhone), ...context });
    },

    /** Start an outbound call to a demo lead; server re-checks eligibility. */
    async dialLead(leadId, context = {}) {
      return startAndTrack({ leadId, ...context });
    },

    dispose() {
      stopPolling();
    },
  };
}
