import type { Database } from "../data";
import { h } from "../dom";
import type { BuildInput } from "../engine/build";
import { simulateAa } from "../engine/aa";
import {
  runFight,
  disposeFightEngine,
  type FightSettings,
} from "../engine/fight";
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
      required: true,
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
  const choice = (label: string, options: Array<[string, string]>) => {
    const select = h(
      "select",
      { class: "select", "aria-label": label },
      ...options.map(([value, text]) => h("option", { value }, text)),
    );
    return { select, row: h("label", { class: "level-row" }, label, select) };
  };
  const rotation = choice("Skill priority", [
    ["auto", "Champion default"],
    ...["QWE", "QEW", "WQE", "WEQ", "EQW", "EWQ"].map(
      (x) => [x, x.split("").join(" → ")] as [string, string],
    ),
  ]);
  const movement = choice("Movement", [
    ["auto", "Champion default"],
    ["skill_envelope", "Keep skill range"],
    ["aa_envelope", "Keep AA range"],
    ["close_envelope", "Close distance"],
  ]);
  const ultimate = choice("Ultimate timing", [
    ["immediate", "As soon as available"],
    ["after_basics", "After basic skills"],
  ]);
  const distance = h("input", {
    type: "number",
    min: 0,
    max: 2500,
    step: 1,
    placeholder: "Champion AA range",
    class: "select",
    "aria-label": "Starting distance",
  });
  const quality = choice("Replay quality", [
    ["low", "Smooth · lighter models"],
    ["balanced", "Detailed · full models"],
  ]);
  quality.select.value = "balanced";
  const controls = [
    ...inputs,
    rotation.select,
    movement.select,
    ultimate.select,
    distance,
    quality.select,
  ];
  try {
    const saved = JSON.parse(
      localStorage.getItem("sharpwr.fight-controls") || "{}",
    );
    for (const control of controls) {
      const value = saved?.[control.getAttribute("aria-label")!];
      if (typeof value !== "string") continue;
      if (control instanceof HTMLSelectElement) {
        if ([...control.options].some((option) => option.value === value))
          control.value = value;
      } else {
        const previous = control.value;
        control.value = value;
        if (!control.validity.valid || (value === "" && control.required))
          control.value = previous;
      }
    }
  } catch {
    /* Storage unavailable: defaults still work. */
  }
  const saveControls = () => {
    try {
      localStorage.setItem(
        "sharpwr.fight-controls",
        JSON.stringify(
          Object.fromEntries(
            controls.map((control) => [
              control.getAttribute("aria-label"),
              control.value,
            ]),
          ),
        ),
      );
    } catch {
      /* Optional persistence. */
    }
  };
  for (const control of controls)
    control.addEventListener("change", saveControls);
  const cancel = h(
    "button",
    {
      type: "button",
      class: "button",
      hidden: true,
      onclick: () => {
        controller?.abort();
        disposeFightEngine();
      },
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
    rotation.row,
    movement.row,
    ultimate.row,
    h("label", { class: "level-row" }, "Starting distance", distance),
    quality.row,
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
    if (
      inputs.some((input) => !input.reportValidity()) ||
      !distance.reportValidity()
    )
      return;
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
    status.textContent = "Calculating fight…";
    try {
      const aa = simulateAa(db, build, target);
      const fight = await runFight(
        {
          build,
          target,
          settings: {
            rotation: rotation.select.value,
            movement: movement.select.value,
            ultimate: ultimate.select.value,
            ...(distance.value !== ""
              ? { distance: Number(distance.value) }
              : {}),
          } as FightSettings,
        },
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
      await mountReplay(
        replay,
        fight.replay,
        quality.select.value as "low" | "balanced",
        operation.signal,
      );
      if (operation.signal.aborted || !root.isConnected) {
        replay.replaceChildren();
        return;
      }
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
      disposeFightEngine();
      replay.replaceChildren();
    },
  };
}
