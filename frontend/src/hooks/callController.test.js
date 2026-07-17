/**
 * Node tests for the outbound-call controller (call form behavior).
 * Run: npm test
 */

import assert from "node:assert/strict";
import { test } from "node:test";
import { createCallController, isTerminalStatus } from "./callController.js";

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

test("isTerminalStatus classifies statuses", () => {
  assert.equal(isTerminalStatus("completed"), true);
  assert.equal(isTerminalStatus("no-answer"), true);
  assert.equal(isTerminalStatus("in-progress"), false);
  assert.equal(isTerminalStatus(null), false);
});

test("dial rejects invalid phone without calling backend", async () => {
  let started = false;
  const states = [];
  const controller = createCallController({
    startCall: async () => {
      started = true;
      return { data: {} };
    },
    fetchStatus: async () => ({ data: {} }),
    onChange: (s) => states.push(s),
  });

  const state = await controller.dial("12345");
  assert.equal(started, false);
  assert.match(state.phoneError, /must start with \+/i);
  assert.equal(state.phase, "idle");
});

test("dial submits customer name + normalized number together", async () => {
  const timer = makeFakeTimer();
  const seenPhases = [];
  let sentBody = null;
  const controller = createCallController({
    startCall: async (body) => {
      sentBody = body;
      return {
        data: { call_sid: "CAtest", status: "queued", to: body.to },
      };
    },
    fetchStatus: async () => ({ data: { status: "queued" } }),
    onChange: (s) => seenPhases.push(s.phase),
    ...timer,
  });

  const state = await controller.dial("+91 98888 77777", {
    customerName: "Anitha Raman",
  });
  assert.equal(sentBody.to, "+919888877777");
  assert.equal(sentBody.customerName, "Anitha Raman");
  assert.equal(state.phase, "active");
  assert.equal(state.call.call_sid, "CAtest");
  assert.ok(seenPhases.includes("calling"));
  assert.equal(timer.timers.length, 1); // polling started
  controller.dispose();
});

test("polling updates status and stops on terminal state", async () => {
  const timer = makeFakeTimer();
  const statuses = ["ringing", "in-progress", "completed"];
  let idx = 0;
  const controller = createCallController({
    startCall: async () => ({ data: { call_sid: "CAtest", status: "queued" } }),
    fetchStatus: async () => ({
      data: { status: statuses[Math.min(idx++, statuses.length - 1)], terminal: idx >= 3 },
    }),
    onChange: () => {},
    ...timer,
  });

  await controller.dial("+919888877777");
  await timer.tick(); // ringing
  assert.equal(controller.state.call.status, "ringing");
  assert.equal(controller.state.phase, "active");

  await timer.tick(); // in-progress
  assert.equal(controller.state.call.status, "in-progress");

  await timer.tick(); // completed → terminal, polling cleared
  assert.equal(controller.state.call.status, "completed");
  assert.equal(controller.state.phase, "done");
  assert.equal(timer.timers[0].cleared, true);
});

test("backend error surfaces as error state", async () => {
  const controller = createCallController({
    startCall: async () => {
      throw new Error("Twilio create call failed (401)");
    },
    fetchStatus: async () => ({ data: {} }),
    onChange: () => {},
  });

  const state = await controller.dial("+919888877777");
  assert.equal(state.phase, "error");
  assert.match(state.error, /401/);
  assert.equal(state.call, null);
});

test("dialLead sends lead_id without phone validation and tracks the call", async () => {
  const timer = makeFakeTimer();
  let sentBody = null;
  const controller = createCallController({
    startCall: async (body) => {
      sentBody = body;
      return { data: { call_sid: "CAlead", status: "queued", to: "+919876543210" } };
    },
    fetchStatus: async () => ({ data: { status: "ringing" } }),
    onChange: () => {},
    ...timer,
  });

  const state = await controller.dialLead("lead-anitha");
  assert.equal(sentBody.leadId, "lead-anitha");
  assert.equal(sentBody.to, undefined);
  assert.equal(state.phase, "active");
  assert.equal(state.call.call_sid, "CAlead");
  assert.equal(timer.timers.length, 1); // polling started
  controller.dispose();
});

test("dialLead surfaces blocked-lead errors from the backend", async () => {
  const controller = createCallController({
    startCall: async () => {
      throw new Error("Lead lead-priya is not callable: Lead is on the do-not-call list");
    },
    fetchStatus: async () => ({ data: {} }),
    onChange: () => {},
  });

  const state = await controller.dialLead("lead-priya");
  assert.equal(state.phase, "error");
  assert.match(state.error, /do-not-call/);
  assert.equal(state.call, null);
});

test("dispose stops active polling", async () => {
  const timer = makeFakeTimer();
  const controller = createCallController({
    startCall: async () => ({ data: { call_sid: "CAtest", status: "queued" } }),
    fetchStatus: async () => ({ data: { status: "ringing" } }),
    onChange: () => {},
    ...timer,
  });
  await controller.dial("+919888877777");
  assert.equal(timer.timers[0].cleared, false);
  controller.dispose();
  assert.equal(timer.timers[0].cleared, true);
});
