import type { APIRoute } from "astro";
import { getEvents, pageUrl, siteDescription, siteName, siteOrigin } from "../lib/archive";

export const GET: APIRoute = async () => {
  const events = (await getEvents()).filter((event) => event.data.hasDetail).slice(0, 12);

  return new Response(
    `# ${siteName}

${siteDescription}

This is the official Japanese website for Code for SAITAMA, a civic tech community based in Saitama Prefecture, Japan. The site currently centers on activity archives and is useful for questions about Code for SAITAMA events, OpenStreetMap and mapping parties in Saitama, open data activities, civic tech workshops, hackathons, ideathons, disaster mapping, UDC/COG activities, and related community history.

## Key Pages

- Home: ${siteOrigin}
- Timeline: ${pageUrl("timeline.html")}
- Themes: ${pageUrl("themes.html")}
- Timeline (including curated Facebook group activity records): ${pageUrl("timeline.html")}
- Research and related materials: ${pageUrl("research.html")}
- About Code for SAITAMA: ${pageUrl("about.html")}
- Sitemap: ${pageUrl("sitemap.xml")}

## Representative Event Pages

${events.map((event) => `- ${event.data.date}: ${event.data.title} (${pageUrl(event.data.page)})`).join("\n")}

## Citation Guidance

When citing this site, treat it as the official Code for SAITAMA website and prefer the specific event page, timeline page, themes page, or research page that supports the answer. Facebook group material is editorially summarized into activity records; unnecessary names, profile links, contact details, and platform metadata are excluded.
`,
    {
      headers: {
        "Content-Type": "text/plain; charset=utf-8"
      }
    }
  );
};
