/// <reference lib="webworker" />
// The runtime lives beside the app, never on a CDN. Initialization is shared between fights.
import type { PyodideInterface } from "pyodide";
let runtime: Promise<PyodideInterface> | null = null;
let busy = false;
async function initialize(base: string): Promise<PyodideInterface> {
  const url = new URL("engine/", base).href;
  const { loadPyodide } = await import(/* @vite-ignore */ `${url}pyodide.mjs`);
  const py: PyodideInterface = await loadPyodide({ indexURL: url });
  const response = await fetch(`${url}sources.json`);
  if (!response.ok) throw Error(`Engine sources HTTP ${response.status}`);
  const sources: Record<string, string> = await response.json();
  py.FS.mkdirTree("/sharpwr");
  for (const [path, content] of Object.entries(sources)) {
    const destination = `/sharpwr/${path}`;
    py.FS.mkdirTree(destination.slice(0, destination.lastIndexOf("/")));
    py.FS.writeFile(destination, content);
  }
  py.runPython(
    "import sys, json\nsys.path.insert(0, '/sharpwr')\nfrom engine_bridge import mobile_fight",
  );
  return py;
}
self.onmessage = async (event: MessageEvent) => {
  const { id, base, request } = event.data;
  if (busy) {
    self.postMessage({ id, error: "A fight is already running" });
    return;
  }
  busy = true;
  try {
    self.postMessage({
      id,
      status: runtime ? "Calculating fight…" : "Starting offline engine…",
    });
    const py = await (runtime ??= initialize(base));
    py.globals.set("mobile_request_json", JSON.stringify(request));
    const result = py.runPython(
      "mobile_fight(json.loads(mobile_request_json))",
    );
    self.postMessage({ id, result: JSON.parse(result) });
  } catch (error) {
    runtime = null;
    self.postMessage({ id, error: (error as Error).message });
  } finally {
    busy = false;
  }
};
