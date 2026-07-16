export default function MemorySlots({ memory }) {
  const slots = memory || {};
  const entries = [
    ["Caller name", slots.caller_name],
    ["Callback time", slots.preferred_callback_time],
    ["Site visit interest", slots.site_visit_interest == null ? null : String(slots.site_visit_interest)],
    ["Preferred visit day", slots.site_visit_preferred_day],
    ["Budget mentioned", slots.budget_mentioned],
  ];

  return (
    <section className="panel memory">
      <header className="panel__header">
        <h2>Memory slots</h2>
        <p>Extracted session memory.</p>
      </header>
      <ul className="memory__list">
        {entries.map(([label, value]) => (
          <li key={label}>
            <span>{label}</span>
            <strong>{value || "—"}</strong>
          </li>
        ))}
      </ul>
      {slots.notes?.length > 0 && (
        <div className="memory__notes">
          <h3>Notes</h3>
          <ul>
            {slots.notes.map((note, i) => (
              <li key={i}>{note}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
