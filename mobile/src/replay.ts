/** Same recorded-trace renderer as the web Build Lab, with bundled Three.js and models. */
import state from "../../assets/replay_state.js?raw";
import baked from "../../assets/marksman-3d/baked-avatar.js?raw";
import geometry from "../../assets/marksman-3d/geometry.js?raw";
import rig from "../../assets/marksman-3d/rig.js?raw";
import effects from "../../assets/marksman-3d/effects.js?raw";
import arena from "../../assets/marksman-3d/rift-arena.js?raw";
import scene from "../../assets/marksman-3d/scene.js?raw";
import adapter from "../../assets/marksman-3d/replay.js?raw";
import { loadModel, loadThree } from "./views/practice";
const safeJson = (value: unknown) =>
  JSON.stringify(value)
    .replace(/</g, "\\u003c")
    .replace(/>/g, "\\u003e")
    .replace(/&/g, "\\u0026");
type Host = Window & { SharpWRReplayScene?: Record<string, unknown> };
export function replayDocument(
  template: string,
  payload: Record<string, unknown>,
  profiles: unknown,
): string {
  const scripts =
    `window.MarksmanArtProfiles=${safeJson(profiles)};window.MarksmanReplaySceneOptions=parent.SharpWRReplayScene;\n` +
    [baked, geometry, rig, effects, arena, scene, adapter].join("\n");
  // Load the pure readers before the player schedules its first animation frame.
  return template
    .replace(/<script type="importmap">[\s\S]*?<\/script>/g, "")
    .replace("<script>__REPLAY_STATE_SCRIPT__</script>", "")
    .replace("</head>", () => `<script>${state}</script></head>`)
    .replace("__REPLAY_DATA__", () => safeJson(payload))
    .replace("__EZREAL_3D_SCRIPT__", () => scripts);
}
export async function mountReplay(
  root: HTMLElement,
  payload: Record<string, unknown>,
): Promise<void> {
  const [response, html] = await Promise.all([
    fetch("data/practice.json"),
    fetch("assets/replay-template.html"),
  ]);
  if (!response.ok) throw Error(`Replay data HTTP ${response.status}`);
  if (!html.ok) throw Error(`Replay template HTTP ${html.status}`);
  const catalogue = await response.json();
  (window as Host).SharpWRReplayScene = {
    three: loadThree,
    loadModel,
    quality: "balanced",
  };
  if (!root.isConnected) return;
  const frame = document.createElement("iframe");
  frame.title = "Recorded build fight";
  frame.style.cssText = "width:100%;height:1020px;border:0;border-radius:12px";
  frame.srcdoc = replayDocument(
    await html.text(),
    payload,
    catalogue.champions,
  );
  root.replaceChildren(frame);
}
