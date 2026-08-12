import rawRecords from "../../fb_group_archive/public_records.json";
import rawPosts from "../../fb_group_archive/posts.json";
import rawEvents from "../../fb_group_archive/group_events.json";
import type { SourceKey } from "./sources";

export interface GroupComment {
  id: string;
  timestamp_label: string;
  text: string;
  summary: string;
  saved_images: string[];
}

export interface GroupPost {
  id: string;
  date: string;
  text: string;
  summary: string;
  comments_summary: string;
  saved_images: string[];
  fb_event_links: Array<{ event_id: string; title?: string }>;
  comments: GroupComment[];
}

export interface GroupEvent {
  event_id: string;
  title: string;
  date: string;
  place: string;
  url: string;
  description: string;
  summary: string;
  saved_images: string[];
}

export interface ArchiveSourceLink {
  label: string;
  url: string;
  type: "post" | "event";
}

export interface ArchiveRecord {
  id: string;
  date: string;
  sort: number;
  title: string;
  summary: string;
  kind: "activity" | "reference";
  themeKeys: string[];
  themes: string[];
  sources: SourceKey[];
  image: string;
  images: string[];
  commentCount: number;
  sourceTypes: Array<"post" | "event">;
  sourceCount: number;
}

export const archiveRecords = rawRecords as ArchiveRecord[];
export const groupPosts = rawPosts as GroupPost[];
export const groupEvents = rawEvents as GroupEvent[];
export const activityRecords = archiveRecords.filter((record) => record.kind === "activity" && record.date);
export const referenceRecords = archiveRecords.filter((record) => record.kind === "reference");
export function archiveRecordPath(record: ArchiveRecord) {
  return `/archive/${record.id}.html`;
}
export function archiveRecordImage(record: ArchiveRecord) {
  return record.image ? `/group-media/${record.image.replace(/^images\//, "")}` : "";
}
export function archiveRecordImages(record: ArchiveRecord) {
  return record.images.map((image) => `/group-media/${image.replace(/^images\//, "")}`);
}

export function groupMediaPath(image: string) {
  return `/group-media/${image.replace(/^images\//, "")}`;
}

export function groupPostUrl(postId: string) {
  return `https://www.facebook.com/groups/186097664924714/posts/${postId}/`;
}

export function archiveRecordPosts(record: ArchiveRecord) {
  if (record.id.startsWith("fb-post-")) {
    const postId = record.id.replace(/^fb-post-/, "");
    return groupPosts.filter((post) => String(post.id) === postId);
  }
  if (record.id.startsWith("fb-event-")) {
    const eventId = record.id.replace(/^fb-event-/, "");
    return groupPosts.filter((post) => post.fb_event_links.some((link) => String(link.event_id) === eventId));
  }
  return [];
}

export function archiveRecordEvent(record: ArchiveRecord) {
  if (!record.id.startsWith("fb-event-")) return undefined;
  const eventId = record.id.replace(/^fb-event-/, "");
  return groupEvents.find((event) => String(event.event_id) === eventId);
}

export function archiveRecordSourceLinks(record: ArchiveRecord): ArchiveSourceLink[] {
  const posts = archiveRecordPosts(record);
  const event = archiveRecordEvent(record);
  return [
    ...posts.map((post, index) => ({
      label: posts.length > 1 ? `元のFB Group投稿 ${index + 1}` : "元のFB Group投稿",
      url: groupPostUrl(String(post.id)),
      type: "post" as const,
    })),
    ...(event?.url ? [{ label: "元のFacebookイベント", url: event.url, type: "event" as const }] : []),
  ];
}
