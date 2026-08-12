import type { APIRoute } from "astro";
import { getEvents, pageUrl, sitemapDate } from "../lib/archive";

const staticPages = [
  { path: "index.html", priority: "1.0", changefreq: "weekly" },
  { path: "timeline.html", priority: "0.9", changefreq: "monthly" },
  { path: "themes.html", priority: "0.8", changefreq: "monthly" },
  { path: "research.html", priority: "0.8", changefreq: "monthly" },
  { path: "about.html", priority: "0.7", changefreq: "monthly" }
];

export const GET: APIRoute = async () => {
  const events = await getEvents();
  const eventPages = events
    .filter((event) => event.data.hasDetail)
    .map((event) => ({
      path: event.data.page,
      lastmod: sitemapDate(event.data.date),
      priority: "0.6",
      changefreq: "yearly"
    }));
  const lastmod = new Date().toISOString().slice(0, 10);
  const urls = [
    ...staticPages.map((page) => ({ ...page, lastmod })),
    ...eventPages
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
