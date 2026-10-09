/**
 * The web Practice Tool's scripts (assets/marksman-3d), shared with the web page. They are classic
 * scripts that define globals (MarksmanScene, MarksmanPractice, …), so they run as scripts here, in
 * this order, instead of being bundled as modules.
 */
import baked from "../../assets/marksman-3d/baked-avatar.js?raw";
import effects from "../../assets/marksman-3d/effects.js?raw";
import fight from "../../assets/marksman-3d/fight.js?raw";
import geometry from "../../assets/marksman-3d/geometry.js?raw";
import practice from "../../assets/marksman-3d/practice.js?raw";
import mechanics from "../../assets/marksman-3d/duel-mechanics.js?raw";
import bot from "../../assets/marksman-3d/duel-bot.js?raw";
import duel from "../../assets/marksman-3d/duel.js?raw";
import tool from "../../assets/marksman-3d/practice-tool.js?raw";
import css from "../../assets/marksman-3d/practice-tool.css?inline";
import arena from "../../assets/marksman-3d/rift-arena.js?raw";
import rig from "../../assets/marksman-3d/rig.js?raw";
import scene from "../../assets/marksman-3d/scene.js?raw";

/** Load order: geometry before practice, which reads it when it runs. */
export const SCRIPTS: ReadonlyArray<[string, string]> = [
  ["baked-avatar.js", baked],
  ["rig.js", rig],
  ["effects.js", effects],
  ["rift-arena.js", arena],
  ["scene.js", scene],
  ["fight.js", fight],
  ["geometry.js", geometry],
  ["practice.js", practice],
  ["duel-bot.js", bot],
  ["duel-mechanics.js", mechanics],
  ["duel.js", duel],
  ["practice-tool.js", tool],
];

let loaded = false;

/** Runs the scripts once and adds the tool's styles to the page. */
export function loadPracticeScripts(): void {
  if (loaded) return;
  for (const [name, code] of SCRIPTS) new Function(`${code}\n//# sourceURL=${name}`)();
  if (typeof document !== "undefined") document.head.append(Object.assign(document.createElement("style"), { textContent: css }));
  loaded = true;
}
