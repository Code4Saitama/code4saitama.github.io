import rawEvents from "../../fb_group_archive/group_events.json";
import { groupImageUrl } from "./groupPosts";

export interface GroupEvent {
  event_id: string;
  title: string;
  date: string;
  date_display: string;
  place: string;
  url: string;
  description: string;
  summary: string;
  detail_text: string;
  header_text: string;
  saved_images: string[];
  discovered_from_post_ids: string[];
  fetched_at: string | null;
  sources: ["facebook-group"];
}

export const groupEvents = (rawEvents as GroupEvent[]).sort((a, b) => {
  if (!a.date) return 1;
  if (!b.date) return -1;
  return a.date.localeCompare(b.date) || a.title.localeCompare(b.title, "ja");
});

export function groupEventImage(event: GroupEvent) {
  return event.saved_images[0] ? groupImageUrl(event.saved_images[0]) : "";
}
