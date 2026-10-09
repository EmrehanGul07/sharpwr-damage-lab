/**
 * Practice tab: the web Practice Tool on the phone. Walk around with any champion, cast every skill on
 * a training dummy and keep notes on what differs from Wild Rift (saved on the phone). Three.js, the
 * 3D scripts and the practice data (data/practice.json, from scripts/export_app_data.py) load only
 * when this tab opens; models use the 3D tab's offline cache.
 */
import { arenaOrientation } from "../arena-orientation";
import { h } from "../dom";
import { remoteAsset } from "../online";
import { fetchModel } from "./model3d";
import type { View } from "./shared";
import { loadDatabase } from '../data';
import { arenaBuild } from '../arena-build';

interface PracticeTool {
  dispose(): void;
}

interface Gltf {
  scene: unknown;
  animations: unknown[];
}

interface GltfLoader {
  parseAsync(data: ArrayBuffer, path: string): Promise<Gltf>;
}

interface PracticeToolApi {
  mount(root: HTMLElement, options: Record<string, unknown>): Promise<PracticeTool>;
}

// One arena at a time: opening the tab again (or another champion) releases the previous one.
let current: PracticeTool | null = null;

export function practiceView(champion: string | null): View {
  current?.dispose();
  current = null;
  const root = h("div", { class: "practice" }, h("p", { class: "status" }, "Loading the Practice Tool…"));
  void start(root, champion);
  return { title: "Practice", back: false, body: root };
}

/** Android back button: leaves the full-screen arena first. */
export function leaveFullScreen(): boolean {
  const button = document.querySelector<HTMLButtonElement>(".pt-stage-wrap.pt-full .pt-focus");
  button?.click();
  return !!button;
}

async function start(root: HTMLElement, champion: string | null): Promise<void> {
  try {
    const [catalogue, { loadPracticeScripts }, database] = await Promise.all([loadCatalogue(), import("../practice-scripts"), loadDatabase()]);
    loadPracticeScripts();
    const api = (globalThis as unknown as { MarksmanPracticeTool: PracticeToolApi }).MarksmanPracticeTool;
    const tool = await api.mount(root, {
      catalogue,
      loadout: arenaBuild(database),
      champion: champion ?? undefined,
      compact: true,
      allowDownload: false,
      // The app's window is the screen; the arena covers it instead of asking the WebView for full screen.
      nativeFullscreen: false,
      orientation: arenaOrientation,
      quality: "balanced",
      sceneOptions: { three: loadThree, loadModel, terrainTextureBase: "assets/models/terrain/" },
    });
    if (!root.isConnected) { tool.dispose(); return; }
    current?.dispose();
    current = tool;
  } catch (error) {
    root.replaceChildren(h("p", { class: "status" }, `The Practice Tool could not start: ${(error as Error).message}`));
  }
}

async function loadCatalogue(): Promise<unknown> {
  const response = await fetch("data/practice.json");
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

/** The bundled Three.js for the shared scene (the web page loads it from a CDN). */
export async function loadThree() {
  const [T, { GLTFLoader }, { clone }, { SVGRenderer }] = await Promise.all([
    import("three"),
    import("three/examples/jsm/loaders/GLTFLoader.js"),
    import("three/examples/jsm/utils/SkeletonUtils.js"),
    import("three/examples/jsm/renderers/SVGRenderer.js"),
  ]);
  return {
    T,
    GLTFLoader,
    cloneSkeleton: clone,
    SVGRenderer,
    // Glow for "High quality" only.
    post: () =>
      Promise.all([
        import("three/examples/jsm/postprocessing/EffectComposer.js"),
        import("three/examples/jsm/postprocessing/RenderPass.js"),
        import("three/examples/jsm/postprocessing/UnrealBloomPass.js"),
        import("three/examples/jsm/postprocessing/OutputPass.js"),
      ]),
  };
}

/** Champion models from this repository, kept for offline use (same cache as the 3D tab). */
export async function loadModel(loader: GltfLoader, id: string, file: string): Promise<Gltf> {
  const bundled = await fetch(`assets/models/${id}/${file}`).catch(() => null);
  if (bundled?.ok) return loader.parseAsync(await bundled.arrayBuffer(), '');
  return loader.parseAsync(await fetchModel(remoteAsset(`static/marksman-3d/${id}/${file}`)), "");
}
