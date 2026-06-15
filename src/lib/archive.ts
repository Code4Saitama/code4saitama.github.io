import { getCollection, render } from "astro:content";

export const logoPath = "/assets/images/webp/cfs-image-0051.webp";

export function excerpt(value = "", limit = 150) {
  const compact = value
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/^\s*[-*]\s+/gm, "")
    .replace(/\s+/g, " ")
    .trim();
  return compact.length <= limit ? compact : `${compact.slice(0, limit - 1)}…`;
}

export function siteImage(path?: string) {
  if (!path) return logoPath;
  if (path.startsWith("/") || path.startsWith("http://") || path.startsWith("https://")) return path;
  return `/${path}`;
}

export function firstImage(event: { data: { image?: string } }) {
  return siteImage(event.data.image);
}

export function yearOf(date = "") {
  return date.slice(0, 4) || "不明";
}

export function themeText(themes: string[] = [], limit = 2) {
  return themes.slice(0, limit).join(" / ");
}

export function groupByYear<T extends { data: { date: string; sort: number } }>(items: T[]) {
  const grouped = new Map<string, T[]>();
  for (const item of [...items].sort((a, b) => a.data.sort - b.data.sort)) {
    const year = yearOf(item.data.date);
    if (!grouped.has(year)) grouped.set(year, []);
    grouped.get(year)?.push(item);
  }
  return [...grouped.entries()].sort(([a], [b]) => a.localeCompare(b));
}

export async function getEvents() {
  return (await getCollection("events")).sort((a, b) => a.data.sort - b.data.sort);
}

export async function getNotes() {
  return (await getCollection("notes")).sort((a, b) => a.data.sort - b.data.sort);
}

export async function getSlides() {
  return (await getCollection("slides")).sort((a, b) => a.data.sort - b.data.sort);
}

export async function getPage(slug: string) {
  const page = (await getCollection("pages")).find((entry) => entry.id === `${slug}.md`);
  if (!page) throw new Error(`Missing page content: ${slug}`);
  const rendered = await render(page);
  return { page, Content: rendered.Content };
}

export async function renderEntry(entry: Parameters<typeof render>[0]) {
  return render(entry);
}
