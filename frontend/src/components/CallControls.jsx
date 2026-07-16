export default function CallControls({
  projects,
  projectId,
  language,
  utterance,
  interrupt,
  loading,
  hasSession,
  onProjectChange,
  onLanguageChange,
  onUtteranceChange,
  onInterruptChange,
  onStart,
  onSend,
  onReset,
}) {
  return (
    <section className="panel call-controls">
      <header className="panel__header">
        <h2>Call controls</h2>
        <p>Start, simulate a user turn, or reset the session.</p>
      </header>

      <div className="controls-row">
        <label>
          Project
          <select
            value={projectId}
            onChange={(e) => onProjectChange(e.target.value)}
            disabled={loading || hasSession}
          >
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
            onChange={(e) => onLanguageChange(e.target.value)}
            disabled={loading}
          >
            <option value="en">English</option>
            <option value="ta">Tamil</option>
            <option value="tanglish">Tanglish</option>
          </select>
        </label>
      </div>

      <label className="controls-utterance">
        Simulate user turn
        <textarea
          rows={3}
          value={utterance}
          onChange={(e) => onUtteranceChange(e.target.value)}
          placeholder="e.g. Tell me about pricing / site visit saturday / Switch to Tamil"
          disabled={loading || !hasSession}
        />
      </label>

      <label className="controls-check">
        <input
          type="checkbox"
          checked={interrupt}
          onChange={(e) => onInterruptChange(e.target.checked)}
          disabled={loading || !hasSession}
        />
        Mark as interruption
      </label>

      <div className="controls-actions">
        {!hasSession ? (
          <button type="button" className="btn btn--primary" onClick={onStart} disabled={loading}>
            Start session
          </button>
        ) : (
          <>
            <button
              type="button"
              className="btn btn--primary"
              onClick={onSend}
              disabled={loading || !utterance.trim()}
            >
              Simulate user turn
            </button>
            <button type="button" className="btn btn--ghost" onClick={onReset} disabled={loading}>
              Reset
            </button>
          </>
        )}
      </div>
    </section>
  );
}
