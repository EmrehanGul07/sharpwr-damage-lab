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
  for (const [champion, width, height] of process.env.PRACTICE_ONLY ? [] : [
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
  for (const [width,height] of [[390,844],[844,390],[1280,800]].filter(([w])=>!process.env.PRACTICE_VIEWPORT||w===Number(process.env.PRACTICE_VIEWPORT))) {
    const page = await browser.newPage({ viewport: { width, height } });
    const errors = [], external = [], models = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('response', r => { if (r.ok() && r.url().includes('/assets/models/')) models.push(r.url()); });
    await page.route('**/*', route => {
      if (new URL(route.request().url()).hostname === '127.0.0.1') return route.continue();
      external.push(route.request().url()); return route.abort();
    });
    await page.addInitScript(()=>{let api;Object.defineProperty(window,'MarksmanPractice',{configurable:true,get:()=>api,set:value=>{api=value;const frame=value.frame;value.frame=(state,...args)=>{window.__practiceState=state;return frame(state,...args);};}});let sceneAPI;Object.defineProperty(window,'MarksmanScene',{configurable:true,get:()=>sceneAPI,set:value=>{sceneAPI=value;const create=value.createScene;value.createScene=async(...args)=>{const scene=await create(...args),render=scene.render;scene.render=(...frames)=>{const m=render(...frames);window.__practiceMetrics=m;return m;};return scene;};}});});
    await page.goto(`${base}#/practice?champion=Ezreal`);
    await page.getByLabel('Arena mode', { exact: true }).waitFor();
    await page.locator('.pt-stage canvas').waitFor({ timeout: 30000 });
    assert.equal(await page.locator('.pt-stage-wrap').getAttribute('data-phase'), 'preview');
    assert.equal(await page.getByRole('button', {name:'Pause',exact:true}).count(),0);
    assert.equal(await page.getByRole('button', {name:'Resume',exact:true}).count(),0);
    assert.ok(await page.getByLabel('Combat sound',{exact:true}).isChecked());
    await page.getByLabel('Combat sound',{exact:true}).uncheck();
    await page.getByLabel('Combat sound',{exact:true}).check();
    await page.getByLabel('Arena mode', { exact: true }).selectOption('duel');
    await page.getByLabel('Bot champion', { exact: true }).selectOption('Jinx');
    assert.ok(await page.getByLabel('No cooldowns', { exact: true }).isDisabled());
    assert.ok(await page.getByLabel('Q rank', { exact: true }).isDisabled());
    let initialStats;
    for (const difficulty of ['easy', 'medium', 'hard', 'impossible']) {
      await page.getByLabel('Bot difficulty', { exact: true }).selectOption(difficulty);
      await page.getByRole('button', { name: 'Start Practice', exact: true }).click();
      await page.waitForFunction(() => document.querySelector('.pt-stage-wrap').dataset.phase==='ready' && !document.querySelector('.pt-skill[data-slot="AA"]').disabled);
      assert.ok((await page.locator('.pt-buffs').textContent()).includes('MANA'));
      const size = await page.locator('.pt-stage').evaluate(e=>[e.clientWidth,e.clientHeight]);
      assert.ok(size[0]>size[1], 'Combat always has a landscape viewport');
      const stats = await page.locator('.pt-stats').textContent();
      if (!initialStats) initialStats = stats;
      assert.equal(stats, initialStats, 'Difficulty must not change player stats');
      const idle = await page.locator('.pt-combo').textContent();
      await page.waitForTimeout(250);
      assert.equal(await page.locator('.pt-combo').textContent(), idle, 'Both actors wait for first gameplay input');
      if (screenshots && difficulty==='easy') await page.screenshot({ path: resolve(screenshots, `dragon-lane-ready-${width}.png`) });
      await page.locator('.pt-skill[data-slot="AA"]').dispatchEvent('pointerdown', { pointerId: 1 });
      await page.waitForFunction(() => document.querySelector('.pt-combo').textContent.startsWith('FIGHT'));
      await page.waitForFunction(() => document.querySelector('.pt-log').textContent.includes('AA'), null, { timeout: 10000 });
      await page.locator('.pt-skill[data-slot="AA"]').dispatchEvent('pointerup', { pointerId: 1 });
      if (difficulty==='easy') {
        await page.evaluate(()=>{const d=window.__practiceState.duel;d.bot.next=Infinity;for(const s of [d.player,d.enemy]){s.pending=null;s.attackHeld=false;s.destination=s.hero.slice();}d.player.deadlines.W=0;window.MarksmanPractice.cast(d.player,'W',d.enemy.hero);});
        await page.waitForFunction(()=>document.querySelector('.pt-target-hud')?.textContent.includes('W MARK')||Array.from(document.querySelectorAll('.pt-stage div')).some(e=>e.textContent.includes('W MARK')));
        const markedTime=await page.evaluate(()=>window.__practiceState.duel.time);
        await page.waitForFunction(t=>window.__practiceState.duel.time>t+.3,markedTime,{timeout:10000});
        assert.deepEqual(errors,[],'Ezreal W mark HUD must render without errors');
      }
      const laneMetrics=await page.evaluate(()=>window.__practiceMetrics);
      assert(laneMetrics.laneActors>=0&&laneMetrics.laneActors<=64,'bounded articulated lane actor pool');
      if(difficulty==='easy')assert(laneMetrics.laneActors>0,'first-wave articulated models render');
      assert(laneMetrics.laneModelGeometries<=5&&laneMetrics.laneModelMaterials<=10,'shared model resources');
      assert(laneMetrics.drawCalls<1500&&laneMetrics.geometryCount<800,'lane renderer stays within regression budget');
      if (screenshots && difficulty==='easy') await page.screenshot({ path: resolve(screenshots, `dragon-lane-fight-${width}.png`) });
      if(difficulty==='easy'){
        await page.waitForFunction(()=>window.__practiceState.duel.lane.units.length>0);
        const lockHero=await page.evaluate(()=>{const d=window.__practiceState.duel,m=d.lane.units.find(m=>m.side===1),r=window.MarksmanPractice.stats(d.player).range/100/3;d.lane.units=[m];d.lane.shots=[];m.position=[d.player.hero[0]+Math.cos(-.78)*r,0,d.player.hero[2]-Math.sin(-.78)*r];m.health.max=m.health.hp=5000;m.health.defeatedAt=null;m.rewarded=false;m.range=4;m.next=Infinity;return d.player.hero.slice();});
        const aa=page.locator('.pt-skill[data-slot="AA"]'),rotated=await page.locator('.pt-stage-wrap').evaluate(e=>e.dataset.rotated==='true');
        await aa.dispatchEvent('pointerdown',{pointerId:32,clientX:100,clientY:100});
        await aa.dispatchEvent('pointermove',{pointerId:99,clientX:rotated?100:130,clientY:rotated?130:100});
        assert.equal(await page.evaluate(()=>window.__practiceState.duel.player.lockedTarget||null),null,'foreign pointer cannot lock');
        assert.equal(await page.evaluate(()=>window.__practiceState.duel.player.attackAim||null),null,'foreign pointer cannot draw selection line');
        await aa.dispatchEvent('pointermove',{pointerId:32,clientX:rotated?100:130,clientY:rotated?130:100});
        await page.waitForFunction(()=>!!window.__practiceState.duel.player.attackAim);
        const aimLine=await page.evaluate(()=>{const s=window.__practiceState.duel.player;return window.MarksmanPractice.frame(s).attackAim;});
        assert.ok(Math.abs(Math.hypot(aimLine.end[0]-aimLine.start[0],aimLine.end[2]-aimLine.start[2])-await page.evaluate(()=>window.MarksmanPractice.stats(window.__practiceState.duel.player).range/100))<1e-9);
        if(screenshots)await page.screenshot({path:resolve(screenshots,`aa-selection-line-${width}.png`)});
        await aa.dispatchEvent('pointerup',{pointerId:32});
        assert.equal(await page.evaluate(()=>window.__practiceState.duel.player.attackAim||null),null,'release clears selection line');
        await page.waitForFunction(()=>window.__practiceState.duel.player.lockedTarget?.startsWith('m'));
        await page.getByLabel('Clear target lock',{exact:true}).waitFor({state:'visible'});
        assert.deepEqual(await page.evaluate(()=>window.__practiceState.duel.player.hero.slice()),lockHero,'target drag never generates movement');
        await page.getByLabel('Clear target lock',{exact:true}).click();
        assert.equal(await page.evaluate(()=>window.__practiceState.duel.player.lockedTarget||null),null);
        // Farm is a separate scenario: do not inherit pending attacks or defeated units from target-lock checks.
        await page.getByRole('button',{name:'Restart practice',exact:true}).click();
        await page.waitForFunction(()=>document.querySelector('.pt-stage-wrap').dataset.phase==='ready');
        const farmStick=page.locator('.pt-joystick'),farmRect=await farmStick.boundingBox();
        await farmStick.dispatchEvent('pointerdown',{pointerId:31,clientX:farmRect.x+farmRect.width/2,clientY:farmRect.y+farmRect.height/2});
        await farmStick.dispatchEvent('pointerup',{pointerId:31});
        await page.waitForFunction(()=>window.__practiceState.duel.lane.units.length>0);
        const farmHero=await page.evaluate(()=>{const d=window.__practiceState.duel;d.bot.next=Infinity;for(const s of[d.player,d.enemy]){s.pending=null;s.attackHeld=false;s.hits=[];s.events=[];s.destination=s.hero.slice();}d.player.deadlines.AA=0;const m=d.lane.units.find(m=>m.side===1);d.lane.units=[m];d.lane.shots=[];m.position=[d.player.hero[0]+1,0,d.player.hero[2]];m.health.hp=1;m.health.defeatedAt=null;m.rewarded=false;m.range=4;m.next=Infinity;return d.player.hero.slice();});
        await page.getByLabel('Farm minions or attack tower',{exact:true}).dispatchEvent('pointerdown',{pointerId:33});
        try{await page.waitForFunction(()=>window.__practiceState.duel.player.training.cs>0,null,{timeout:10000});}catch(error){console.error('Farm fixture state',await page.evaluate(()=>{const d=window.__practiceState.duel,s=d.player;return{time:d.time,finished:d.finished,result:d.result,hero:s.hero,targetId:s.targetId,held:s.attackHeld,pending:s.pending,health:s.health.hp,deadlines:s.deadlines,hits:s.hits,events:s.events,units:d.lane.units,phase:document.querySelector('.pt-stage-wrap').dataset.phase,disabled:document.querySelector('[data-slot="Farm"]').disabled};}));throw error;}
        await page.getByLabel('Farm minions or attack tower',{exact:true}).dispatchEvent('pointerup',{pointerId:33});
        assert.deepEqual(await page.evaluate(()=>window.__practiceState.duel.player.hero.slice()),farmHero,'Farm never generates movement');
        await page.getByLabel('Finish training session',{exact:true}).click();
        await page.getByLabel('Training results',{exact:true}).waitFor({state:'visible'});
        assert.ok((await page.getByLabel('Training results',{exact:true}).textContent()).includes('Gold score: 30'));
        if(screenshots)await page.screenshot({path:resolve(screenshots,`lane-results-${width}.png`)});
      }
      await page.getByRole('button',{name:'Restart practice',exact:true}).click();
      await page.waitForFunction(()=>document.querySelector('.pt-stage-wrap').dataset.phase==='ready'&&document.querySelector('.pt-combo').textContent.startsWith('READY'));
      const reset = await page.locator('.pt-combo').textContent();
      await page.waitForTimeout(150);
      assert.equal(await page.locator('.pt-combo').textContent(),reset,'Restart waits for input');
      const stickRect=await page.locator('.pt-joystick').boundingBox(),sx=stickRect.x+stickRect.width/2,sy=stickRect.y+stickRect.height/2;
      await page.locator('.pt-joystick').dispatchEvent('pointerdown',{pointerId:2,clientX:sx,clientY:sy});
      await page.locator('.pt-joystick').dispatchEvent('pointermove',{pointerId:2,clientX:sx+30,clientY:sy});
      await page.waitForFunction(()=>document.querySelector('.pt-stage-wrap').dataset.phase==='playing');
      await page.evaluate(()=>{const d=window.__practiceState.duel;d.bot.next=Infinity;d.player.health.hp=0;});
      await page.getByLabel('Training results',{exact:true}).waitFor({state:'visible'});
      assert.equal(await page.locator('.pt-joystick i').evaluate(e=>e.style.transform),'','death clears joystick pointer before release');
      assert.ok(await page.locator('.pt-skill[data-slot="Q"]').isDisabled(),'dead actor cannot cast');
      await page.locator('.pt-joystick').dispatchEvent('pointerup',{pointerId:2});
      await page.getByRole('button',{name:'Exit practice',exact:true}).click();
      await page.waitForFunction(()=>document.querySelector('.pt-stage-wrap').dataset.phase==='preview');
    }
    assert.ok(models.some(x => x.includes('/ezreal/')) && models.some(x => x.includes('/jinx/')), 'Both champion models load offline');
    for (const name of ['stone','grass','rock','foliage']) assert.ok(models.some(x=>x.endsWith('/terrain/'+name+'-v1.webp')), name+' terrain texture loads offline');
    await page.getByLabel('Arena mode', { exact: true }).selectOption('practice');
    assert.ok(await page.getByLabel('Q rank', { exact: true }).isEnabled());
    await page.getByRole('button',{name:'Start Practice',exact:true}).click();
    await page.waitForFunction(()=>!document.querySelector('.pt-skill[data-slot="Q"]').disabled);
    await page.locator('.pt-skill[data-slot="Q"]').dispatchEvent('pointerdown',{pointerId:3});
    await page.locator('.pt-skill[data-slot="Q"]').dispatchEvent('pointerup',{pointerId:3});
    await page.waitForFunction(()=>document.querySelector('.pt-log').textContent.includes('Q'));
    await page.getByRole('button',{name:'Restart practice',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('.pt-stage-wrap').dataset.phase==='ready');
    await page.evaluate(()=>{window.MarksmanPractice.placeDummy(window.__practiceState,[15,0,0]);});
    const hero=await page.evaluate(()=>window.__practiceState.hero.slice());
    const cdp=await page.context().newCDPSession(page);
    const center=async selector=>{const r=await page.locator(selector).boundingBox();return {x:r.x+r.width/2,y:r.y+r.height/2};};
    const stickPoint=await center('.pt-joystick'),aaPoint=await center('.pt-skill[data-slot="AA"]'),qPoint=await center('.pt-skill[data-slot="Q"]');
    const touch=async(type,points)=>cdp.send('Input.dispatchTouchEvent',{type,touchPoints:points.map(p=>({...p,radiusX:2,radiusY:2,force:1}))});
    // Real touch capture: AA/skill drag into the joystick never takes ownership.
    for(const [id,point]of[[10,aaPoint],[11,qPoint]]){
      await touch('touchStart',[{id,...point}]);await touch('touchMove',[{id,...stickPoint}]);await page.waitForTimeout(150);
      assert.deepEqual(await page.evaluate(()=>window.__practiceState.hero.slice()),hero,'AA/skill drag must not move hero');
      assert.equal(await page.locator('.pt-joystick i').evaluate(e=>e.style.transform),'');await touch('touchEnd',[]);
    }
    await page.getByRole('button',{name:'Restart practice',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('.pt-stage-wrap').dataset.phase==='ready');
    // A new gesture outside the joystick, including a ground drag, cannot start movement.
    await page.locator('.pt-joystick').dispatchEvent('pointerdown',{pointerId:99,clientX:0,clientY:0});
    await page.locator('.pt-stage canvas').dispatchEvent('pointerdown',{pointerId:99,clientX:width/2,clientY:height/2});
    await page.locator('.pt-joystick').dispatchEvent('pointermove',{pointerId:99,...stickPoint});
    assert.equal(await page.locator('.pt-stage-wrap').getAttribute('data-phase'),'ready');
    await page.evaluate(()=>window.MarksmanPractice.placeDummy(window.__practiceState,[15,0,0]));
    // Joystick finger keeps ownership while a second finger attacks and is released.
    const movingPoint={x:stickPoint.x+18,y:stickPoint.y};
    await touch('touchStart',[{id:20,...stickPoint}]);await touch('touchMove',[{id:20,...movingPoint}]);
    const knob=await page.locator('.pt-joystick i').evaluate(e=>e.style.transform);
    await touch('touchStart',[{id:20,...movingPoint},{id:21,...aaPoint}]);
    await page.locator('.pt-joystick').dispatchEvent('pointermove',{pointerId:999,clientX:0,clientY:0});
    await page.locator('.pt-joystick').dispatchEvent('pointerup',{pointerId:999});
    assert.equal(await page.locator('.pt-joystick i').evaluate(e=>e.style.transform),knob,'Foreign pointer cannot steer or release joystick');
    await touch('touchEnd',[{id:21,...aaPoint}]);
    assert.equal(await page.locator('.pt-joystick i').evaluate(e=>e.style.transform),knob,'AA release preserves joystick');
    await touch('touchEnd',[]);assert.equal(await page.locator('.pt-joystick i').evaluate(e=>e.style.transform),'');
    // Skill cancellation must preserve the independent movement pointer.
    // Start on open lane ground rather than inherit a wall collision from the touch scenario.
    await page.getByRole('button',{name:'Restart practice',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('.pt-stage-wrap').dataset.phase==='ready');
    await page.evaluate(()=>{const s=window.__practiceState;s.hero=[0,0,0];s.destination=s.hero.slice();window.MarksmanPractice.placeDummy(s,[15,0,0]);});
    const stick=page.locator('.pt-joystick'),q=page.locator('.pt-skill[data-slot="Q"]'),aa=page.locator('.pt-skill[data-slot="AA"]');
    await stick.dispatchEvent('pointerdown',{pointerId:41,clientX:stickPoint.x,clientY:stickPoint.y});
    await stick.dispatchEvent('pointermove',{pointerId:41,clientX:movingPoint.x,clientY:movingPoint.y});
    const skillKnob=await stick.locator('i').evaluate(e=>e.style.transform);
    await q.dispatchEvent('pointerdown',{pointerId:42,clientX:qPoint.x,clientY:qPoint.y});
    await q.dispatchEvent('pointermove',{pointerId:42,clientX:qPoint.x+30,clientY:qPoint.y});
    assert.equal(await page.evaluate(()=>window.__practiceState.aimSlot),'Q');
    await q.dispatchEvent('pointercancel',{pointerId:42});
    assert.equal(await page.evaluate(()=>window.__practiceState.aimSlot),null);
    assert.equal(await stick.locator('i').evaluate(e=>e.style.transform),skillKnob,'skill cancel preserves movement pointer');
    const beforeMove=await page.evaluate(()=>window.__practiceState.hero.slice());
    await page.waitForFunction(p=>{const s=window.__practiceState;return Math.hypot(s.hero[0]-p[0],s.hero[2]-p[2])>.02;},beforeMove,{timeout:5000});
    await aa.dispatchEvent('pointerdown',{pointerId:43,clientX:aaPoint.x,clientY:aaPoint.y});
    await aa.dispatchEvent('pointermove',{pointerId:43,clientX:aaPoint.x+30,clientY:aaPoint.y});
    await page.evaluate(()=>window.dispatchEvent(new Event('blur')));
    const cleared=await page.evaluate(()=>{const s=window.__practiceState;return{held:s.attackHeld,pending:s.pending,buffered:s.buffered,queued:s.queued,aim:s.aimSlot,line:s.attackAim,destination:s.destination,hero:s.hero};});
    assert.equal(cleared.held,false);for(const key of['pending','buffered','queued','aim','line'])assert.equal(cleared[key],null,key);
    assert.deepEqual(cleared.destination,cleared.hero);assert.equal(await stick.locator('i').evaluate(e=>e.style.transform),'');
    await aa.dispatchEvent('pointerup',{pointerId:43});await q.dispatchEvent('pointerup',{pointerId:42});
    assert.equal(await page.evaluate(()=>window.__practiceState.attackHeld),false,'late releases cannot restore cleared input');
    await cdp.detach();
    await page.getByRole('button',{name:'Exit practice',exact:true}).click();
    // Saved equipment is read again for a fresh round; named drills keep the input gate.
    await page.evaluate(()=>localStorage.setItem('sharpwr.build',JSON.stringify({champion:'Ezreal',level:15,items:["Guinsoo's Rageblade",'Statikk Shiv'],runes:true})));
    await page.getByLabel('Arena mode',{exact:true}).selectOption('duel');
    for(const scenario of ['kite','dodge','last-hit','tower']) {
      await page.getByLabel('Training scenario',{exact:true}).selectOption(scenario);
      await page.waitForFunction(name=>window.__practiceState?.duel?.scenario===name,scenario);
      const setup=await page.evaluate(()=>{const d=window.__practiceState.duel;return {scenario:d.scenario,build:!!d.player.loadout,ad:window.MarksmanPractice.stats(d.player).ad,time:d.time,damage:d.player.training.damage,duration:d.duration,lane:!!d.lane};});
      assert(setup.build);assert(setup.ad>120);assert.equal(setup.time,0);assert.equal(setup.damage,0);assert.equal(setup.duration,60);
      if(scenario==='last-hit'||scenario==='tower')assert(setup.lane);
    }
    await page.getByRole('button',{name:'Start Practice',exact:true}).click();
    await page.getByRole('button',{name:'Finish training session',exact:true}).click();
    await page.locator('.pt-results:not([hidden])').waitFor();
    assert.match(await page.locator('.pt-results').innerText(),/TOWER/);
    await page.getByRole('button',{name:'Exit practice',exact:true}).click();
    assert.deepEqual(errors, []);
    assert.deepEqual(external.filter(x => !x.endsWith('/app-data/database.json')), []);
    await page.locator('nav a').first().click();
    await page.waitForFunction(() => document.querySelectorAll('.pt-stage canvas').length === 0);
    assert.equal(await page.evaluate(()=>document.body.style.overflow),'');
    await page.close();
    console.log(`PASS offline landscape arena: preview, idle gate, four equal-stat modes, AA/joystick/skill start, restart/exit, two GLBs, navigation (${width}x${height})`);
  }

} finally {
  await browser?.close();
  await new Promise((resolve) => server.close(resolve));
}
