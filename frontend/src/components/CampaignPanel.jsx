import { useEffect, useMemo, useState } from "react";
import {
  cancelCampaign,
  createCampaign,
  getCampaign,
  startCampaign,
} from "../api/calls";
import { createCampaignController } from "../hooks/campaignController";

const LEAD_STATUSES = [
  { value: "new", label: "New" },
  { value: "contacted", label: "Contacted" },
  { value: "interested", label: "Interested" },
  { value: "qualified", label: "Qualified" },
  { value: "converted", label: "Converted" },
];

const BUCKET_LABELS = {
  introduction: "Introduction",
  education: "Education",
  next_steps: "Next steps",
  closing_summary: "Closing & summary",
};

const STATE_LABELS = {
  pending: "Pending",
  dialing: "Dialing",
  connected: "Connected",
  completed: "Completed",
  blocked: "Blocked",
  failed: "Failed",
};

export default function CampaignPanel({ projects = [] }) {
  const [projectId, setProjectId] = useState("");
  const [language, setLanguage] = useState("");
  const [status, setStatus] = useState("");
  const [requireConsent, setRequireConsent] = useState(true);
  const [excludeDnc, setExcludeDnc] = useState(true);
  const [respectCallWindow, setRespectCallWindow] = useState(true);
  const [view, setView] = useState({
    phase: "idle",
    campaign: null,
    summary: null,
    error: null,
  });

  const controller = useMemo(
    () =>
      createCampaignController({
        createCampaign,
        startCampaign,
        getCampaign,
        cancelCampaign,
        onChange: setView,
      }),
    []
  );

  useEffect(() => () => controller.dispose(), [controller]);

  const { phase, campaign, summary, error } = view;
  const busy = phase === "previewing";
  const running = phase === "running";
  const leads = campaign?.leads || [];
  const eligibleLeads = leads.filter((l) => l.eligible_at_creation);
  const blockedLeads = leads.filter((l) => !l.eligible_at_creation);

  function handlePreview() {
    controller.preview({
      projectId: projectId || null,
      language: language || null,
      statuses: status ? [status] : null,
      requireConsent,
      excludeDnc,
      respectCallWindow,
    });
  }

  return (
    <section className="panel campaign-panel">
      <header className="panel__header">
        <h2>Demo campaign</h2>
        <p>Filter leads, preview eligibility, then dial eligible leads one by one.</p>
      </header>

      <div className="lead-filter-grid">
        <label>
          Project
          <select
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            disabled={running}
          >
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
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            disabled={running}
          >
            <option value="">Any language</option>
            <option value="en">English</option>
            <option value="ta">Tamil</option>
            <option value="tanglish">Tanglish</option>
          </select>
        </label>
        <label>
          Lead status
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            disabled={running}
          >
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
            disabled={running}
          />
          Require consent
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={excludeDnc}
            onChange={(e) => setExcludeDnc(e.target.checked)}
            disabled={running}
          />
          Exclude DNC
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={respectCallWindow}
            onChange={(e) => setRespectCallWindow(e.target.checked)}
            disabled={running}
          />
          Respect call window
        </label>
      </div>

      <div className="controls-actions">
        <button
          type="button"
          className="btn"
          onClick={handlePreview}
          disabled={busy || running}
        >
          {busy ? "Previewing…" : "Preview campaign"}
        </button>
        {phase === "ready" && (
          <button
            type="button"
            className="btn btn--primary"
            onClick={() => controller.start()}
          >
            Start Demo Campaign
          </button>
        )}
        {running && (
          <button type="button" className="btn" onClick={() => controller.cancel()}>
            Cancel campaign
          </button>
        )}
      </div>

      {error && (
        <div className="banner banner--error" role="alert">
          {error}
        </div>
      )}

      {summary && (
        <div className="campaign-summary">
          <div className="campaign-chips">
            <span className="chip">Total {summary.total}</span>
            <span className="chip chip--ok">Eligible {summary.eligible}</span>
            <span className="chip chip--warn">Blocked {summary.blocked}</span>
            {running && <span className="chip chip--live">Running…</span>}
            {phase === "done" && (
              <span className="chip">
                {campaign?.status === "cancelled" ? "Cancelled" : "Finished"}
              </span>
            )}
          </div>
          {Object.keys(summary.buckets || {}).length > 0 && (
            <p className="provider-line mono">
              Buckets:{" "}
              {Object.entries(summary.buckets)
                .map(([bucket, count]) => `${BUCKET_LABELS[bucket] || bucket} ×${count}`)
                .join(" · ")}
            </p>
          )}
        </div>
      )}

      {leads.length > 0 && (
        <div className="lead-results">
          {eligibleLeads.map((lead) => (
            <div className="lead-row" key={lead.lead_id}>
              <div className="lead-row__info">
                <strong>{lead.name}</strong>
                <span className="mono">
                  {lead.phone} · {lead.project_id} · {lead.language}
                </span>
                <span className="lead-bucket">
                  {lead.bucket ? BUCKET_LABELS[lead.bucket] || lead.bucket : "—"}
                </span>
                {lead.call_sid && (
                  <span className="mono">
                    {lead.call_sid}
                    {lead.duration ? ` · ${lead.duration}s` : ""}
                  </span>
                )}
                {lead.error && <span className="lead-block-reasons">{lead.error}</span>}
                {lead.state === "blocked" && lead.reasons?.length > 0 && (
                  <span className="lead-block-reasons">
                    {lead.reasons.map((r) => r.message).join("; ")}
                  </span>
                )}
              </div>
              <span className={`state-badge state-badge--${lead.state}`}>
                {STATE_LABELS[lead.state] || lead.state}
              </span>
            </div>
          ))}

          {blockedLeads.length > 0 && (
            <details className="campaign-blocked">
              <summary>
                {blockedLeads.length} lead{blockedLeads.length === 1 ? "" : "s"} blocked
                by filters
              </summary>
              {blockedLeads.map((lead) => (
                <div className="lead-row lead-row--blocked" key={lead.lead_id}>
                  <div className="lead-row__info">
                    <strong>{lead.name}</strong>
                    <span className="mono">{lead.phone}</span>
                    <span className="lead-block-reasons">
                      {lead.reasons.map((r) => r.message).join("; ")}
                    </span>
                  </div>
                  <span className="state-badge state-badge--blocked">Blocked</span>
                </div>
              ))}
            </details>
          )}
        </div>
      )}
    </section>
  );
}
