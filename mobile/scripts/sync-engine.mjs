// Bundle the pinned WASM runtime and exact repository engine for offline worker use.
import {
  cpSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const mobile = join(dirname(fileURLToPath(import.meta.url)), "..");
const repo = join(mobile, "..");
const output = join(mobile, "public", "engine");
rmSync(output, { recursive: true, force: true });
mkdirSync(output, { recursive: true });
for (const file of [
  "pyodide.mjs",
  "pyodide.asm.js",
  "pyodide.asm.wasm",
  "python_stdlib.zip",
  "pyodide-lock.json",
])
  cpSync(join(mobile, "node_modules", "pyodide", file), join(output, file));
const files = {};
for (const name of readdirSync(join(repo, "sharpwr")).filter((name) =>
  name.endsWith(".py"),
))
  files[`sharpwr/${name}`] = readFileSync(join(repo, "sharpwr", name), "utf8");
for (const name of [
  "marksman-ability-catalogue.json",
  "marksman_champion_stats.json",
  "damage-classification.json",
  "pc-combat-timing.json",
  "default-rune-pages.json",
  "build-styles.json",
  "editor-core-items.json",
])
  files[`data/${name}`] = readFileSync(join(repo, "data", name), "utf8");
files["combat_replay.py"] = readFileSync(
  join(repo, "combat_replay.py"),
  "utf8",
);
files["engine_bridge.py"] = readFileSync(
  join(mobile, "engine_bridge.py"),
  "utf8",
);
writeFileSync(join(output, "sources.json"), JSON.stringify(files));
console.log(
  `Bundled offline fight engine (${Object.keys(files).length} sources)`,
);
