import { defineCollection, z } from "astro:content";

const events = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    eventId: z.string(),
    date: z.string(),
    start: z.string().optional(),
    end: z.string().optional(),
    sort: z.number(),
    place: z.string().optional(),
    themes: z.array(z.string()),
    themeKeys: z.array(z.string()),
    page: z.string(),
    image: z.string().optional(),
    images: z.array(z.string()).default([]),
    fbid: z.string().optional(),
    sources: z.array(z.enum(["facebook-page", "facebook-group", "deep-research"])).default([]),
    groupPostIds: z.array(z.string()).default([]),
    hasDetail: z.boolean()
  })
});

const notes = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    date: z.string(),
    sort: z.number(),
    theme: z.string(),
    source: z.string(),
    sources: z.array(z.enum(["facebook-page", "facebook-group", "deep-research"])).default([])
  })
});

const pages = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    eyebrow: z.string().optional(),
    lead: z.string().optional()
  })
});

const slides = defineCollection({
  type: "content",
  schema: z.object({
    assetId: z.string(),
    date: z.string(),
    caption: z.string(),
    text: z.string(),
    eventDate: z.string().optional(),
    sort: z.number()
  })
});

export const collections = { events, notes, pages, slides };
