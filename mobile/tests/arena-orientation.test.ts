import { beforeEach, describe, expect, it, vi } from "vitest";
const native = vi.hoisted(() => ({ value: true }));
const calls = vi.hoisted(() => ({ lock: vi.fn(), unlock: vi.fn() }));
vi.mock("@capacitor/core", () => ({ Capacitor: { isNativePlatform: () => native.value } }));
vi.mock("@capacitor/screen-orientation", () => ({ ScreenOrientation: calls }));
import { arenaOrientation } from "../src/arena-orientation";
describe("arena orientation", () => {
  beforeEach(() => { vi.clearAllMocks(); native.value = true; });
  it("locks the native session to landscape and releases it on exit", async () => {
    await arenaOrientation.enter(); expect(calls.lock).toHaveBeenCalledWith({ orientation: "landscape" });
    await arenaOrientation.leave(); expect(calls.unlock).toHaveBeenCalledOnce();
  });
  it("lets the arena handle a platform rejection with its landscape surface", async () => {
    calls.lock.mockRejectedValueOnce(new Error("orientation unavailable"));
    await expect(arenaOrientation.enter()).rejects.toThrow("orientation unavailable");
    await arenaOrientation.leave(); expect(calls.unlock).toHaveBeenCalledOnce();
  });
});
