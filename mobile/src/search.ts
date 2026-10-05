/** Forgiving search: ignores case, accents, spaces and punctuation ("kaisa" finds "Kai'Sa"). */

export function normalize(text: string): string {
  return text
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "");
}

export function matches(query: string, ...fields: string[]): boolean {
  const needle = normalize(query);
  return needle === "" || fields.some((field) => normalize(field).includes(needle));
}
