// End-to-end offline fight + WebGL replay. Run after npm run build.
import assert from "node:assert/strict";
import { createServer } from "node:http";
import { readFile, mkdir } from "node:fs/promises";
import { dirname, extname, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";
const mobile = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const root = resolve(mobile, "dist");
const screenshots = process.env.BROWSER_SCREENSHOTS;
if (screenshots) await mkdir(screenshots, { recursive: true });
const server = createServer(async (request, response) => {
  try {
    const pathname = decodeURIComponent(
      new URL(request.url, "http://localhost").pathname,
    );
    let path = resolve(root, `.${pathname}`);
    if (path !== root && !path.startsWith(root + sep)) {
      response.writeHead(403).end();
      return;
    }
    if (pathname.endsWith("/")) path = resolve(path, "index.html");
    const content = await readFile(path);
    response.setHeader(
      "Content-Type",
      {
        ".js": "text/javascript",
        ".mjs": "text/javascript",
        ".wasm": "application/wasm",
        ".json": "application/json",
        ".html": "text/html",
        ".css": "text/css",
        ".png": "image/png",
        ".webp": "image/webp",
      }[extname(path)] ?? "application/octet-stream",
    );
    response.end(content);
  } catch {
    response.writeHead(404).end();
  }
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const base = `http://127.0.0.1:${server.address().port}/`;
let browser;
try {
  browser = await chromium.launch({
    headless: true,
    ...(process.env.CHROMIUM_EXECUTABLE
      ? { executablePath: process.env.CHROMIUM_EXECUTABLE }
      : {}),
    args: [
      "--no-sandbox",
      "--disable-dev-shm-usage",
      "--use-gl=angle",
      "--use-angle=swiftshader",
      "--enable-unsafe-swiftshader",
    ],
  });
  for (const [champion, width, height] of [
    ["Ezreal", 390, 844],
    ["Samira", 390, 844],
    ["Kai'Sa", 1280, 900],
  ]) {
    const page = await browser.newPage({ viewport: { width, height } });
    const errors = [],
      external = [],
      modelLoads = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("response", (response) => {
      if (response.url().includes("/assets/models/") && response.ok())
        modelLoads.push(response.url());
    });
    await page.route("**/*", (route) => {
      if (new URL(route.request().url()).hostname === "127.0.0.1")
        return route.continue();
      external.push(route.request().url());
      return route.abort();
    });
    const params = new URLSearchParams({
      champion,
      level: "15",
      items: "Statikk Shiv|Guinsoo's Rageblade",
      boots: "Immortal Treads",
    });
    await page.goto(`${base}#/build?${params}`);
    const run = page.getByRole("button", {
      name: "Simulate fight + 3D",
      exact: true,
    });
    // Cancellation interrupts initialization and restores the button.
    await run.click();
    await page.getByRole("button", { name: "Cancel", exact: true }).click();
    await page.getByText("Cancelled.", { exact: true }).waitFor();
    assert.equal(await run.isEnabled(), true);
    await run.click();
    await page
      .getByText("Ready. Press Play to watch.", { exact: true })
      .waitFor({ timeout: 180_000 });
    const frame = page.frames().find((frame) => frame !== page.mainFrame());
    assert.ok(frame);
    await frame.locator("#stage3d canvas").waitFor({ timeout: 30_000 });
    await frame.getByRole("button", { name: "▶ Play", exact: true }).click();
    await frame.waitForFunction(
      () =>
        Number(document.querySelector("#clock").textContent.replace("s", "")) >
        1,
    );
    const trace = await frame.evaluate(() => ({
      champion: D.champion,
      source: D.source,
      motion: D.motion.length,
      events: D.events.length,
      status: document.querySelector(".render-status").textContent,
      stack: document.querySelector("#stackSnapshot").textContent,
    }));
    assert.equal(trace.champion, champion);
    assert.equal(trace.source, "build_lab");
    assert.ok(trace.motion > 0 && trace.events > 0);
    assert.equal(trace.status, "PBR • WEBGL");
    await frame.getByRole("button", { name: "❚❚ Pause", exact: true }).click();
    await frame.locator("#reset").click();
    await frame.waitForFunction(
      () =>
        document.querySelector("#stackSnapshot").textContent ===
        "Stacks: no impact yet",
    );
    assert.ok(
      modelLoads.some((url) => url.endsWith("/character.glb")),
      "Bundled GLB must load offline",
    );
    assert.deepEqual(
      external.filter((url) => !url.endsWith("/app-data/database.json")),
      [],
      "No model/runtime/CDN request",
    );
    assert.deepEqual(errors, []);
    if (screenshots)
      await page.screenshot({
        path: resolve(
          screenshots,
          `${champion.replace(/[^a-z]/gi, "").toLowerCase()}.png`,
        ),
        fullPage: true,
      });
    // Navigation removes the replay and cancels a new fight.
    await run.click();
    await page.locator("nav a").first().click();
    assert.equal(page.frames().length, 1);
    assert.deepEqual(errors, []);
    console.log(
      `PASS offline ${champion}: fight, WebGL/GLB, play/reset, cancel/navigation (${width}px)`,
    );
    await page.close();
  }
} finally {
  await browser?.close();
  await new Promise((resolve) => server.close(resolve));
}
