export default function SummaryPanel({ summary, handoffPayload }) {
  return (
    <section className="panel summary-panel">
      <header className="panel__header">
        <h2>Closing summary</h2>
        <p>Final recap produced in the closing bucket.</p>
      </header>

      {summary ? (
        <p className="summary-text">{summary}</p>
      ) : (
        <p className="muted">Summary appears after the call reaches closing.</p>
      )}

      {handoffPayload && (
        <div className="handoff-box">
          <h3>Handoff payload</h3>
          <pre className="mono">{JSON.stringify(handoffPayload, null, 2)}</pre>
        </div>
      )}
    </section>
  );
}
