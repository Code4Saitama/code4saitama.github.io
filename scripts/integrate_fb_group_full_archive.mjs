import fs from "node:fs";
import path from "node:path";

const repoRoot = path.resolve(import.meta.dirname, "..");
const archiveDir = path.join(repoRoot, "fb_group_archive");
const args = process.argv.slice(2);
const dryRun = args.includes("--dry-run");
const checkpointPath = args.find((argument) => !argument.startsWith("--")) || "/tmp/fb_group_full_checkpoint.json";
const postsPath = path.join(archiveDir, "posts.json");

const posts = JSON.parse(fs.readFileSync(postsPath, "utf8"));
const checkpoint = JSON.parse(fs.readFileSync(checkpointPath, "utf8"));
const fetchedById = new Map(checkpoint.posts.map((post) => [String(post.id), post]));

const noiseLines = new Set([
  "·",
  "管理者",
  "フォローする",
  "投稿をシェアしました",
  "シェアする",
  "編集済み",
  "いいね！",
  "リアクションする",
  "非表示にするまたは報告",
  "コメントする",
]);

function normalizeLines(value = "") {
  return String(value)
    .replaceAll("\u00a0", " ")
    .replace(/\r\n/g, "\n")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function isNoiseLine(line) {
  return noiseLines.has(line)
    || /^Code for SAITAMA～/.test(line)
    || /^プライバシー設定:/.test(line)
    || /^\d{4}年\d{1,2}月\d{1,2}日(?:.+)?$/.test(line)
    || /^\d+(?:件|人)?$/.test(line)
    || /^\d+(?:年|か月|週間|日|時間|分|秒)$/.test(line)
    || /^リアクション\d+件/.test(line)
    || /^いいね！:/.test(line);
}

function cleanPostText(raw = "", post) {
  const author = String(post.author || "").split("\n")[0].replace(/さんが.*$/, "").trim();
  const lines = normalizeLines(raw);
  while (lines.length && (isNoiseLine(lines[0]) || lines[0] === author)) lines.shift();
  while (lines.length && isNoiseLine(lines.at(-1))) lines.pop();
  return lines.filter((line) => !isNoiseLine(line)).join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

function cleanCommentText(raw = "", author = "") {
  const lines = normalizeLines(raw);
  while (lines.length && (isNoiseLine(lines[0]) || lines[0] === author)) lines.shift();
  while (lines.length && isNoiseLine(lines.at(-1))) lines.pop();
  return lines.filter((line) => !isNoiseLine(line)).join("\n").trim();
}

function summarize(value = "", limit = 180) {
  const compact = value.replace(/https?:\/\/\S+/g, "").replace(/\s+/g, " ").trim();
  if (!compact) return "";
  const sentences = compact.match(/[^。！？!?]+[。！？!?]?/g) || [compact];
  let summary = "";
  for (const sentence of sentences) {
    if (summary && summary.length + sentence.length > limit) break;
    summary += sentence;
    if (summary.length >= Math.min(80, limit)) break;
  }
  if (!summary) summary = compact.slice(0, limit);
  return summary.length <= limit ? summary : `${summary.slice(0, limit - 1)}…`;
}

function stableImageKey(image) {
  const photoId = String(image.photo_url || "").match(/[?&]fbid=(\d+)/)?.[1];
  if (photoId) return `photo:${photoId}`;
  try {
    return new URL(image.src).pathname;
  } catch {
    return image.src;
  }
}

function imageExtension(image) {
  try {
    const extension = path.extname(new URL(image.src).pathname).toLowerCase();
    return [".jpg", ".jpeg", ".png", ".gif", ".webp"].includes(extension) ? extension : ".jpg";
  } catch {
    return ".jpg";
  }
}

const commentImageManifest = [];
const eventLinkMap = new Map();
let recoveredBodies = 0;
let commentCount = 0;

for (const post of posts) {
  const fetched = fetchedById.get(String(post.id));
  const fetchedBody = fetched ? cleanPostText(fetched.post_raw_text, post) : "";
  const existingBody = cleanPostText(post.text, post);
  const body = fetchedBody || existingBody;
  if (!existingBody && fetchedBody) recoveredBodies += 1;

  post.text = body;
  post.summary = summarize(body);
  post.fetched_at = fetched?.fetched_at || null;
  post.expected_comment_count = fetched?.expected_comment_count ?? null;
  post.fb_event_links = (fetched?.event_links || []).map((event) => {
    const match = String(event.url).match(/\/events\/(\d+)/);
    const eventId = match?.[1] || "";
    if (eventId && !eventLinkMap.has(eventId)) {
      eventLinkMap.set(eventId, {
        event_id: eventId,
        url: `https://www.facebook.com/events/${eventId}/`,
        title: String(event.title || "").replace(/\s+/g, " ").trim(),
        discovered_from_post_ids: [],
      });
    }
    if (eventId) eventLinkMap.get(eventId).discovered_from_post_ids.push(post.id);
    return { event_id: eventId, url: eventId ? `https://www.facebook.com/events/${eventId}/` : event.url, title: event.title };
  });

  post.comments = (fetched?.comments || []).map((comment, commentIndex) => {
    const commentId = String(comment.comment_id || `${post.id}-${commentIndex + 1}`);
    const text = cleanCommentText(comment.raw_text, comment.author);
    const savedImages = [];
    const seen = new Set();
    for (const image of comment.images || []) {
      const key = stableImageKey(image);
      if (!image.src || seen.has(key)) continue;
      seen.add(key);
      const relativePath = path.posix.join(
        "images",
        "comments",
        post.date.slice(0, 4),
        post.id,
        commentId,
        `${String(savedImages.length + 1).padStart(2, "0")}${imageExtension(image)}`,
      );
      savedImages.push(relativePath);
      commentImageManifest.push({
        post_id: post.id,
        comment_id: commentId,
        author: comment.author,
        timestamp_label: comment.timestamp_label,
        alt: image.alt,
        width: image.width,
        height: image.height,
        photo_url: image.photo_url,
        source_url: image.src,
        saved_path: relativePath,
      });
    }
    commentCount += 1;
    return {
      id: commentId,
      parent_comment_id: String(comment.parent_comment_id || ""),
      author: String(comment.author || "").trim() || "投稿者不明",
      timestamp_label: String(comment.timestamp_label || "").trim(),
      permalink: String(comment.permalink || "").split("&__cft__")[0],
      text,
      summary: summarize(text, 140),
      images: comment.images || [],
      saved_images: savedImages,
    };
  });

  const commentText = post.comments.map((comment) => comment.text).filter(Boolean).join(" ");
  post.comments_summary = summarize(commentText, 240);
}

for (const event of eventLinkMap.values()) {
  event.discovered_from_post_ids = [...new Set(event.discovered_from_post_ids)];
}

const crawlReport = {
  generated_at: new Date().toISOString(),
  checkpoint_path: checkpointPath,
  total_posts: posts.length,
  fetched_posts: fetchedById.size,
  missing_posts: posts.filter((post) => !fetchedById.has(String(post.id))).map((post) => post.id),
  errors: checkpoint.errors || [],
  recovered_bodies: recoveredBodies,
  comments: commentCount,
  comment_images: commentImageManifest.length,
  discovered_events: eventLinkMap.size,
};

if (!dryRun) {
  fs.writeFileSync(postsPath, `${JSON.stringify(posts, null, 2)}\n`);
  fs.writeFileSync(path.join(archiveDir, "comment_images_manifest.json"), `${JSON.stringify(commentImageManifest, null, 2)}\n`);
  fs.writeFileSync(path.join(archiveDir, "group_events.json"), `${JSON.stringify([...eventLinkMap.values()], null, 2)}\n`);
  fs.writeFileSync(path.join(archiveDir, "full_crawl_report.json"), `${JSON.stringify(crawlReport, null, 2)}\n`);
}

console.log(JSON.stringify(crawlReport, null, 2));
