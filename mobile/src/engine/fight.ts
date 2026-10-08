import type { BuildInput } from "./build";
import type { Target } from "./attacks";
export interface FightRequest {
  build: BuildInput;
  target: Target;
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
/** One isolated worker per operation: cancellation also interrupts a long Python calculation. */
export function runFight(
  request: FightRequest,
  status: (message: string) => void,
  signal?: AbortSignal,
): Promise<FightResult> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted)
      return reject(new DOMException("Cancelled", "AbortError"));
    const worker = new Worker(new URL("./fight-worker.ts", import.meta.url), {
      type: "module",
    });
    const finish = (error?: Error, result?: FightResult) => {
      clearTimeout(timeout);
      signal?.removeEventListener("abort", cancel);
      worker.terminate();
      if (error) reject(error);
      else resolve(result!);
    };
    const cancel = () => finish(new DOMException("Cancelled", "AbortError"));
    const timeout = setTimeout(
      () => finish(Error("Fight timed out. Try again with a smaller target.")),
      180_000,
    );
    signal?.addEventListener("abort", cancel, { once: true });
    worker.onmessage = (event) => {
      if (event.data.status) status(event.data.status);
      else if (event.data.error) finish(Error(event.data.error));
      else finish(undefined, event.data.result);
    };
    worker.onerror = (event) =>
      finish(Error(event.message || "Offline engine could not start"));
    worker.postMessage({
      id: 1,
      base: new URL("./", document.baseURI).href,
      request,
    });
  });
}
