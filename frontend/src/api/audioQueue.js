/**
 * Sequential WAV/PCM chunk player.
 * Queues base64 audio blobs and plays them one-at-a-time (no overlap).
 */

export class WavChunkPlayer {
  /**
   * @param {{ createAudio?: (src: string) => HTMLAudioElement }} [options]
   */
  constructor(options = {}) {
    this._queue = [];
    this._playing = false;
    this._current = null;
    this._generation = 0;
    this._createAudio =
      typeof options.createAudio === "function"
        ? options.createAudio
        : (src) => new Audio(src);
  }

  /** Number of chunks waiting (not including the one currently playing). */
  get pending() {
    return this._queue.length;
  }

  get isPlaying() {
    return this._playing;
  }

  /**
   * Enqueue a base64 audio chunk for sequential playback.
   * @param {string} audioBase64
   * @param {string} [mimeType]
   */
  enqueue(audioBase64, mimeType = "audio/wav") {
    if (!audioBase64) return;
    this._queue.push({
      audioBase64,
      mimeType: mimeType || "audio/wav",
    });
    void this._pump();
  }

  /** Stop current playback and drop any queued chunks (e.g. new turn / interrupt). */
  clear() {
    this._generation += 1;
    this._queue = [];
    const current = this._current;
    this._current = null;
    this._playing = false;
    if (current) {
      try {
        current.pause();
        current.removeAttribute("src");
        current.load?.();
      } catch {
        /* ignore */
      }
    }
  }

  async _pump() {
    if (this._playing) return;
    this._playing = true;
    const gen = this._generation;
    while (this._queue.length > 0 && gen === this._generation) {
      const item = this._queue.shift();
      await this._playOne(item, gen);
    }
    if (gen === this._generation) {
      this._playing = false;
    }
  }

  _playOne(item, gen) {
    return new Promise((resolve) => {
      if (gen !== this._generation) {
        resolve();
        return;
      }
      let settled = false;
      const finish = () => {
        if (settled) return;
        settled = true;
        if (this._current === audio) this._current = null;
        resolve();
      };

      let audio;
      try {
        const src = `data:${item.mimeType};base64,${item.audioBase64}`;
        audio = this._createAudio(src);
        this._current = audio;
        if (typeof audio.addEventListener === "function") {
          audio.addEventListener("ended", finish, { once: true });
          audio.addEventListener("error", finish, { once: true });
        } else if (typeof audio.on === "function") {
          audio.once("ended", finish);
          audio.once("error", finish);
        }
        const playResult = audio.play?.();
        if (playResult && typeof playResult.then === "function") {
          playResult.catch(finish);
        }
      } catch {
        finish();
      }
    });
  }
}

/** Shared demo player — one sequential stream across turn chunks. */
export const playbackQueue = new WavChunkPlayer();
