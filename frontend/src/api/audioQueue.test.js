/**
 * Node tests for sequential WAV chunk playback queue.
 * Run: node --test src/api/audioQueue.test.js
 */

import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { test } from "node:test";
import { WavChunkPlayer } from "./audioQueue.js";

class FakeAudio extends EventEmitter {
  constructor(src) {
    super();
    this.src = src;
    this.paused = true;
    this._ended = false;
  }

  addEventListener(type, handler) {
    this.on(type, handler);
  }

  removeEventListener(type, handler) {
    this.off(type, handler);
  }

  play() {
    this.paused = false;
    return Promise.resolve();
  }

  pause() {
    this.paused = true;
  }

  removeAttribute() {}

  load() {}

  /** Test helper: finish playback. */
  finish() {
    this._ended = true;
    this.emit("ended");
  }
}

function waitMicrotask() {
  return new Promise((resolve) => setImmediate(resolve));
}

test("enqueues chunks and plays them in order without overlap", async () => {
  const created = [];
  const player = new WavChunkPlayer({
    createAudio: (src) => {
      const audio = new FakeAudio(src);
      created.push(audio);
      return audio;
    },
  });

  player.enqueue("AAA", "audio/wav");
  player.enqueue("BBB", "audio/wav");
  player.enqueue("CCC", "audio/wav");

  await waitMicrotask();
  assert.equal(created.length, 1);
  assert.match(created[0].src, /^data:audio\/wav;base64,AAA$/);
  assert.equal(player.pending, 2);
  assert.equal(player.isPlaying, true);

  created[0].finish();
  await waitMicrotask();
  assert.equal(created.length, 2);
  assert.match(created[1].src, /base64,BBB$/);
  assert.equal(player.pending, 1);

  created[1].finish();
  await waitMicrotask();
  assert.equal(created.length, 3);
  assert.match(created[2].src, /base64,CCC$/);

  created[2].finish();
  await waitMicrotask();
  assert.equal(player.pending, 0);
  assert.equal(player.isPlaying, false);
});

test("playback uses wav data URL compatible with HTMLAudioElement", async () => {
  let lastSrc = null;
  const player = new WavChunkPlayer({
    createAudio: (src) => {
      lastSrc = src;
      const audio = new FakeAudio(src);
      queueMicrotask(() => audio.finish());
      return audio;
    },
  });

  player.enqueue("UklGRg==", "audio/wav");
  await waitMicrotask();
  assert.equal(lastSrc, "data:audio/wav;base64,UklGRg==");
});

test("clear drops queued chunks and stops current playback", async () => {
  const created = [];
  const player = new WavChunkPlayer({
    createAudio: (src) => {
      const audio = new FakeAudio(src);
      created.push(audio);
      return audio;
    },
  });

  player.enqueue("ONE", "audio/wav");
  player.enqueue("TWO", "audio/wav");
  await waitMicrotask();
  assert.equal(created.length, 1);
  assert.equal(player.pending, 1);

  player.clear();
  assert.equal(player.pending, 0);
  assert.equal(player.isPlaying, false);
  assert.equal(created[0].paused, true);

  // Finishing a cleared clip must not start the dropped queue.
  created[0].finish();
  await waitMicrotask();
  assert.equal(created.length, 1);
});
