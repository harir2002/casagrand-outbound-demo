const BUCKET_LABELS = {
  introduction: "Introduction",
  education: "Education",
  next_steps: "Next steps",
  closing_summary: "Closing summary",
};

const STATUS_LABELS = {
  idle: "Idle",
  active: "Active",
  fallback: "Fallback",
  handoff: "Handoff",
  completed: "Completed",
};

export default function CurrentStateCard({ session, callStatus, faqSource, handoffReason }) {
  const bucket = session?.flow_bucket;
  const status = callStatus || session?.call_status || (session ? "active" : "idle");

  return (
    <section className="panel state-card">
      <header className="panel__header">
        <h2>Current state</h2>
        <p>Project, language, bucket, and routing signals.</p>
      </header>

      <div className="state-card__grid">
        <div>
          <span className="meta-label">Project</span>
          <strong>{session?.project_id || "—"}</strong>
        </div>
        <div>
          <span className="meta-label">Language</span>
          <strong>{session?.language || "—"}</strong>
        </div>
        <div>
          <span className="meta-label">Bucket</span>
          <strong>
            {bucket ? (
              <span className={`pill pill--bucket pill--${bucket}`}>
                {BUCKET_LABELS[bucket] || bucket}
              </span>
            ) : (
              "—"
            )}
          </strong>
        </div>
        <div>
          <span className="meta-label">Call status</span>
          <strong>
            <span className={`status status--${status}`}>
              {STATUS_LABELS[status] || status}
            </span>
          </strong>
        </div>
        <div>
          <span className="meta-label">Last intent</span>
          <strong className="mono">{session?.last_intent || "—"}</strong>
        </div>
        <div>
          <span className="meta-label">Handoff</span>
          <strong>
            {session?.needs_handoff
              ? handoffReason || session?.handoff_reason || "requested"
              : "no"}
          </strong>
        </div>
      </div>

      <div className="faq-source">
        <span className="meta-label">FAQ source</span>
        <p className="mono">{faqSource || session?.last_faq_source || "—"}</p>
      </div>

      {session?.session_id && (
        <p className="session-id mono">session: {session.session_id}</p>
      )}
    </section>
  );
}
