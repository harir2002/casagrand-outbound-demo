import { useState } from "react";
import { filterLeads } from "../api/calls";
import { isTerminalStatus } from "../hooks/callController";
import useTwilioCall from "../hooks/useTwilioCall";

const LEAD_STATUSES = [
  { value: "new", label: "New" },
  { value: "contacted", label: "Contacted" },
  { value: "interested", label: "Interested" },
  { value: "qualified", label: "Qualified" },
  { value: "converted", label: "Converted" },
  { value: "not_interested", label: "Not interested" },
];

const BUCKET_LABELS = {
  introduction: "Introduction",
  education: "Education",
  next_steps: "Next steps",
  closing_summary: "Closing & summary",
};

export default function LeadFilterPanel({ projects = [] }) {
  const [projectId, setProjectId] = useState("");
  const [language, setLanguage] = useState("");
  const [status, setStatus] = useState("");
  const [requireConsent, setRequireConsent] = useState(true);
  const [excludeDnc, setExcludeDnc] = useState(true);
  const [respectCallWindow, setRespectCallWindow] = useState(true);
  const [result, setResult] = useState(null);
  const [filtering, setFiltering] = useState(false);
  const [filterError, setFilterError] = useState(null);
  const [showBlocked, setShowBlocked] = useState(false);
  const [activeLeadId, setActiveLeadId] = useState(null);

  const { readiness, call, error, calling, dialLead } = useTwilioCall({});

  async function applyFilters() {
    setFiltering(true);
    setFilterError(null);
    try {
      const { data } = await filterLeads({
        projectId: projectId || null,
        language: language || null,
        statuses: status ? [status] : null,
        requireConsent,
        excludeDnc,
        respectCallWindow,
      });
      setResult(data);
    } catch (err) {
      setFilterError(err.message || "Filtering failed");
      setResult(null);
    } finally {
      setFiltering(false);
    }
  }

  async function handleCall(lead) {
    setActiveLeadId(lead.lead_id);
    await dialLead(lead.lead_id);
  }

  const telephonyReady = readiness?.enabled && readiness?.ready;
  const callStatus = call?.status || null;
  const isLive = callStatus && !isTerminalStatus(callStatus);

  return (
    <section className="panel lead-filter-panel">
      <header className="panel__header">
        <h2>Demo lead filters</h2>
        <p>Filter the demo lead list, then call only eligible leads.</p>
      </header>

      <div className="lead-filter-grid">
        <label>
          Project
          <select value={projectId} onChange={(e) => setProjectId(e.target.value)}>
            <option value="">Any project</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Language
          <select value={language} onChange={(e) => setLanguage(e.target.value)}>
            <option value="">Any language</option>
            <option value="en">English</option>
            <option value="ta">Tamil</option>
            <option value="tanglish">Tanglish</option>
          </select>
        </label>
        <label>
          Lead status
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">Any status</option>
            {LEAD_STATUSES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="lead-filter-flags">
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={requireConsent}
            onChange={(e) => setRequireConsent(e.target.checked)}
          />
          Require consent
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={excludeDnc}
            onChange={(e) => setExcludeDnc(e.target.checked)}
          />
          Exclude DNC
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={respectCallWindow}
            onChange={(e) => setRespectCallWindow(e.target.checked)}
          />
          Respect call window
        </label>
      </div>

      <div className="controls-actions">
        <button
          type="button"
          className="btn btn--primary"
          onClick={applyFilters}
          disabled={filtering}
        >
          {filtering ? "Filtering…" : "Apply filters"}
        </button>
        {result && (
          <span className="lead-count mono">
            {result.passed} of {result.total} leads eligible
          </span>
        )}
      </div>

      {filterError && (
        <div className="banner banner--error" role="alert">
          {filterError}
        </div>
      )}
      {error && (
        <div className="banner banner--error" role="alert">
          {error}
        </div>
      )}

      {result && (
        <div className="lead-results">
          {result.eligible.length === 0 && (
            <p className="provider-line mono">No leads passed the current filters.</p>
          )}
          {result.eligible.map(({ lead, bucket }) => (
            <div className="lead-row" key={lead.lead_id}>
              <div className="lead-row__info">
                <strong>{lead.name}</strong>
                <span className="mono">{lead.phone}</span>
                <span className="mono">
                  {lead.project_id} · {lead.language} · {lead.status}
                </span>
                <span className="lead-bucket">{BUCKET_LABELS[bucket] || bucket}</span>
              </div>
              <button
                type="button"
                className="btn"
                onClick={() => handleCall(lead)}
                disabled={calling || !telephonyReady}
                title={telephonyReady ? "" : "Twilio not configured"}
              >
                {calling && activeLeadId === lead.lead_id ? "Calling…" : "Call"}
              </button>
              {call && activeLeadId === lead.lead_id && (
                <span className={`mono lead-call-status ${isLive ? "ok" : ""}`}>
                  {call.call_sid ? `${call.call_sid} · ` : ""}
                  {callStatus || "queued"}
                </span>
              )}
            </div>
          ))}

          {result.blocked.length > 0 && (
            <button
              type="button"
              className="btn btn--ghost"
              onClick={() => setShowBlocked((v) => !v)}
            >
              {showBlocked ? "Hide" : "Show"} {result.blocked_count} blocked lead
              {result.blocked_count === 1 ? "" : "s"}
            </button>
          )}
          {showBlocked &&
            result.blocked.map(({ lead, reasons }) => (
              <div className="lead-row lead-row--blocked" key={lead.lead_id}>
                <div className="lead-row__info">
                  <strong>{lead.name}</strong>
                  <span className="mono">{lead.phone}</span>
                  <span className="lead-block-reasons">
                    {reasons.map((r) => r.message).join("; ")}
                  </span>
                </div>
              </div>
            ))}
        </div>
      )}
    </section>
  );
}
