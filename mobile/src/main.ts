import "./styles.css";
import { App } from "@capacitor/app";
import { type Database, loadDatabase } from "./data";
import { h } from "./dom";
import { type Route, href, parseRoute } from "./router";
import { about } from "./views/about";
import { championDetail, championList } from "./views/champions";
import { itemDetail, itemList } from "./views/items";
import { runeDetail, runeList } from "./views/runes";
import type { View } from "./views/shared";

const title = document.getElementById("title") as HTMLElement;
const back = document.getElementById("back") as HTMLButtonElement;
const viewRoot = document.getElementById("view") as HTMLElement;
const tabs = Array.from(document.querySelectorAll<HTMLAnchorElement>(".tabbar a"));

function resolve(db: Database, route: Route): View {
  const [first, second] = route.parts;
  switch (route.section) {
    case "champions":
      return first ? championDetail(db, first) : championList(db);
    case "items":
      return first && second ? itemDetail(db, first, second) : itemList(db, route.params);
    case "runes":
      return first ? runeDetail(db, first) : runeList(db, route.params);
    case "about":
      return about(db);
  }
}

function render(db: Database): void {
  const route = parseRoute(location.hash);
  const view = resolve(db, route);
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
  try {
    const db = await loadDatabase();
    window.addEventListener("hashchange", () => render(db));
    render(db);
  } catch (error) {
    viewRoot.replaceChildren(h("p", { class: "status" }, `Could not load the database: ${(error as Error).message}`));
  }
}

void start();
