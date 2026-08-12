import fs from "node:fs";
import path from "node:path";

const repoRoot = path.resolve(import.meta.dirname, "..");
const archiveDir = path.join(repoRoot, "fb_group_archive");
const posts = JSON.parse(fs.readFileSync(path.join(archiveDir, "posts.json"), "utf8"));
const events = JSON.parse(fs.readFileSync(path.join(archiveDir, "group_events.json"), "utf8"));
const postImages = JSON.parse(fs.readFileSync(path.join(archiveDir, "images_manifest.json"), "utf8"));
const commentImages = JSON.parse(fs.readFileSync(path.join(archiveDir, "comment_images_manifest.json"), "utf8"));
const eventImages = JSON.parse(fs.readFileSync(path.join(archiveDir, "event_images_manifest.json"), "utf8"));

const readme = `# Facebook group archive\n\n` +
  `公開Facebookグループから取得した記録を、Code for SAITAMAの活動年表・テーマ・関連資料へ統合するための編集用データです。投稿者・コメント投稿者・プロフィールURLなど、活動の理解に不要な個人情報は公開用データから削除しています。\n\n` +
  `- \`public_records.json\`: 年表・テーマ・関連資料に統合する公開用記録\n` +
  `- \`posts.json\`: 匿名化済みの投稿・要約・コメント\n` +
  `- \`group_events.json\`: 匿名化済みのグループイベント情報\n` +
  `- \`*_images_manifest.json\`: 保存画像の識別子と保存先（人物名・元URLは除去）\n` +
  `- \`event_filter_manifest.json\`: レビュー結果の集計\n` +
  `- \`full_crawl_report.json\`: 取得結果\n\n` +
  `投稿・FBイベントの独立した公開ページは設けず、公開用記録は内容に応じて年表・テーマ別・関連資料に表示します。\n\n` +
  `投稿 ${posts.length}件、コメント ${posts.reduce((sum, post) => sum + post.comments.length, 0)}件、` +
  `投稿画像 ${postImages.length}点、コメント画像 ${commentImages.length}点、グループイベント ${events.length}件、イベント画像 ${eventImages.length}点。\n`;
fs.writeFileSync(path.join(archiveDir, "README.md"), readme);

console.log(JSON.stringify({ posts: posts.length, comments: posts.reduce((sum, post) => sum + post.comments.length, 0), postImages: postImages.length, commentImages: commentImages.length, events: events.length, eventImages: eventImages.length }));
