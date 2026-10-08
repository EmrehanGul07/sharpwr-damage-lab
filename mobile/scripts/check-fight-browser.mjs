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
    let wasmLoads = 0;
    const errors = [],
      external = [],
      modelLoads = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("response", (response) => {
      if (response.url().endsWith("/pyodide.asm.wasm")) wasmLoads++;
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
    if (champion === "Ezreal") {
      await page
        .getByLabel("Skill priority", { exact: true })
        .selectOption("EWQ");
      await page
        .getByLabel("Movement", { exact: true })
        .selectOption("aa_envelope");
      await page
        .getByLabel("Ultimate timing", { exact: true })
        .selectOption("after_basics");
      await page.getByLabel("Starting distance", { exact: true }).fill("850");
      await page
        .getByLabel("Replay quality", { exact: true })
        .selectOption("low");
    }
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
      policy: D.policy,
      initialDistance: D.motion[0].distance,
    }));
    assert.equal(trace.champion, champion);
    assert.equal(trace.source, "build_lab");
    assert.ok(trace.motion > 0 && trace.events > 0);
    assert.equal(trace.status, "PBR • WEBGL");
    if (champion === "Ezreal") {
      assert.equal(trace.policy.Rotation, "E → W → Q");
      assert.equal(trace.policy.Movement, "aa_envelope");
      assert.equal(trace.policy["Ultimate timing"], "after_basics");
      assert.equal(trace.initialDistance, 850);
    }
    await frame.waitForFunction(
      () =>
        [...document.querySelectorAll(".skill-hud img")].length === 4 &&
        [...document.querySelectorAll(".skill-hud img")].every(
          (i) => i.naturalWidth > 0,
        ),
    );
    await frame.getByRole("button", { name: "❚❚ Pause", exact: true }).click();
    await frame.locator("#reset").click();
    await frame.waitForFunction(
      () =>
        document.querySelector("#stackSnapshot").textContent ===
        "Stacks: no impact yet",
    );
    assert.ok(
      modelLoads.some((url) =>
        url.endsWith(champion === "Ezreal" ? "/preview.glb" : "/character.glb"),
      ),
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
    // A second completed calculation reuses the initialized WASM worker.
    const loadedBefore = wasmLoads;
    await run.click();
    await page
      .getByText("Ready. Press Play to watch.", { exact: true })
      .waitFor({ timeout: 180000 });
    assert.equal(wasmLoads, loadedBefore, "Warm fight must not reload WASM");
    // Navigation removes the replay and cancels a new fight.
    await run.click();
    await page.locator("nav a").first().click();
    await page.waitForFunction(()=>location.hash.startsWith('#/champions') && document.querySelectorAll('iframe').length===0);
    assert.equal(page.frames().length, 1);
    assert.deepEqual(errors, []);
    console.log(
      `PASS offline ${champion}: fight, WebGL/GLB, play/reset, cancel/navigation (${width}px)`,
    );
    await page.close();
  }
  for (const width of [390, 1280]) {
    const page = await browser.newPage({ viewport: { width, height: 900 } });
    const errors = [], external = [], models = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('response', r => { if (r.ok() && r.url().includes('/assets/models/')) models.push(r.url()); });
    await page.route('**/*', route => {
      if (new URL(route.request().url()).hostname === '127.0.0.1') return route.continue();
      external.push(route.request().url()); return route.abort();
    });
    await page.goto(`${base}#/practice?champion=Ezreal`);
    await page.getByLabel('Arena mode', { exact: true }).waitFor();
    await page.locator('.pt-stage canvas').waitFor({ timeout: 30000 });
    await page.getByLabel('Arena mode', { exact: true }).selectOption('duel');
    await page.getByLabel('Bot champion', { exact: true }).selectOption('Jinx');
    assert.ok(await page.getByLabel('No cooldowns', { exact: true }).isDisabled());
    assert.ok(await page.getByLabel('Q rank', { exact: true }).isDisabled());
    let initialStats;
    for (const difficulty of ['easy', 'medium', 'hard', 'impossible']) {
      await page.getByLabel('Bot difficulty', { exact: true }).selectOption(difficulty);
      await page.getByRole('button', { name: 'Start 1v1', exact: true }).click();
      await page.waitForFunction(() => document.querySelector('.pt-combo').textContent.startsWith('FIGHT'));
      const stats = await page.locator('.pt-stats').textContent();
      if (!initialStats) initialStats = stats;
      assert.equal(stats, initialStats, 'Difficulty must not change player stats');
      await page.getByRole('button', { name: 'Pause', exact: true }).click();
      await page.waitForFunction(() => document.querySelector('.pt-combo').textContent.startsWith('PAUSED'));
      const paused = await page.locator('.pt-combo').textContent();
      await page.waitForTimeout(200);
      assert.equal(await page.locator('.pt-combo').textContent(), paused, 'Pause freezes both actors');
      await page.getByRole('button', { name: 'Resume', exact: true }).click();
      await page.locator('.pt-skill[data-slot="AA"]').dispatchEvent('pointerdown', { pointerId: 1 });
      await page.waitForFunction(() => document.querySelector('.pt-log').textContent.includes('AA'), null, { timeout: 10000 });
      await page.locator('.pt-skill[data-slot="AA"]').dispatchEvent('pointerup', { pointerId: 1 });
    }
    assert.ok(models.some(x => x.includes('/ezreal/')) && models.some(x => x.includes('/jinx/')), 'Both champion models load offline');
    if (screenshots) await page.screenshot({ path: resolve(screenshots, `duel-${width}.png`), fullPage: true });
    await page.getByLabel('Arena mode', { exact: true }).selectOption('practice');
    assert.ok(await page.getByLabel('Q rank', { exact: true }).isEnabled());
    assert.deepEqual(errors, []);
    assert.deepEqual(external.filter(x => !x.endsWith('/app-data/database.json')), []);
    await page.locator('nav a').first().click();
    await page.waitForFunction(() => document.querySelectorAll('.pt-stage canvas').length === 0);
    await page.close();
    console.log(`PASS offline 1v1: four modes, equal stats, controls, pause, two GLBs, navigation (${width}px)`);
  }
} finally {
  await browser?.close();
  await new Promise((resolve) => server.close(resolve));
}
