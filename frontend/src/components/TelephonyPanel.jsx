import { useEffect, useState } from "react";
import { phoneValidationError } from "../api/phone";
import { isTerminalStatus } from "../hooks/callController";
import useTwilioCall from "../hooks/useTwilioCall";

/**
 * Primary outbound call form: customer name + E.164 phone → Initiate call.
 * Keeps the agent on the existing Sarvam STT/TTS pipeline via Twilio Media Streams.
 */
export default function TelephonyPanel({
  projects = [],
  onCallSessionChange,
}) {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [nameError, setNameError] = useState(null);
  const [projectId, setProjectId] = useState("");
  const [language, setLanguage] = useState("ta");
  const { readiness, phase, call, error, phoneError, calling, dial } = useTwilioCall();

  const disabledReason =
    readiness === null
      ? "Checking telephony…"
      : !readiness.enabled
        ? "Telephony disabled (set TWILIO_ENABLED=true)"
        : !readiness.ready
          ? readiness.problems?.[0] || "Telephony not configured"
          : null;

  const status = call?.status || null;
  const isLive = status && !isTerminalStatus(status) && phase !== "error";

  // Notify parent so transcript / memory panels follow the live Twilio session.
  useEffect(() => {
    if (typeof onCallSessionChange !== "function") return;
    onCallSessionChange({
      sessionId: call?.session_id || null,
      callSid: call?.call_sid || null,
      status: status || null,
      phase,
      live: Boolean(isLive),
      customerName: call?.provider_meta?.customer_name || name.trim() || null,
      to: call?.to || null,
    });
  }, [call, status, phase, isLive, name, onCallSessionChange]);

  function handleInitiateCall() {
    if (!name.trim()) {
      setNameError("Enter the customer's name");
      return;
    }
    setNameError(null);
    dial(phone, {
      customerName: name.trim(),
      projectId: projectId || null,
      language: language || null,
    });
  }

  return (
    <section className="panel telephony-panel">
      <header className="panel__header">
        <h2>Call a customer</h2>
        <p>
          Enter a name and number — Initiate places a live Twilio outbound call
          connected to the Sarvam voice agent (STT + TTS).
        </p>
      </header>

      <label className="controls-utterance">
        Customer name
        <input
          type="text"
          value={name}
          placeholder="e.g. Anitha Raman"
          onChange={(e) => setName(e.target.value)}
          disabled={calling || Boolean(disabledReason)}
          autoComplete="name"
        />
      </label>
      {nameError && !name.trim() && (
        <p className="banner banner--error" role="alert">
          {nameError}
        </p>
      )}

      <label className="controls-utterance">
        Customer phone number (E.164)
        <input
          type="tel"
          value={phone}
          placeholder="+919876543210"
          onChange={(e) => setPhone(e.target.value)}
          disabled={calling || Boolean(disabledReason)}
          autoComplete="tel"
          inputMode="tel"
        />
      </label>
      {phoneError && phoneValidationError(phone) && (
        <p className="banner banner--error" role="alert">
          {phoneError}
        </p>
      )}

      <div className="controls-actions">
        <button
          type="button"
          className="btn btn--primary"
          onClick={handleInitiateCall}
          disabled={calling || Boolean(disabledReason)}
          data-testid="initiate-call"
        >
          {calling ? "Initiating…" : "Initiate call"}
        </button>
      </div>

      <details className="advanced-options">
        <summary>Advanced options (optional)</summary>
        <div className="lead-filter-grid">
          <label>
            Project (agent adapts if left on auto)
            <select
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              disabled={calling}
            >
              <option value="">Auto — based on conversation</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Language
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              disabled={calling}
            >
              <option value="ta">Tamil (default · ~90% Tamil / 10% English)</option>
              <option value="en">English</option>
              <option value="tanglish">Tanglish</option>
            </select>
          </label>
        </div>
      </details>

      {disabledReason && <p className="provider-line mono">{disabledReason}</p>}
      {error && (
        <div className="banner banner--error" role="alert">
          {error}
        </div>
      )}

      {call && (
        <div className="call-status mono" data-testid="call-status">
          <p>
            <strong>Status:</strong>{" "}
            <span className={isLive ? "ok" : ""}>{status || "unknown"}</span>
            {isLive ? " · live" : ""}
          </p>
          {call.provider_meta?.customer_name && (
            <p>
              <strong>Customer:</strong> {call.provider_meta.customer_name}
            </p>
          )}
          <p>
            <strong>Call SID:</strong> {call.call_sid}
          </p>
          <p>
            <strong>To:</strong> {call.to} · <strong>From:</strong>{" "}
            {call.from_number || "—"}
          </p>
          {call.session_id && (
            <p>
              <strong>Session:</strong> {call.session_id}
            </p>
          )}
          {call.duration != null && (
            <p>
              <strong>Duration:</strong> {call.duration}s
            </p>
          )}
          {isLive && (
            <p className="ok">
              Agent pipeline: Sarvam STT + Sarvam TTS (transcript syncs below)
            </p>
          )}
        </div>
      )}
    </section>
  );
}
