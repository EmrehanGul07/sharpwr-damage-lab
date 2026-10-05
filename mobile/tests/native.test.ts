import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { isNewerVersion } from "../src/online";

// Live updates replace the web screens only. Whatever the installed APK fixes is fingerprinted
// here; when it changes, older APKs must not take the new screens (src/live-update.ts).
const mobile = fileURLToPath(new URL("..", import.meta.url));
const read = (file: string) => readFileSync(join(mobile, file), "utf8");
const native = JSON.parse(read("native.json")) as { minApkVersion: string; fingerprint: string };
const pkg = JSON.parse(read("package.json")) as { version: string; dependencies: Record<string, string> };

/** Android project, Capacitor config and the installed version of every runtime (native) dependency. */
function nativeFingerprint(): string {
  const hash = createHash("sha256");
  const listed = execFileSync("git", ["ls-files", "--cached", "--others", "--exclude-standard", "android", "capacitor.config.json"], {
    cwd: mobile,
    encoding: "utf8",
  });
  for (const file of [...new Set(listed.split("\n").filter(Boolean))].sort()) {
    hash.update(`${file}\0`);
    hash.update(readFileSync(join(mobile, file)));
  }
  const lock = JSON.parse(read("package-lock.json")) as { packages: Record<string, { version: string }> };
  for (const name of Object.keys(pkg.dependencies).sort()) hash.update(`${name}@${lock.packages[`node_modules/${name}`].version}\0`);
  return hash.digest("hex");
}

describe("native shell", () => {
  it("matches the fingerprint recorded with minApkVersion", () => {
    const fingerprint = nativeFingerprint();
    expect(
      fingerprint,
      `The Android shell changed. If that is intended, set "minApkVersion" to "${pkg.version}" and "fingerprint" to "${fingerprint}" in mobile/native.json.`,
    ).toBe(native.fingerprint);
  });

  it("never requires an APK newer than this version", () => {
    expect(isNewerVersion(native.minApkVersion, pkg.version)).toBe(false);
  });
});
