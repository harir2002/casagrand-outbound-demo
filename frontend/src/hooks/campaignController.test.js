/**
 * Node tests for the demo-campaign controller (preview → start → poll → done).
 * Run: npm test
 */

import assert from "node:assert/strict";
import { test } from "node:test";
import { createCampaignController } from "./campaignController.js";

function makeFakeTimer() {
  const timers = [];
  return {
    setIntervalFn: (fn, ms) => {
      timers.push({ fn, ms, cleared: false });
      return timers.length - 1;
    },
    clearIntervalFn: (id) => {
      if (timers[id]) timers[id].cleared = true;
    },
    async tick() {
      for (const t of timers) {
        if (!t.cleared) await t.fn();
      }
    },
    timers,
  };
}

function view({ status = "draft", done = false, states = {}, leads = [] } = {}) {
  return {
    campaign: { campaign_id: "cmp-1", status, leads },
    summary: { total: 9, eligible: 4, blocked: 5, states, buckets: {}, done },
  };
}

function makeApi(overrides = {}) {
  return {
    createCampaign: async () => ({ data: view() }),
    startCampaign: async () => ({ data: view({ status: "running" }) }),
    getCampaign: async () => ({ data: view({ status: "running" }) }),
    cancelCampaign: async () => ({ data: view({ status: "cancelled", done: true }) }),
    ...overrides,
  };
}

test("preview snapshots a campaign and reports counts", async () => {
  const phases = [];
  const controller = createCampaignController({
    ...makeApi(),
    onChange: (s) => phases.push(s.phase),
  });
  const state = await controller.preview({ projectId: "highcity" });
  assert.equal(state.phase, "ready");
  assert.equal(state.summary.eligible, 4);
  assert.equal(state.summary.blocked, 5);
  assert.ok(phases.includes("previewing"));
});

test("preview failure surfaces error", async () => {
  const controller = createCampaignController({
    ...makeApi({
      createCampaign: async () => {
        throw new Error("Backend unavailable");
      },
    }),
    onChange: () => {},
  });
  const state = await controller.preview({});
  assert.equal(state.phase, "error");
  assert.match(state.error, /unavailable/i);
});

test("start requires a previewed campaign", async () => {
  const controller = createCampaignController({ ...makeApi(), onChange: () => {} });
  const state = await controller.start();
  assert.equal(state.phase, "error");
  assert.match(state.error, /preview/i);
});

test("start begins polling and finishes when summary reports done", async () => {
  const timer = makeFakeTimer();
  let polls = 0;
  const controller = createCampaignController({
    ...makeApi({
      getCampaign: async () => {
        polls += 1;
        return {
          data:
            polls < 2
              ? view({ status: "running", states: { dialing: 1, pending: 3 } })
              : view({ status: "completed", done: true, states: { completed: 4 } }),
        };
      },
    }),
    onChange: () => {},
    ...timer,
  });

  await controller.preview({});
  await controller.start();
  assert.equal(controller.state.phase, "running");
  assert.equal(timer.timers.length, 1);

  await timer.tick(); // still running
  assert.equal(controller.state.phase, "running");
  assert.equal(controller.state.summary.states.dialing, 1);

  await timer.tick(); // completed
  assert.equal(controller.state.phase, "done");
  assert.equal(controller.state.summary.states.completed, 4);
  assert.equal(timer.timers[0].cleared, true);
});

test("start failure surfaces error without polling", async () => {
  const timer = makeFakeTimer();
  const controller = createCampaignController({
    ...makeApi({
      startCampaign: async () => {
        throw new Error("Campaign already running");
      },
    }),
    onChange: () => {},
    ...timer,
  });
  await controller.preview({});
  const state = await controller.start();
  assert.equal(state.phase, "error");
  assert.equal(timer.timers.length, 0);
});

test("cancel stops polling and marks campaign done", async () => {
  const timer = makeFakeTimer();
  const controller = createCampaignController({
    ...makeApi(),
    onChange: () => {},
    ...timer,
  });
  await controller.preview({});
  await controller.start();
  assert.equal(timer.timers[0].cleared, false);

  const state = await controller.cancel();
  assert.equal(state.phase, "done");
  assert.equal(state.campaign.status, "cancelled");
  assert.equal(timer.timers[0].cleared, true);
});

test("dispose stops active polling", async () => {
  const timer = makeFakeTimer();
  const controller = createCampaignController({
    ...makeApi(),
    onChange: () => {},
    ...timer,
  });
  await controller.preview({});
  await controller.start();
  controller.dispose();
  assert.equal(timer.timers[0].cleared, true);
});
