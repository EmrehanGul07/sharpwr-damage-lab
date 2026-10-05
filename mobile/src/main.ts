import "./styles.css";
import { App } from "@capacitor/app";
import { version } from "../package.json";
import { type DataState, loadDatabase } from "./data";
import { h } from "./dom";
import {
  APK_URL,
  confirmStarted,
  downloadForNextLaunch,
  latestWebUpdate,
  planUpdate,
  readApkVersion,
  recordLaunch,
  restartNow,
} from "./live-update";
import { type KeyValueStore, downloadDatabase, readSaved, save } from "./online";
import { type Route, href, parseRoute } from "./router";
import { about } from "./views/about";
import { championDetail, championList } from "./views/champions";
import { itemDetail, itemList } from "./views/items";
import { runeDetail, runeList } from "./views/runes";
import { tierList } from "./views/tiers";
import type { View } from "./views/shared";

const title = document.getElementById("title") as HTMLElement;
const back = document.getElementById("back") as HTMLButtonElement;
const viewRoot = document.getElementById("view") as HTMLElement;
const notice = document.getElementById("notice") as HTMLElement;
const tabs = Array.from(document.querySelectorAll<HTMLAnchorElement>(".tabbar a"));

function resolve(state: DataState, route: Route): View {
  const { db } = state;
  const [first, second] = route.parts;
  switch (route.section) {
    case "champions":
      return first ? championDetail(db, first, route.params) : championList(db);
    case "tiers":
      return tierList(db);
    case "items":
      return first && second ? itemDetail(db, first, second) : itemList(db, route.params);
    case "runes":
      return first ? runeDetail(db, first) : runeList(db, route.params);
    case "about":
      return about(state);
  }
}

function render(state: DataState): void {
  const route = parseRoute(location.hash);
  const view = resolve(state, route);
  title.textContent = view.title;
  back.hidden = !view.back;
  viewRoot.replaceChildren(view.body);
  for (const tab of tabs) {
    const active = tab.dataset.section === route.section;
    tab.classList.toggle("active", active);
    if (active) tab.setAttribute("aria-current", "page");
    else tab.removeAttribute("aria-current");
  }
  window.scrollTo(0, 0);
}

function goBack(): void {
  if (history.length > 1) history.back();
  else location.hash = href(parseRoute(location.hash).section);
}

async function start(): Promise<void> {
  back.addEventListener("click", goBack);
  // Android back button: return to the previous page, or leave the app from a top-level list.
  await App.addListener("backButton", ({ canGoBack }) => {
    if (canGoBack) history.back();
    else void App.exitApp();
  });
  const storage = localStore();
  let state: DataState;
  try {
    state = (storage && readSaved(storage, __APP_BUILD__)) ?? { db: await loadDatabase(), downloadedAt: null };
  } catch (error) {
    viewRoot.replaceChildren(h("p", { class: "status" }, `Could not load the database: ${(error as Error).message}`));
    return;
  }
  window.addEventListener("hashchange", () => render(state));
  render(state);

  const db = await downloadDatabase();
  if (db) {
    // Shown from the next screen on, so the page being read does not jump.
    state = { db, downloadedAt: new Date().toISOString() };
    if (storage) save(storage, __APP_BUILD__, state);
  }
}

function localStore(): KeyValueStore | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function showNotice(title: string, text: string, action: HTMLElement): void {
  notice.replaceChildren(
    h("p", {}, h("strong", {}, title), ` ${text}`),
    h("div", { class: "notice-actions" }, action, h("button", { class: "button", type: "button", onclick: () => (notice.hidden = true) }, "Later")),
  );
  notice.hidden = false;
}

/**
 * Preview builds only (Play Store builds are updated by Google Play): new screens download in the
 * background; a new Android shell is offered as an APK download.
 */
async function checkForUpdates(): Promise<void> {
  const storage = localStore();
  if (!storage) return;
  const failed = recordLaunch(storage, version);
  const apk = await readApkVersion();
  const update = apk ? await latestWebUpdate() : null;
  if (!apk || !update) return;
  const plan = planUpdate(update, version, apk, failed);
  if (plan.action === "download" && (await downloadForNextLaunch(storage, plan.update))) {
    const restart = h("button", { class: "button primary", type: "button", onclick: restartNow }, "Restart now");
    showNotice(`SharpWR ${plan.update.version} is ready.`, "It opens the next time you start the app.", restart);
  } else if (plan.action === "apk") {
    // External links open in the phone's browser, which downloads the APK.
    const download = h("a", { class: "button primary", href: APK_URL }, "Download");
    showNotice(`SharpWR ${plan.version} needs a new app download.`, `You have ${apk}.`, download);
  }
}

confirmStarted();
void start();
if (import.meta.env.VITE_PREVIEW_BUILD === "1") void checkForUpdates();
