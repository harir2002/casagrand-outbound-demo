export default function SessionPanel({ session }) {
  if (!session) {
    return (
      <section className="panel session-panel">
        <header className="panel__header">
          <h2>Session</h2>
          <p>Start a call to inspect live state.</p>
        </header>
      </section>
    );
  }

  return (
    <section className="panel session-panel">
      <header className="panel__header">
        <h2>Session</h2>
        <p className="mono">{session.session_id}</p>
      </header>

      <dl className="kv">
        <div>
          <dt>Project</dt>
          <dd>{session.project_id}</dd>
        </div>
        <div>
          <dt>Language</dt>
          <dd>{session.language}</dd>
        </div>
        <div>
          <dt>Flow bucket</dt>
          <dd>
            <span className="pill">{session.flow_bucket}</span>
          </dd>
        </div>
        <div>
          <dt>Last intent</dt>
          <dd>{session.last_intent || "—"}</dd>
        </div>
        <div>
          <dt>FAQ source</dt>
          <dd className="mono">{session.last_faq_source || "—"}</dd>
        </div>
        <div>
          <dt>Handoff</dt>
          <dd>{session.needs_handoff ? "requested" : "no"}</dd>
        </div>
        <div>
          <dt>Interrupted</dt>
          <dd>{session.is_interrupted ? "yes" : "no"}</dd>
        </div>
      </dl>

      {session.final_summary && (
        <div className="summary-box">
          <h3>Final summary</h3>
          <p>{session.final_summary}</p>
        </div>
      )}
    </section>
  );
}
