/** Minimal DOM builder. Text is always set as text, never parsed as HTML. */
import { remoteAsset } from "./online";

type Child = Node | string | number | null | undefined | false;
type Props = Record<string, string | number | boolean | EventListener | undefined>;

export function h<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  props: Props = {},
  ...children: Child[]
): HTMLElementTagNameMap[K] {
  const element = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value === undefined || value === false) continue;
    if (key === "class") element.className = String(value);
    else if (key.startsWith("on") && typeof value === "function") {
      element.addEventListener(key.slice(2).toLowerCase(), value);
    } else element.setAttribute(key, value === true ? "" : String(value));
  }
  for (const child of children) {
    if (child === null || child === undefined || child === false) continue;
    element.append(child instanceof Node ? child : String(child));
  }
  return element;
}

/**
 * Bundled icon, or an empty placeholder of the same size when a record has none. An icon the app
 * does not bundle (added by an online data update) loads from GitHub, or shows the placeholder offline.
 */
export function icon(src: string | null, alt: string, size: number, extraClass = ""): HTMLElement {
  const className = `icon ${extraClass}`.trim();
  const placeholder = () => h("span", { class: `${className} icon-empty`, style: `width:${size}px;height:${size}px` });
  if (!src) return placeholder();
  const image = h("img", { class: className, src, alt, width: size, height: size, loading: "lazy" });
  let triedOnline = false;
  image.addEventListener("error", () => {
    if (triedOnline) return image.replaceWith(placeholder());
    triedOnline = true;
    image.src = remoteAsset(src);
  });
  return image;
}
