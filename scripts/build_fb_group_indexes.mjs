import fs from "node:fs";
import path from "node:path";

const repoRoot = path.resolve(import.meta.dirname, "..");
const archiveDir = path.join(repoRoot, "fb_group_archive");
const posts = JSON.parse(fs.readFileSync(path.join(archiveDir, "posts.json"), "utf8"));
const events = JSON.parse(fs.readFileSync(path.join(archiveDir, "group_events.json"), "utf8"));
const postImages = JSON.parse(fs.readFileSync(path.join(archiveDir, "images_manifest.json"), "utf8"));
const commentImages = JSON.parse(fs.readFileSync(path.join(archiveDir, "comment_images_manifest.json"), "utf8"));
const eventImages = JSON.parse(fs.readFileSync(path.join(archiveDir, "event_images_manifest.json"), "utf8"));

const csvEscape = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
const csv = [
  ["date", "post_id", "author", "url", "summary", "text", "comments_summary", "comment_count", "saved_images"].map(csvEscape).join(","),
  ...posts.map((post) => [post.date, post.id, post.author, post.url, post.summary, post.text, post.comments_summary, post.comments.length, post.saved_images.join(" | ")].map(csvEscape).join(",")),
].join("\n");
fs.writeFileSync(path.join(archiveDir, "posts.csv"), `${csv}\n`);

const markdown = [
  "# Facebookグループ投稿アーカイブ",
  "",
  "シビックテックのイベントに関連すると判定した投稿を、古い順に掲載しています。",
  "",
  `- 投稿数: ${posts.length}`,
  `- コメント数: ${posts.reduce((sum, post) => sum + post.comments.length, 0)}`,
  `- 投稿画像数: ${postImages.length}`,
  `- コメント画像数: ${commentImages.length}`,
  `- 期間: ${posts[0]?.date || "不明"} 〜 ${posts.at(-1)?.date || "不明"}`,
  "",
  ...posts.flatMap((post, index) => [
    `## ${String(index + 1).padStart(4, "0")} — ${post.date} — ${post.author}`,
    "",
    `- 投稿ID: ${post.id}`,
    `- 投稿URL: ${post.url}`,
    `- 要約: ${post.summary || "（要約なし）"}`,
    `- コメント要約: ${post.comments_summary || "（コメントなし）"}`,
    "",
    post.text || "（本文なし。コメントからイベント関連性を確認）",
    "",
    ...post.comments.flatMap((comment) => [
      `### コメント — ${comment.author}`,
      "",
      comment.text || "（本文なし）",
      "",
      ...comment.saved_images.flatMap((imagePath, imageIndex) => [`![コメント画像 ${imageIndex + 1}](${imagePath})`, ""]),
    ]),
    ...post.saved_images.flatMap((imagePath, imageIndex) => [`![投稿 ${post.id} の画像 ${imageIndex + 1}](${imagePath})`, ""]),
  ]),
].join("\n");
fs.writeFileSync(path.join(archiveDir, "posts_oldest_first.md"), `${markdown}\n`);

const readme = `# Facebook group archive\n\n` +
  `公開Facebookグループのうち、シビックテックのイベントに関連する投稿とコメント、グループイベントを保存したアーカイブです。\n\n` +
  `- \`posts.json\`: 投稿・要約・コメント・コメント要約\n` +
  `- \`posts.csv\`: 表計算ソフト向け投稿一覧\n` +
  `- \`posts_oldest_first.md\`: 古い順の本文・コメント・画像\n` +
  `- \`group_events.json\`: グループイベント一覧・詳細・要約\n` +
  `- \`*_images_manifest.json\`: 投稿・コメント・イベント画像の出典と保存先\n` +
  `- \`event_filter_manifest.json\`: 保持・除外の判定理由\n` +
  `- \`full_crawl_report.json\`: 取得結果\n\n` +
  `投稿 ${posts.length}件、コメント ${posts.reduce((sum, post) => sum + post.comments.length, 0)}件、` +
  `投稿画像 ${postImages.length}点、コメント画像 ${commentImages.length}点、グループイベント ${events.length}件、イベント画像 ${eventImages.length}点。\n`;
fs.writeFileSync(path.join(archiveDir, "README.md"), readme);

console.log(JSON.stringify({ posts: posts.length, comments: posts.reduce((sum, post) => sum + post.comments.length, 0), postImages: postImages.length, commentImages: commentImages.length, events: events.length, eventImages: eventImages.length }));
