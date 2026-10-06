/**
 * 3D tab: the champion's skinned model and its clips from the web Animation Studio
 * (static/marksman-3d in this repository). Models download on demand from GitHub and are kept in
 * Cache Storage for offline use; Three.js loads as a separate chunk, only when this tab opens.
 */
import type { AbilitySlot, Champion } from "../data";
import { h } from "../dom";
import { remoteAsset } from "../online";
import { href } from "../router";

export interface ClipSpec {
  clip: string;
  label: string;
  loop: boolean;
  slot?: AbilitySlot;
}

/** The eight studio clips, in button order. */
export const CLIPS: ReadonlyArray<ClipSpec> = [
  { clip: "Idle", label: "Idle", loop: true },
  { clip: "Walk", label: "Run", loop: true },
  { clip: "AA", label: "Attack", loop: false },
  { clip: "P", label: "P", loop: false, slot: "P" },
  { clip: "Q", label: "Q", loop: false, slot: "Q" },
  { clip: "W", label: "W", loop: false, slot: "W" },
  { clip: "E", label: "E", loop: false, slot: "E" },
  { clip: "R", label: "R", loop: false, slot: "R" },
];

const CACHE = "sharpwr-models";
const TIMEOUT_MS = 30_000;

/** The studio's folder name for a champion: lower case, no apostrophes, spaces become dashes. */
export function modelId(name: string): string {
  return name
    .toLowerCase()
    .replace(/['’.]/g, "")
    .replace(/\s+/g, "-");
}

export function modelUrl(name: string, file = "character.glb"): string {
  return remoteAsset(`static/marksman-3d/${modelId(name)}/${file}`);
}

/** Caption under the stage for a clip, e.g. "Q · Dancing Grenade". */
export function clipCaption(champion: Champion, spec: ClipSpec): string {
  if (!spec.slot) return spec.label;
  const ability = champion.abilities?.find((entry) => entry.slot === spec.slot);
  return ability ? `${spec.slot} · ${ability.name}` : spec.slot;
}

/** Network first, so model updates arrive; the saved copy when offline. */
export async function fetchModel(url: string, store: CacheStorage | null = "caches" in globalThis ? caches : null): Promise<ArrayBuffer> {
  const cache = store ? await store.open(CACHE).catch(() => null) : null;
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(TIMEOUT_MS) });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    if (cache) await cache.put(url, response.clone()).catch(() => undefined);
    return await response.arrayBuffer();
  } catch (error) {
    const saved = cache ? await cache.match(url) : undefined;
    if (saved) return saved.arrayBuffer();
    throw error;
  }
}

// One viewer at a time: opening another champion (or leaving the tab) releases the previous one.
let current: { dispose(): void } | null = null;

export function modelTab(champion: Champion): HTMLElement[] {
  current?.dispose();
  current = null;
  const status = h("p", { class: "model-status" }, "Loading the 3D model…");
  const stage = h("div", { class: "model-stage" }, status);
  const caption = h("p", { class: "model-caption" }, "Idle");
  let play: (spec: ClipSpec) => void = () => undefined;
  const buttons = CLIPS.map((spec) =>
    h("button", { type: "button", class: spec.clip === "Idle" ? "active" : "", disabled: true, onclick: () => play(spec) }, spec.label),
  );
  const select = (spec: ClipSpec) => {
    buttons.forEach((button, index) => button.classList.toggle("active", CLIPS[index] === spec));
    caption.textContent = clipCaption(champion, spec);
  };
  mount(stage, status, champion, select)
    .then((viewer) => {
      current = viewer;
      play = (spec) => {
        select(spec);
        viewer.play(spec);
      };
      buttons.forEach((button) => (button.disabled = false));
    })
    .catch(() => {
      status.textContent = "The 3D model needs an internet connection the first time it opens.";
    });
  return [
    stage,
    caption,
    h("div", { class: "segments model-clips", role: "group", "aria-label": "Animations" }, ...buttons),
    h("p", { class: "note" }, "Drag to turn the model. Original stylized SharpWR model and animations, not Riot game art."),
    h("a", { class: "button", href: href("practice", [], { champion: champion.name }) }, `Practice with ${champion.name}`),
  ];
}

