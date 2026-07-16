export default function LoadingIndicator({ loading, latencyMs, apiMode }) {
  return (
    <div className={`loading-indicator ${loading ? "is-busy" : ""}`} aria-live="polite">
      <span className="loading-indicator__dot" />
      <span className="loading-indicator__label">
        {loading ? "Processing…" : latencyMs != null ? `${latencyMs} ms` : "Idle"}
      </span>
      {apiMode && <span className="loading-indicator__mode">{apiMode}</span>}
    </div>
  );
}
