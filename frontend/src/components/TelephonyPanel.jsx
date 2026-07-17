import { useState } from "react";
import { phoneValidationError } from "../api/phone";
import { isTerminalStatus } from "../hooks/callController";
import useTwilioCall from "../hooks/useTwilioCall";

/**
 * Primary customer-facing call form: name + phone number only.
 * The agent introduces itself and explains whichever project the customer
 * asks about during the call; project/language are optional advanced controls.
 */
export default function TelephonyPanel({ projects = [] }) {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [nameError, setNameError] = useState(null);
  const [projectId, setProjectId] = useState("");
  const [language, setLanguage] = useState("");
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

  function handleStartCall() {
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
          Enter a name and number — the agent introduces the visit, answers
          project questions, and closes with next steps.
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
        />
      </label>
      {nameError && !name.trim() && (
        <p className="banner banner--error" role="alert">
          {nameError}
        </p>
      )}

      <label className="controls-utterance">
        Phone number (E.164)
        <input
          type="tel"
          value={phone}
          placeholder="+919876543210"
          onChange={(e) => setPhone(e.target.value)}
          disabled={calling || Boolean(disabledReason)}
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
          onClick={handleStartCall}
          disabled={calling || Boolean(disabledReason)}
        >
          {calling ? "Calling…" : "Start call"}
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
              <option value="">Default (English)</option>
              <option value="en">English</option>
              <option value="ta">Tamil</option>
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
        </div>
      )}
    </section>
  );
}