async function mount(stage: HTMLElement, status: HTMLElement, champion: Champion, select: (spec: ClipSpec) => void) {
  const [THREE, { GLTFLoader }] = await Promise.all([import("three"), import("three/examples/jsm/loaders/GLTFLoader.js")]);
  const gltf = await new GLTFLoader().parseAsync(await fetchModel(modelUrl(champion.name)), "");
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(globalThis.devicePixelRatio || 1, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  const canvas = renderer.domElement;
  stage.replaceChildren(canvas);

  const scene = new THREE.Scene();
  scene.add(new THREE.HemisphereLight("#cfe3ff", "#2a3340", 1.6));
  const key = new THREE.DirectionalLight("#fff1dc", 2.4);
  key.position.set(2, 4, 3);
  scene.add(key);
  const rim = new THREE.DirectionalLight("#9fc6ff", 1.2);
  rim.position.set(-3, 2.5, -2.5);
  scene.add(rim);
  const floor = new THREE.Mesh(new THREE.CircleGeometry(1.4, 48), new THREE.MeshBasicMaterial({ color: "#16212f" }));
  floor.rotation.x = -Math.PI / 2;
  scene.add(floor);

  const model = gltf.scene;
  scene.add(model);
  const mixer = new THREE.AnimationMixer(model);
  const actions = new Map(gltf.animations.map((clip) => [clip.name, mixer.clipAction(clip)]));
  let active: ReturnType<typeof mixer.clipAction> | null = null;
  const play = (spec: ClipSpec) => {
    const next = actions.get(spec.clip);
    if (!next) return;
    next.reset();
    next.setLoop(spec.loop ? THREE.LoopRepeat : THREE.LoopOnce, Infinity);
    next.clampWhenFinished = !spec.loop;
    next.fadeIn(0.15).play();
    if (active && active !== next) active.fadeOut(0.15);
    active = next;
  };
  const idle = CLIPS[0];
  mixer.addEventListener("finished", (event) => {
    if (event.action === active) {
      select(idle);
      play(idle);
    }
  });
  play(idle);
  mixer.update(0);

  // Frame the model from its idle pose: three-quarter view, slightly above.
  const box = new THREE.Box3().setFromObject(model);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const height = Math.max(size.y, size.x * 0.8, 0.5);
  const camera = new THREE.PerspectiveCamera(32, 1, 0.05, 50);
  camera.position.set(center.x + height * 0.75, center.y + height * 0.35, center.z + height * 2.1);
  camera.lookAt(center);
  floor.scale.setScalar(Math.max(size.x, size.z, height * 0.6));

  // Drag to turn.
  let dragging: number | null = null;
  canvas.addEventListener("pointerdown", (event) => {
    dragging = event.clientX;
    canvas.setPointerCapture(event.pointerId);
  });
  canvas.addEventListener("pointermove", (event) => {
    if (dragging === null) return;
    model.rotation.y += (event.clientX - dragging) * 0.012;
    dragging = event.clientX;
  });
  const release = () => (dragging = null);
  canvas.addEventListener("pointerup", release);
  canvas.addEventListener("pointercancel", release);

  let frame = 0;
  let last = performance.now();
  let disposed = false;
  const dispose = () => {
    if (disposed) return;
    disposed = true;
    cancelAnimationFrame(frame);
    mixer.stopAllAction();
    model.traverse((object) => {
      const mesh = object as { geometry?: { dispose(): void }; material?: { dispose(): void } | Array<{ dispose(): void }> };
      mesh.geometry?.dispose();
      for (const material of Array.isArray(mesh.material) ? mesh.material : mesh.material ? [mesh.material] : []) material.dispose();
    });
    renderer.dispose();
  };
  const tick = (now: number) => {
    // The tab was left or the page re-rendered: release the GPU resources.
    if (!canvas.isConnected) return dispose();
    const width = stage.clientWidth || 320;
    const heightPx = stage.clientHeight || 340;
    if (canvas.width !== Math.round(width * renderer.getPixelRatio()) || canvas.height !== Math.round(heightPx * renderer.getPixelRatio())) {
      renderer.setSize(width, heightPx, false);
      camera.aspect = width / heightPx;
      camera.updateProjectionMatrix();
    }
    mixer.update(Math.min(0.1, (now - last) / 1000));
    last = now;
    renderer.render(scene, camera);
    frame = requestAnimationFrame(tick);
  };
  frame = requestAnimationFrame(tick);
  status.remove();
  return { play, dispose };
}
