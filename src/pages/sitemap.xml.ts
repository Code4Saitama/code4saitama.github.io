import type { APIRoute } from "astro";
import { getEvents, getNotes, noteArchivePath, pageUrl, sitemapDate } from "../lib/archive";
import { archiveRecordPath, archiveRecords } from "../lib/archiveRecords";

const staticPages = [
  { path: "index.html", priority: "1.0", changefreq: "weekly" },
  { path: "timeline.html", priority: "0.9", changefreq: "monthly" },
  { path: "themes.html", priority: "0.8", changefreq: "monthly" },
  { path: "research.html", priority: "0.8", changefreq: "monthly" }
];

export const GET: APIRoute = async () => {
  const events = await getEvents();
  const notes = await getNotes();
  const eventPages = events.map((event) => ({
      path: event.data.page,
      lastmod: sitemapDate(event.data.date),
      priority: "0.6",
      changefreq: "yearly"
    }));
  const archivePages = archiveRecords.map((record) => ({
    path: archiveRecordPath(record),
    lastmod: sitemapDate(record.date),
    priority: "0.5",
    changefreq: "yearly"
  }));
  const notePages = notes.map((note) => ({
    path: noteArchivePath(note.id),
    lastmod: sitemapDate(note.data.date),
    priority: "0.5",
    changefreq: "yearly"
  }));
  const lastmod = new Date().toISOString().slice(0, 10);
  const urls = [
    ...staticPages.map((page) => ({ ...page, lastmod })),
    ...eventPages,
    ...archivePages,
    ...notePages
  ];

  return new Response(
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
      `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
      urls
        .map(
          (url) => `  <url>
    <loc>${pageUrl(url.path)}</loc>
    <lastmod>${url.lastmod}</lastmod>
    <changefreq>${url.changefreq}</changefreq>
    <priority>${url.priority}</priority>
  </url>`
        )
        .join("\n") +
      `\n</urlset>\n`,
    {
      headers: {
        "Content-Type": "application/xml; charset=utf-8"
      }
    }
  );
};
