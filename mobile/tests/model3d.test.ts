import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { Champion } from "../src/data";
import { CLIPS, clipCaption, fetchModel, modelId, modelUrl } from "../src/views/model3d";

const root = fileURLToPath(new URL("../..", import.meta.url));
const art = JSON.parse(readFileSync(join(root, "data/marksman-art-direction.json"), "utf8")) as { champions: Record<string, { id: string }> };
const db = JSON.parse(readFileSync(join(root, "app-data/database.json"), "utf8")) as { champions: Champion[] };

/** In-memory Cache Storage with the two calls fetchModel uses. */
function memoryCaches() {
  const entries = new Map<string, Response>();
  const cache = {
    put: async (url: string, response: Response) => void entries.set(url, response),
    match: async (url: string) => entries.get(url)?.clone(),
  };
  return { entries, store: { open: async () => cache } as unknown as CacheStorage };
}

afterEach(() => vi.unstubAllGlobals());

describe("3D tab", () => {
  it("finds the studio model of every database champion", () => {
    for (const champion of db.champions) {
      expect(modelId(champion.name), champion.name).toBe(art.champions[champion.name].id);
      expect(existsSync(join(root, "static/marksman-3d", modelId(champion.name), "character.glb")), champion.name).toBe(true);
    }
    expect(modelUrl("Kai'Sa")).toBe("https://raw.githubusercontent.com/EmrehanGul07/sharpwr-damage-lab/main/static/marksman-3d/kaisa/character.glb");
  });

  it("offers the eight studio clips, looping only idle and run", () => {
    expect(CLIPS.map((spec) => spec.clip)).toEqual(["Idle", "Walk", "AA", "P", "Q", "W", "E", "R"]);
    expect(CLIPS.filter((spec) => spec.loop).map((spec) => spec.clip)).toEqual(["Idle", "Walk"]);
  });

  it("names a clip after the champion's ability", () => {
    const jinx = db.champions.find((champion) => champion.name === "Jinx")!;
    expect(clipCaption(jinx, CLIPS[4])).toBe(`Q · ${jinx.abilities!.find((ability) => ability.slot === "Q")!.name}`);
    expect(clipCaption(jinx, CLIPS[1])).toBe("Run");
  });

  it("downloads a model, keeps a copy and uses it offline", async () => {
    const { entries, store } = memoryCaches();
    vi.stubGlobal("fetch", vi.fn(async () => new Response(new Uint8Array([1, 2, 3]))));
    expect(new Uint8Array(await fetchModel("https://example.test/a.glb", store))).toEqual(new Uint8Array([1, 2, 3]));
    expect(entries.has("https://example.test/a.glb")).toBe(true);

    vi.stubGlobal("fetch", vi.fn(async () => Promise.reject(new TypeError("offline"))));
    expect(new Uint8Array(await fetchModel("https://example.test/a.glb", store))).toEqual(new Uint8Array([1, 2, 3]));
    await expect(fetchModel("https://example.test/missing.glb", store)).rejects.toThrow("offline");
  });

  it("does not keep a failed download", async () => {
    const { entries, store } = memoryCaches();
    vi.stubGlobal("fetch", vi.fn(async () => new Response("not found", { status: 404 })));
    await expect(fetchModel("https://example.test/b.glb", store)).rejects.toThrow("HTTP 404");
    expect(entries.size).toBe(0);
  });
});
