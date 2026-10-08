import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { disposeFightEngine, runFight } from "../src/engine/fight";
const created: FakeWorker[] = [];
class FakeWorker {
  onmessage: ((event: { data: Record<string, unknown> }) => void) | null = null;
  onerror: ((event: { message: string }) => void) | null = null;
  request: { id: number } | null = null;
  terminated = false;
  constructor() {
    created.push(this);
  }
  postMessage(request: { id: number }) {
    this.request = request;
  }
  terminate() {
    this.terminated = true;
  }
  complete() {
    this.onmessage?.({
      data: {
        id: this.request!.id,
        result: { summary: { Damage: 123 }, replay: {} },
      },
    });
  }
}
const request = {
  build: { champion: "Ezreal", level: 15, items: [], boots: null },
  target: { health: 3000, armor: 100, magicResist: 80 },
};
beforeEach(() => {
  vi.useFakeTimers();
  vi.stubGlobal("Worker", FakeWorker);
  vi.stubGlobal("document", { baseURI: "https://localhost/" });
  created.length = 0;
});
afterEach(() => {
  disposeFightEngine();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});
describe("warm fight runtime", () => {
  it("reuses a completed worker and releases it after 30 seconds idle", async () => {
    const first = runFight(request, () => {});
    created[0].complete();
    await first;
    const second = runFight(request, () => {});
    expect(created).toHaveLength(1);
    created[0].complete();
    await second;
    expect(created[0].terminated).toBe(false);
    vi.advanceTimersByTime(30000);
    expect(created[0].terminated).toBe(true);
  });
  it("cancellation terminates active WASM and creates a clean worker next time", async () => {
    const controller = new AbortController(),
      first = runFight(request, () => {}, controller.signal);
    controller.abort();
    await expect(first).rejects.toMatchObject({ name: "AbortError" });
    expect(created[0].terminated).toBe(true);
    const second = runFight(request, () => {});
    expect(created).toHaveLength(2);
    created[1].complete();
    await second;
    disposeFightEngine();
    expect(created[1].terminated).toBe(true);
  });
});
