// Copy the Database export and bundled Riot icons into public/ so the app works offline.
// Sources: app-data/database.json and app-data/practice.json (scripts/export_app_data.py) and assets/riot/.
import { cpSync, mkdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import './sync-engine.mjs';

const mobile = join(dirname(fileURLToPath(import.meta.url)), "..");
const repo = join(mobile, "..");
const publicDir = join(mobile, "public");

rmSync(join(publicDir, "data"), { recursive: true, force: true });
rmSync(join(publicDir, "assets"), { recursive: true, force: true });
mkdirSync(join(publicDir, "data"), { recursive: true });
cpSync(join(repo, "app-data", "database.json"), join(publicDir, "data", "database.json"));
cpSync(join(repo, "app-data", "practice.json"), join(publicDir, "data", "practice.json"));
cpSync(join(repo, "assets", "riot"), join(publicDir, "assets", "riot"), {
  recursive: true,
  filter: (source) => !source.endsWith(".md"),
});
cpSync(join(repo, 'static', 'marksman-3d'), join(publicDir, 'assets', 'models'), {
  recursive: true,
});
cpSync(join(repo, 'assets', 'combat_replay.html'), join(publicDir, 'assets', 'replay-template.html'));
console.log("Synced app-data/database.json, app-data/practice.json and assets/riot into mobile/public");
