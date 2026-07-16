import { useEffect, useState } from "react";
import {
  checkHealth,
  getApiMode,
  listProjects,
  resetSession,
  sendTurn,
  startSession,
} from "../api/calls";
import CallControls from "../components/CallControls";
import CurrentStateCard from "../components/CurrentStateCard";
import LoadingIndicator from "../components/LoadingIndicator";
import SlotPanel from "../components/SlotPanel";
import SummaryPanel from "../components/SummaryPanel";
import TranscriptPanel from "../components/TranscriptPanel";

const FALLBACK_PROJECTS = [
  { id: "highcity", name: "Casagrand Highcity" },
  { id: "avenuepark", name: "Casagrand Avenuepark" },
  { id: "mercury", name: "Casagrand Mercury" },
];

function deriveCallStatus(session) {
  if (!session) return "idle";
  if (session.call_status) return session.call_status;
  if (session.needs_handoff) return "handoff";
  if (session.flow_bucket === "closing_summary" && session.final_summary) {
    return "completed";
  }
  if (session.last_intent === "out_of_domain") return "fallback";
  return "active";
}

export default function DemoPage() {
  const apiMode = getApiMode();
  const [projects, setProjects] = useState(FALLBACK_PROJECTS);
  const [projectId, setProjectId] = useState("highcity");
  const [language, setLanguage] = useState("en");
  const [utterance, setUtterance] = useState("");
  const [interrupt, setInterrupt] = useState(false);
  const [session, setSession] = useState(null);
  const [reply, setReply] = useState(null);
  const [loading, setLoading] = useState(false);
  const [latencyMs, setLatencyMs] = useState(null);
  const [error, setError] = useState(null);
  const [warning, setWarning] = useState(null);
  const [apiOnline, setApiOnline] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const health = await checkHealth();
        const projectRes = await listProjects();
        if (cancelled) return;
        setApiOnline(health.data?.status === "ok");
        if (projectRes.data?.length) setProjects(projectRes.data);
      } catch (err) {
        if (!cancelled) {
          setApiOnline(false);
          setError(err.message || "Backend unavailable. Start FastAPI on port 8000.");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function run(action) {
    setLoading(true);
    setError(null);
    setWarning(null);
    try {
      const { data, latencyMs: ms } = await action();
      setSession(data.session);
      setReply(data.reply || null);
      setLatencyMs(data.latency_ms ?? ms);
      setWarning(data.warning || null);
      if (data.error) setError(data.error);
      if (data.session?.language) setLanguage(data.session.language);
      if (data.session?.project_id) setProjectId(data.session.project_id);
      return data;
    } catch (err) {
      setError(err.message || "Request failed");
      if (err.latencyMs != null) setLatencyMs(err.latencyMs);
      return null;
    } finally {
      setLoading(false);
    }
  }

  async function handleStart() {
    await run(() => startSession({ projectId, language }));
  }

  async function handleSend() {
    if (!session?.session_id || !utterance.trim()) return;
    const data = await run(() =>
      sendTurn({
        sessionId: session.session_id,
        text: utterance.trim(),
        language,
        interrupt,
      })
    );
    if (data) {
      setUtterance("");
      setInterrupt(false);
    }
  }

  async function handleReset() {
    if (!session?.session_id) return;
    await run(() => resetSession({ sessionId: session.session_id }));
    setUtterance("");
    setInterrupt(false);
  }

  const callStatus = deriveCallStatus(session);
  const faqSource = reply?.faq_source || session?.last_faq_source;
  const providerLine = session
    ? `stt:${session.stt_provider || "—"} · llm:${session.llm_provider || "—"} · tts:${session.tts_provider || "—"}`
    : null;

  return (
    <div className="demo-page">
      <div className="atmosphere" aria-hidden="true" />

      <header className="hero">
        <p className="brand">Casagrand</p>
        <h1>Voice Agent Demo</h1>
        <p className="lede">
          Live call console for Highcity, Avenuepark, and Mercury — English, Tamil,
          and Tanglish across introduction, education, next steps, and closing summary.
        </p>
        <div className="hero__status">
          <LoadingIndicator loading={loading} latencyMs={latencyMs} apiMode={apiMode} />
          <span
            className={`api-chip ${apiOnline ? "ok" : apiOnline === false ? "bad" : ""}`}
          >
            {apiOnline === null
              ? "Checking API…"
              : apiOnline
                ? "Backend online"
                : "Backend offline"}
          </span>
        </div>
        {providerLine && <p className="provider-line mono">{providerLine}</p>}
      </header>

      {error && (
        <div className="banner banner--error" role="alert">
          {error}
        </div>
      )}
      {warning && !error && (
        <div className="banner banner--warn" role="status">
          {warning}
        </div>
      )}

      <main className="demo-grid">
        <CallControls
          projects={projects}
          projectId={projectId}
          language={language}
          utterance={utterance}
          interrupt={interrupt}
          loading={loading || apiOnline === false}
          hasSession={Boolean(session)}
          onProjectChange={setProjectId}
          onLanguageChange={setLanguage}
          onUtteranceChange={setUtterance}
          onInterruptChange={setInterrupt}
          onStart={handleStart}
          onSend={handleSend}
          onReset={handleReset}
        />

        <CurrentStateCard
          session={session}
          callStatus={callStatus}
          faqSource={faqSource}
          handoffReason={session?.handoff_reason}
        />
        <TranscriptPanel turns={session?.transcript} />
        <SlotPanel memory={session?.memory} />
        <SummaryPanel
          summary={session?.final_summary}
          handoffPayload={session?.handoff_payload}
        />
      </main>
    </div>
  );
}
