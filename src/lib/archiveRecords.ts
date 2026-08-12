import rawRecords from "../../fb_group_archive/public_records.json";
import type { SourceKey } from "./sources";

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
export const activityRecords = archiveRecords.filter((record) => record.kind === "activity" && record.date);
export const referenceRecords = archiveRecords.filter((record) => record.kind === "reference");
export function archiveRecordImage(record: ArchiveRecord) {
  return record.image ? `/group-media/${record.image.replace(/^images\//, "")}` : "";
}
export function archiveRecordImages(record: ArchiveRecord) {
  return record.images.map((image) => `/group-media/${image.replace(/^images\//, "")}`);
}
