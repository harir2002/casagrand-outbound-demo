export default function SlotPanel({ memory }) {
  const slots = memory || {};
  const entries = [
    ["Caller name", slots.caller_name],
    ["Callback time", slots.preferred_callback_time],
    [
      "Site visit interest",
      slots.site_visit_interest == null ? null : String(slots.site_visit_interest),
    ],
    ["Preferred visit day", slots.site_visit_preferred_day],
    ["Budget mentioned", slots.budget_mentioned],
    [
      "Brochure requested",
      slots.brochure_requested == null ? null : String(slots.brochure_requested),
    ],
  ];

  return (
    <section className="panel slot-panel">
      <header className="panel__header">
        <h2>Memory slots</h2>
        <p>Extracted values from the active session.</p>
      </header>

      <ul className="slot-list">
        {entries.map(([label, value]) => (
          <li key={label}>
            <span>{label}</span>
            <strong>{value || "—"}</strong>
          </li>
        ))}
      </ul>

      {slots.notes?.length > 0 && (
        <div className="slot-notes">
          <h3>Notes</h3>
          <ul>
            {slots.notes.map((note, idx) => (
              <li key={idx}>{note}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
