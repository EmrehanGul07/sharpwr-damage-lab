import type { BuildInput } from "./build";
import type { Target } from "./attacks";
export interface FightSettings {
  rotation: "auto" | "QWE" | "QEW" | "WQE" | "WEQ" | "EQW" | "EWQ";
  movement: "auto" | "skill_envelope" | "aa_envelope" | "close_envelope";
  ultimate: "immediate" | "after_basics";
  distance?: number;
}
export interface FightRequest {
  build: BuildInput;
  target: Target;
  settings?: FightSettings;
}
export interface FightResult {
  summary: {
    TTK: number | null;
    Damage: number;
    DPS: number;
    Rotation: string;
    Movement: string;
  };
  replay: Record<string, unknown>;
}
let worker: Worker | null = null;
let idle: ReturnType<typeof setTimeout> | undefined;
let activeCancel: (() => void) | null = null;
let nextId = 0;
/** Keep the initialized runtime warm briefly; cancellation/navigation release it immediately. */
export function disposeFightEngine(): void {
  if (activeCancel) {
    activeCancel();
    return;
  }
  clearTimeout(idle);
  worker?.terminate();
  worker = null;
}
export function runFight(
  request: FightRequest,
  status: (message: string) => void,
  signal?: AbortSignal,
): Promise<FightResult> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted)
      return reject(new DOMException("Cancelled", "AbortError"));
    if (activeCancel) return reject(Error("A fight is already running"));
    clearTimeout(idle);
    worker ??= new Worker(new URL("./fight-worker.ts", import.meta.url), {
      type: "module",
    });
    const current = worker,
      id = ++nextId;
    let settled = false;
    const finish = (error?: Error, result?: FightResult) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      signal?.removeEventListener("abort", cancel);
      activeCancel = null;
      current.onmessage = null;
      current.onerror = null;
      if (error) {
        disposeFightEngine();
        reject(error);
      } else {
        idle = setTimeout(disposeFightEngine, 30_000);
        resolve(result!);
      }
    };
    const cancel = () => finish(new DOMException("Cancelled", "AbortError"));
    const timeout = setTimeout(
      () => finish(Error("Fight timed out. Try a smaller target.")),
      180_000,
    );
    activeCancel = cancel;
    signal?.addEventListener("abort", cancel, { once: true });
    current.onmessage = (event) => {
      if (event.data.id !== id) return;
      if (event.data.status) status(event.data.status);
      else if (event.data.error) finish(Error(event.data.error));
      else finish(undefined, event.data.result);
    };
    current.onerror = (event) =>
      finish(Error(event.message || "Offline engine could not start"));
    current.postMessage({
      id,
      base: new URL("./", document.baseURI).href,
      request,
    });
  });
}
