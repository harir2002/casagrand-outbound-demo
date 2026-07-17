/**
 * Framework-agnostic demo-campaign controller (testable in Node).
 * Phases: idle → previewing → ready → running → done (or error).
 */

export function createCampaignController({
  createCampaign,
  startCampaign,
  getCampaign,
  cancelCampaign,
  onChange,
  pollMs = 2000,
  setIntervalFn = (...args) => setInterval(...args),
  clearIntervalFn = (id) => clearInterval(id),
}) {
  let state = {
    phase: "idle", // idle | previewing | ready | running | done | error
    campaign: null,
    summary: null,
    error: null,
  };
  let pollId = null;

  function emit(patch) {
    state = { ...state, ...patch };
    if (typeof onChange === "function") onChange(state);
    return state;
  }

  function stopPolling() {
    if (pollId != null) {
      clearIntervalFn(pollId);
      pollId = null;
    }
  }

  function applyView(view, phaseWhenLive) {
    const done = Boolean(view.summary?.done);
    return emit({
      campaign: view.campaign,
      summary: view.summary,
      phase: done ? "done" : phaseWhenLive,
    });
  }

  function startPolling(campaignId) {
    stopPolling();
    pollId = setIntervalFn(async () => {
      try {
        const { data } = await getCampaign(campaignId);
        applyView(data, "running");
        if (data.summary?.done) stopPolling();
      } catch {
        // Transient polling failures are ignored; next tick retries
      }
    }, pollMs);
  }

  return {
    get state() {
      return state;
    },

    /** Apply filters and snapshot a campaign (no dialing). */
    async preview(filters) {
      emit({ phase: "previewing", error: null, campaign: null, summary: null });
      try {
        const { data } = await createCampaign(filters);
        return applyView(data, "ready");
      } catch (err) {
        return emit({ phase: "error", error: err.message || "Preview failed" });
      }
    },

    /** Start dialing the previewed campaign's eligible leads. */
    async start(options = {}) {
      const campaignId = state.campaign?.campaign_id;
      if (!campaignId || state.phase !== "ready") {
        return emit({ phase: "error", error: "Preview a campaign before starting" });
      }
      emit({ error: null });
      try {
        const { data } = await startCampaign(campaignId, options);
        applyView(data, "running");
        if (!data.summary?.done) startPolling(campaignId);
      } catch (err) {
        emit({ phase: "error", error: err.message || "Campaign start failed" });
      }
      return state;
    },

    /** Cancel a running campaign; keeps last known progress on screen. */
    async cancel() {
      const campaignId = state.campaign?.campaign_id;
      if (!campaignId) return state;
      try {
        const { data } = await cancelCampaign(campaignId);
        stopPolling();
        return applyView(data, "done");
      } catch (err) {
        return emit({ error: err.message || "Cancel failed" });
      }
    },

    dispose() {
      stopPolling();
    },
  };
}
