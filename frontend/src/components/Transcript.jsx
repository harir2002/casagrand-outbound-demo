export default function Transcript({ turns }) {
  return (
    <section className="panel transcript">
      <header className="panel__header">
        <h2>Transcript</h2>
        <p>User and agent turns for this session.</p>
      </header>
      <ol className="transcript__list">
        {(turns || []).length === 0 && <li className="muted">No turns yet.</li>}
        {(turns || []).map((turn, idx) => (
          <li key={`${turn.timestamp}-${idx}`} className={`turn turn--${turn.role}`}>
            <div className="turn__meta">
              <span className="turn__role">{turn.role}</span>
              {turn.intent && <span className="turn__intent">{turn.intent}</span>}
            </div>
            <p>{turn.text}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
