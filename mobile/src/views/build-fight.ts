import type { Database } from "../data";
import { h } from "../dom";
import type { BuildInput } from "../engine/build";
import { simulateAa } from "../engine/aa";
import { runFight } from "../engine/fight";
import { statTable } from "./shared";

export function buildFightPanel(
  db: Database,
  build: BuildInput,
  legal: boolean,
) {
  let controller: AbortController | null = null;
  const fields = [
    ["Health", 3000, 1, 100000, 1],
    ["Armor", 100, -100, 1000, 1],
    ["Magic resist", 80, -100, 1000, 1],
    ["Bonus health", 0, 0, 100000, 1],
    ["AA reduction (%)", 0, 0, 100, 1],
  ] as const;
  const inputs = fields.map(([label, value, min, max, step]) =>
    h("input", {
      type: "number",
      value,
      min,
      max,
      step,
      class: "select",
      "aria-label": `Target ${label}`,
    }),
  );
  const status = h("p", {
    class: "status",
    role: "status",
    "aria-live": "polite",
  });
  const result = h("div");
  const replay = h("div");
  const cancel = h(
    "button",
    {
      type: "button",
      class: "button",
      hidden: true,
      onclick: () => controller?.abort(),
    },
    "Cancel",
  );
  const run = h(
    "button",
    { type: "button", class: "button", disabled: !legal },
    "Simulate fight + 3D",
  );
  const root = h(
    "section",
    {},
    h("h3", {}, "Fight Lab"),
    ...fields.map(([label], index) =>
      h("label", { class: "level-row" }, label, inputs[index]),
    ),
    h(
      "p",
      { class: "muted small" },
      "Stationary target · energized ready · SharpWR combat assumptions. Includes skills, mana, cooldowns, movement and your selected rune page.",
    ),
    run,
    cancel,
    status,
    result,
    replay,
  );
  run.onclick = () => {
    void simulate();
  };
  async function simulate() {
    if (inputs.some((input) => !input.reportValidity())) return;
    const [health, armor, magicResist, bonusHealth, reduction] = inputs.map(
      (input) => Number(input.value),
    );
    if (bonusHealth > health) {
      status.textContent = "Bonus health cannot exceed total health.";
      return;
    }
    const target = {
      health,
      armor,
      magicResist,
      bonusHealth,
      attackReduction: reduction / 100,
    };
    controller?.abort();
    const operation = new AbortController();
    controller = operation;
    run.disabled = true;
    cancel.hidden = false;
    result.replaceChildren();
    replay.replaceChildren();
    try {
      const aa = simulateAa(db, build, target);
      const fight = await runFight(
        { build, target },
        (message) => {
          status.textContent = message;
        },
        operation.signal,
      );
      if (operation.signal.aborted || !root.isConnected) return;
      result.replaceChildren(
        statTable([
          [
            "Fight TTK",
            fight.summary.TTK === null
              ? "Survived 60s"
              : `${fight.summary.TTK.toFixed(3)}s`,
          ],
          ["Fight damage", fight.summary.Damage.toFixed(1)],
          ["Fight DPS", fight.summary.DPS.toFixed(1)],
          ["Rotation", fight.summary.Rotation],
          ["Movement", fight.summary.Movement],
          [
            "AA-only cycle TTK",
            aa.ttk === null ? "Survived 500 attacks" : `${aa.ttk.toFixed(3)}s`,
          ],
          ["AA-only DPS", aa.dps.toFixed(1)],
          ["AA-only attacks", String(aa.attacks)],
        ]),
        h(
          "p",
          { class: "muted small" },
          "AA-only excludes champion abilities/passives and runes; cycle TTK includes the final attack interval. Fight TTK is the recorded defeat time.",
        ),
      );
      status.textContent = "Fight calculated. Loading replay…";
      const { mountReplay } = await import("../replay");
      if (operation.signal.aborted || !root.isConnected) return;
      await mountReplay(replay, fight.replay);
      status.textContent = "Ready. Press Play to watch.";
    } catch (error) {
      if (!operation.signal.aborted && root.isConnected)
        status.textContent = `Could not simulate: ${(error as Error).message}`;
      else if (root.isConnected) status.textContent = "Cancelled.";
    } finally {
      if (controller === operation) {
        controller = null;
        run.disabled = !legal;
        cancel.hidden = true;
      }
    }
  }
  return {
    root,
    dispose: () => {
      controller?.abort();
      replay.replaceChildren();
    },
  };
}
