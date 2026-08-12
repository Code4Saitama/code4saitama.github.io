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

for (const item of downloads) fs.mkdirSync(path.dirname(path.join(outDir, item.saved_path)), { recursive: true });
const curlRecords = downloads.flatMap((item) => [path.join(outDir, item.saved_path), item.source_url]);
fs.writeFileSync("/tmp/fb_group_image_downloads.nul", `${curlRecords.join("\0")}\0`);

console.log(JSON.stringify({ posts: posts.length, images: downloads.length, first: posts[0]?.date, last: posts.at(-1)?.date }));
