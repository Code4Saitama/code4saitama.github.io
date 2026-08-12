import fs from "node:fs";
import path from "node:path";

const repoRoot = path.resolve(import.meta.dirname, "..");
const archiveDir = path.join(repoRoot, "fb_group_archive");
const postsPath = path.join(archiveDir, "posts.json");
const apply = process.argv.includes("--apply");
const previousReportPath = path.join(archiveDir, "event_filter_manifest.json");

const posts = JSON.parse(fs.readFileSync(postsPath, "utf8"));
const reviewedDeletionPath = path.join(archiveDir, "facebook-posts-selected-for-deletion.json");
const reviewedDeletion = fs.existsSync(reviewedDeletionPath)
  ? JSON.parse(fs.readFileSync(reviewedDeletionPath, "utf8"))
  : { posts: [] };
const reviewedDeletionIds = new Set(reviewedDeletion.posts.map((post) => String(post.post_id)));

function frontmatterValue(source, key) {
  const match = source.match(new RegExp(`^${key}:\\s*(.+)$`, "m"));
  if (!match) return undefined;
  const value = match[1].trim();
  try {
    return JSON.parse(value);
  } catch {
    return value.replace(/^['"]|['"]$/g, "");
  }
}

const eventsDir = path.join(repoRoot, "src", "content", "events");
const knownEvents = fs.readdirSync(eventsDir).filter((name) => name.endsWith(".md")).map((name) => {
  const source = fs.readFileSync(path.join(eventsDir, name), "utf8");
  return {
    title: frontmatterValue(source, "title") || name,
    date: String(frontmatterValue(source, "date") || "").replaceAll(".", "-"),
    groupPostIds: frontmatterValue(source, "groupPostIds") || [],
    page: frontmatterValue(source, "page") || "",
  };
});
const linkedPostIds = new Set(knownEvents.flatMap((event) => event.groupPostIds.map(String)));

const eventPattern = /(イベント|勉強会|ミートアップ|meetup|ミーティング|会合|もくもく|アイデアソン|ハッカソン|マッピングパーティ|ワークショップ|セミナー|講座|フォーラム|サミット|説明会|交流会|トークイベント|発表会|コンテスト|オープンデータデイ|open data day|udc|アーバンデータチャレンジ|定例会|作業会|訓練|報告会|上映会|研究会|シンポジウム|カンファレンス|懇親会)/i;
const civicPattern = /(code for|シビックテック|オープンデータ|open data|openstreetmap|\bosm\b|マッピング|地図|\bgis\b|qgis|地域課題|市民活動|自治体|行政|公共|防災|災害|バリアフリー|車いす|localwiki|\budc\b|アーバンデータ|アイデアソン|ハッカソン|arduino|\biot\b|まちづくり|地域情報|sdgs|データ活用|公民連携|市民協働)/i;
const unavailablePattern = /(このコンテンツは現在ご利用いただけません|所有者がシェア先を一部の人のみに限定|コンテンツが削除された)/;

function normalize(value = "") {
  return String(value)
    .normalize("NFKC")
    .toLowerCase()
    .replace(/code\s*for\s*saitama/g, "")
    .replace(/[\s\p{P}\p{S}]/gu, "");
}

function daysBetween(a, b) {
  const aTime = Date.parse(`${a}T00:00:00Z`);
  const bTime = Date.parse(`${b}T00:00:00Z`);
  return Number.isFinite(aTime) && Number.isFinite(bTime) ? Math.abs(aTime - bTime) / 86400000 : Infinity;
}

function matchKnownEvent(post, combined) {
  const normalizedCombined = normalize(combined);
  return knownEvents.find((event) => {
    if (daysBetween(post.date, event.date) > 90) return false;
    const title = normalize(event.title)
      .replace(/^(満員御礼|初心者歓迎|申込完了|中止)/, "")
      .replace(/^\d+月\d+日/, "");
    return title.length >= 8 && normalizedCombined.includes(title);
  });
}

function classify(post) {
  if (reviewedDeletionIds.has(String(post.id))) {
    return { keep: false, reason: "目視レビューで非シビックテックと判定済み" };
  }
  if (linkedPostIds.has(String(post.id))) {
    return { keep: true, reason: "既存イベント記録から参照されている" };
  }

  const commentText = (post.comments || []).map((comment) => comment.text).join("\n");
  const eventLinkText = (post.fb_event_links || []).map((event) => event.title).join("\n");
  const combined = [post.author, post.text, commentText, eventLinkText].filter(Boolean).join("\n");
  const hasUsefulBody = Boolean(String(post.text || "").trim()) && !unavailablePattern.test(post.text);
  const knownEvent = matchKnownEvent(post, combined);
  if (knownEvent) {
    return { keep: true, reason: `既存イベント名と一致: ${knownEvent.title}`, matched_event_page: knownEvent.page };
  }

  const hasEventContext = eventPattern.test(combined);
  const hasCivicContext = civicPattern.test(combined);
  if ((post.fb_event_links || []).length > 0 && hasCivicContext) {
    return { keep: true, reason: "Facebookイベントリンクとシビックテック文脈がある" };
  }
  if (hasEventContext && hasCivicContext) {
    return { keep: true, reason: "イベント表現とシビックテック表現が共存する" };
  }

  const sameDayEvent = knownEvents.find((event) => event.date === post.date);
  const hasArchiveEvidence = Boolean(post.text || commentText || post.saved_images.length || (post.comments || []).some((comment) => comment.saved_images.length));
  if (sameDayEvent && hasArchiveEvidence && /(参加|開催|会場|写真|作業|発表|成果|終了|お疲れ)/.test(combined)) {
    return { keep: true, reason: `既存イベント開催日と一致: ${sameDayEvent.title}`, matched_event_page: sameDayEvent.page };
  }

  if (!hasUsefulBody && !commentText) {
    return { keep: false, reason: "本文とコメントを取得できず、イベント関連性を確認できない" };
  }
  if (!hasEventContext) return { keep: false, reason: "イベントに関する記述がない" };
  if (!hasCivicContext) return { keep: false, reason: "シビックテックに関する記述がない" };
  return { keep: false, reason: "シビックテックイベントとの関連を確認できない" };
}

const classified = posts.map((post) => ({
  post_id: post.id,
  date: post.date,
  author: post.author,
  url: post.url,
  text_preview: String(post.text || "").replace(/\s+/g, " ").slice(0, 240),
  post_image_paths: post.saved_images,
  comment_image_paths: (post.comments || []).flatMap((comment) => comment.saved_images),
  ...classify(post),
}));
const keptIds = new Set(classified.filter((item) => item.keep).map((item) => item.post_id));
const keptPosts = posts.filter((post) => keptIds.has(post.id));
const removed = classified.filter((item) => !item.keep);
const previousReport = fs.existsSync(previousReportPath)
  ? JSON.parse(fs.readFileSync(previousReportPath, "utf8"))
  : null;
const previousRemoved = previousReport && Number(previousReport.original_posts) > posts.length
  ? previousReport.removed || []
  : [];
const allRemoved = [...previousRemoved, ...removed].filter((item, index, rows) => rows.findIndex((row) => String(row.post_id) === String(item.post_id)) === index);
const originalPostCount = previousReport && Number(previousReport.original_posts) > posts.length
  ? Number(previousReport.original_posts)
  : posts.length;

const report = {
  generated_at: new Date().toISOString(),
  mode: apply ? "applied" : "dry-run",
  criteria: "シビックテックのイベントへの関連が本文・コメント・イベントリンク・既存イベント記録から確認できる投稿のみ保持",
  original_posts: originalPostCount,
  kept_posts: keptPosts.length,
  removed_posts: allRemoved.length,
  kept: classified.filter((item) => item.keep),
  removed: allRemoved,
};

if (!apply) {
  fs.writeFileSync("/tmp/fb_event_filter_report.json", `${JSON.stringify(report, null, 2)}\n`);
  console.log(JSON.stringify({ original_posts: posts.length, kept_posts: keptPosts.length, removed_posts: removed.length, report: "/tmp/fb_event_filter_report.json" }, null, 2));
  process.exit(0);
}

const exactImagePaths = removed.flatMap((item) => [...item.post_image_paths, ...item.comment_image_paths]);
for (const relativePath of exactImagePaths) {
  const absolutePath = path.resolve(archiveDir, relativePath);
  const expectedRoot = `${path.resolve(archiveDir, "images")}${path.sep}`;
  if (!absolutePath.startsWith(expectedRoot)) throw new Error(`Refusing to delete outside image archive: ${absolutePath}`);
  if (fs.existsSync(absolutePath)) fs.unlinkSync(absolutePath);
}

function filterManifest(fileName, key = "post_id") {
  const filePath = path.join(archiveDir, fileName);
  if (!fs.existsSync(filePath)) return;
  const rows = JSON.parse(fs.readFileSync(filePath, "utf8"));
  const usedPaths = new Set(keptPosts.flatMap((post) => [
    ...post.saved_images,
    ...(post.comments || []).flatMap((comment) => comment.saved_images),
  ]));
  fs.writeFileSync(filePath, `${JSON.stringify(rows.filter((row) => keptIds.has(String(row[key])) || usedPaths.has(row.saved_path)), null, 2)}\n`);
}

fs.writeFileSync(postsPath, `${JSON.stringify(keptPosts, null, 2)}\n`);
filterManifest("images_manifest.json");
filterManifest("comment_images_manifest.json");
fs.writeFileSync(path.join(archiveDir, "event_filter_manifest.json"), `${JSON.stringify(report, null, 2)}\n`);

console.log(JSON.stringify({ original_posts: posts.length, kept_posts: keptPosts.length, removed_posts: removed.length, removed_image_files: exactImagePaths.length }, null, 2));
