import { readFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import { describe, expect, it } from "vitest";
import { loadPyodide } from "pyodide";
const root = new URL("../", import.meta.url);
const cases = JSON.parse(
  gunzipSync(
    readFileSync(
      new URL("../../app-data/golden/fights.json.gz", import.meta.url),
    ),
  ).toString(),
);
describe("offline mobile fight engine", () => {
  it("matches CPython traces for all 23 champions at levels 1, 9 and 15, with runes and survival", async () => {
    const py = await loadPyodide({
      indexURL: new URL("node_modules/pyodide/", root).pathname,
    });
    const sources = JSON.parse(
      readFileSync(new URL("public/engine/sources.json", root), "utf8"),
    );
    for (const [path, content] of Object.entries(sources)) {
      const destination = `/sharpwr/${path}`;
      py.FS.mkdirTree(destination.slice(0, destination.lastIndexOf("/")));
      py.FS.writeFile(destination, String(content));
    }
    py.runPython(
      "import sys, json\nsys.path.insert(0, '/sharpwr')\nfrom engine_bridge import mobile_fight",
    );
    for (const fixture of cases) {
      py.globals.set("request_json", JSON.stringify(fixture.request));
      const actual = JSON.parse(
        py.runPython("mobile_fight(json.loads(request_json))"),
      );
      const context = `${fixture.request.build.champion} L${fixture.request.build.level}`;
      expect(actual.summary.TTK, context).toEqual(fixture.summary.TTK);
      expect(actual.summary.Damage, context).toBeCloseTo(
        fixture.summary.Damage,
        6,
      );
      expect(actual.summary.DPS, context).toBeCloseTo(fixture.summary.DPS, 6);
      expect(actual.summary.Rotation, context).toEqual(
        fixture.summary.Rotation,
      );
      expect(actual.replay.events.length, context).toBe(fixture.events.length);
      expect(actual.replay.motion.length, context).toBe(fixture.motionCount);
      expect(actual.replay.motion.length, context).toBeGreaterThan(0);
      fixture.events.forEach(
        (event: Record<string, unknown>, index: number) => {
          const got = actual.replay.events[index];
          for (const [key, value] of Object.entries(event)) {
            if (typeof value === "number")
              expect(got[key], `${context} #${index} ${key}`).toBeCloseTo(
                value,
                6,
              );
            else expect(got[key], `${context} #${index} ${key}`).toEqual(value);
          }
        },
      );
    }
  }, 180_000);
});
