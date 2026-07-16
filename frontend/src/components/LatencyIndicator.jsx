export default function LatencyIndicator({ loading, latencyMs }) {
  return (
    <div className={`latency ${loading ? "latency--busy" : ""}`} aria-live="polite">
      <span className="latency__dot" />
      <span className="latency__label">
        {loading ? "Processing…" : latencyMs != null ? `${latencyMs} ms` : "Idle"}
      </span>
    </div>
  );
}
