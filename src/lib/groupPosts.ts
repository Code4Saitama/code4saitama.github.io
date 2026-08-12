import rawPosts from "../../fb_group_archive/posts.json";
import deletionSelection from "../../fb_group_archive/facebook-posts-selected-for-deletion.json";

export interface GroupPostImage {
  alt: string;
  h: number;
  src: string;
  w: number;
}

export interface GroupPost {
  id: string;
  date: string;
  date_display: string;
  author: string;
  url: string;
  text: string;
  images: GroupPostImage[];
  saved_images: string[];
}

const deletedIds = new Set(deletionSelection.posts.map((post) => String(post.post_id)));

export const groupPosts = (rawPosts as GroupPost[])
  .filter((post) => !deletedIds.has(post.id))
  .sort((a, b) => a.date.localeCompare(b.date) || a.id.localeCompare(b.id));

export const groupPostsById = new Map(groupPosts.map((post) => [post.id, post]));

export function cleanGroupAuthor(author = "") {
  return author
    .split("\n")[0]
    .replace(/さんが.*$/, "")
    .trim() || "投稿者不明";
}

export function groupPostBody(post: GroupPost) {
  let body = post.text.replaceAll("\u00a0", " ").replace(/\r\n/g, "\n").trim();
  if (!body) return "";

  const authorPrefix = post.author.replaceAll("\u00a0", " ").trim();
  if (authorPrefix && body.startsWith(authorPrefix)) body = body.slice(authorPrefix.length).trim();

  const lines = body.split("\n");
  while (lines.length && (
    !lines[0].trim() ||
    lines[0].trim() === "·" ||
    lines[0].trim() === "管理者" ||
    lines[0].trim() === "フォローする" ||
    /^\d{4}年\d{1,2}月\d{1,2}日$/.test(lines[0].trim())
  )) lines.shift();

  return lines.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

export function groupPostTitle(post: GroupPost) {
  const action = post.author.replace(/\s+/g, " ").trim();
  if (/さんが.+(?:作成|変更|追加|貢献)/.test(action)) return truncate(action, 96);

  const body = groupPostBody(post);
  const firstLine = body.split("\n").map((line) => line.trim()).find(Boolean);
  if (firstLine) return truncate(firstLine.replace(/\.\.\. さらに表示$/, ""), 96);

  const alt = post.images.map((image) => image.alt?.trim()).find((value) => value && !value.includes("説明はありません"));
  if (alt) return truncate(alt, 96);
  return `${cleanGroupAuthor(post.author)}の投稿`;
}

export function groupPostExcerpt(post: GroupPost, limit = 170) {
  const compact = groupPostBody(post).replace(/\s+/g, " ").trim();
  if (!compact) return post.saved_images.length ? `写真 ${post.saved_images.length}点を保存した投稿です。` : "本文を取得できなかった投稿です。";
  return truncate(compact, limit);
}

export function groupPostPage(post: GroupPost) {
  return `/posts/${post.id}.html`;
}

export function groupImageUrl(savedPath: string) {
  return `/group-media/${savedPath.replace(/^images\//, "")}`;
}

function truncate(value: string, limit: number) {
  return value.length <= limit ? value : `${value.slice(0, limit - 1)}…`;
}
