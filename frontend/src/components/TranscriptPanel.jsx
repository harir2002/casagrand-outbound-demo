export default function TranscriptPanel({ turns }) {
  const items = turns || [];

  return (
    <section className="panel transcript-panel">
      <header className="panel__header">
        <h2>Live transcript</h2>
        <p>User and agent turns for this call.</p>
      </header>

      <ol className="transcript-list">
        {items.length === 0 && <li className="muted">Start a session to see turns.</li>}
        {items.map((turn, idx) => (
          <li key={`${turn.timestamp || idx}-${idx}`} className={`turn turn--${turn.role}`}>
            <div className="turn__meta">
              <span className="turn__role">{turn.role}</span>
              {turn.intent && <span className="turn__intent">{turn.intent}</span>}
              {turn.language && <span className="turn__lang">{turn.language}</span>}
            </div>
            <p>{turn.text}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
