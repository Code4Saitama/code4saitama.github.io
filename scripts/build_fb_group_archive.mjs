import fs from "node:fs";
import path from "node:path";

const sourcePath = "/tmp/fb_crawl_checkpoint.json";
const outDir = path.resolve("fb_group_archive");
const imagesDir = path.join(outDir, "images");

const source = JSON.parse(fs.readFileSync(sourcePath, "utf8"));
const rows = source.rows ?? [];

const parseDate = (value) => {
  const match = String(value ?? "").match(/^(\d{4})年(\d{1,2})月(\d{1,2})日$/);
  if (!match) return null;
  const [, y, m, d] = match;
  return `${y}-${m.padStart(2, "0")}-${d.padStart(2, "0")}`;
};

const posts = rows
  .map((row) => ({
    id: row.id,
    date: parseDate(row.dateText),
    date_display: row.dateText,
    author: row.author,
    url: row.url,
    text: row.text,
    images: row.imgs ?? [],
  }))
  .sort((a, b) => {
    const byDate = String(a.date ?? "9999-99-99").localeCompare(String(b.date ?? "9999-99-99"));
    if (byDate) return byDate;
    return BigInt(a.id) < BigInt(b.id) ? -1 : BigInt(a.id) > BigInt(b.id) ? 1 : 0;
  });

fs.mkdirSync(imagesDir, { recursive: true });

const seenImages = new Map();
const downloads = [];
for (const post of posts) {
  post.saved_images = [];
  for (const [index, image] of post.images.entries()) {
    let relativePath = seenImages.get(image.src);
    if (!relativePath) {
      const date = post.date ?? "unknown-date";
      relativePath = path.posix.join("images", date.slice(0, 4), date, post.id, `${String(index + 1).padStart(2, "0")}.jpg`);
      seenImages.set(image.src, relativePath);
      downloads.push({
        post_id: post.id,
        date: post.date,
        author: post.author,
        alt: image.alt,
        width: image.w,
        height: image.h,
        source_url: image.src,
        saved_path: relativePath,
      });
    }
    post.saved_images.push(relativePath);
  }
}

fs.writeFileSync(path.join(outDir, "posts.json"), `${JSON.stringify(posts, null, 2)}\n`);
fs.writeFileSync(path.join(outDir, "images_manifest.json"), `${JSON.stringify(downloads, null, 2)}\n`);

const csvEscape = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
const csv = [
  ["date", "post_id", "author", "url", "text", "saved_images"].map(csvEscape).join(","),
  ...posts.map((post) => [post.date, post.id, post.author, post.url, post.text, post.saved_images.join(" | ")].map(csvEscape).join(",")),
].join("\n");
fs.writeFileSync(path.join(outDir, "posts.csv"), `${csv}\n`);

const md = [
  "# Facebookグループ投稿アーカイブ",
  "",
  "- グループ: Code for SAITAMA～さいたまのIT×市民活動をわくわくする～",
  "- URL: https://www.facebook.com/groups/186097664924714/",
  `- 投稿数: ${posts.length}`,
  `- 画像数: ${downloads.length}`,
  `- 期間: ${posts[0]?.date ?? "不明"} 〜 ${posts.at(-1)?.date ?? "不明"}`,
  "- 並び順: 古い投稿から",
  "",
  ...posts.flatMap((post, index) => [
    `## ${String(index + 1).padStart(4, "0")} — ${post.date ?? post.date_display} — ${post.author}`,
    "",
    `- 投稿ID: ${post.id}`,
    `- 投稿URL: ${post.url}`,
    "",
    post.text || "（本文なし）",
    "",
    ...post.saved_images.flatMap((imagePath, imageIndex) => [
      `![投稿 ${post.id} の画像 ${imageIndex + 1}](${imagePath})`,
      "",
    ]),
  ]),
].join("\n");
fs.writeFileSync(path.join(outDir, "posts_oldest_first.md"), `${md}\n`);

for (const item of downloads) fs.mkdirSync(path.dirname(path.join(outDir, item.saved_path)), { recursive: true });
const curlRecords = downloads.flatMap((item) => [path.join(outDir, item.saved_path), item.source_url]);
fs.writeFileSync("/tmp/fb_group_image_downloads.nul", `${curlRecords.join("\0")}\0`);

const readme = `# Facebook group archive\n\n` +
  `Facebookグループの投稿を古い順に保存したアーカイブです。\n\n` +
  `- \`posts_oldest_first.md\`: 本文と画像を古い順に閲覧\n` +
  `- \`posts.json\`: 構造化データ\n` +
  `- \`posts.csv\`: 表計算ソフト向け\n` +
  `- \`images_manifest.json\`: 画像の出典URL・投稿ID・保存先\n` +
  `- \`images/\`: 投稿画像\n\n` +
  `取得件数: ${posts.length}件、画像: ${downloads.length}件\n`;
fs.writeFileSync(path.join(outDir, "README.md"), readme);

console.log(JSON.stringify({ posts: posts.length, images: downloads.length, first: posts[0]?.date, last: posts.at(-1)?.date }));
