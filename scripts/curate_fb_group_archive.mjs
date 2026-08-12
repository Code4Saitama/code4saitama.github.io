import fs from "node:fs";
import path from "node:path";

const repoRoot = path.resolve(import.meta.dirname, "..");
const archiveDir = path.join(repoRoot, "fb_group_archive");
const postsPath = path.join(archiveDir, "posts.json");
const eventsPath = path.join(archiveDir, "group_events.json");
const contentSourceArgument = process.argv.find((argument) => argument.startsWith("--content-source="));
const eventSourceArgument = process.argv.find((argument) => argument.startsWith("--event-source="));
const posts = JSON.parse(fs.readFileSync(contentSourceArgument ? contentSourceArgument.slice("--content-source=".length) : postsPath, "utf8"));
const groupEvents = JSON.parse(fs.readFileSync(eventSourceArgument ? eventSourceArgument.slice("--event-source=".length) : eventsPath, "utf8"));
const nameSourceArgument = process.argv.find((argument) => argument.startsWith("--name-source="));
const nameSourcePosts = nameSourceArgument
  ? JSON.parse(fs.readFileSync(nameSourceArgument.slice("--name-source=".length), "utf8"))
  : posts;

const organizationPattern = /(Code for|シビックテック|研究会|協議会|大学|学校|自治体|市役所|県庁|委員会|実行委員|NPO|法人|株式会社|新聞|社協|センター|クラブ|プロジェクト|ネットワーク|ラボ|Dojo|訓練)/i;
const exactPersonNames = new Set();
const contextualPersonNames = new Set();
for (const value of nameSourcePosts.flatMap((post) => [post.author, ...(post.comments || []).map((comment) => comment.author)])) {
  for (const candidate of String(value || "").replace(/さん.*/, "").split(/[、,\n]/)) {
    const name = candidate.trim().replace(/^(作成:|投稿者:)/, "").trim();
    const plausibleLength = /^[一-龯々]{2,5}$/.test(name) || (name.length >= 3 && name.length <= 30);
    if (!plausibleLength || organizationPattern.test(name) || /^(参加者|グループ|投稿者不明)/.test(name)) continue;
    if (/^[一-龯々]{2,3}$/.test(name)) contextualPersonNames.add(name);
    else exactPersonNames.add(name);
    if (/^[一-龯々]+[ 　]/.test(name)) contextualPersonNames.add(name.split(/[ 　]+/)[0]);
    else if (/^[一-龯々]{4,5}$/.test(name)) contextualPersonNames.add(name.slice(0, 2));
  }
}
const sharedText = [
  ...nameSourcePosts.flatMap((post) => [post.text, ...(post.comments || []).map((comment) => comment.text)]),
  ...groupEvents.flatMap((event) => [event.description, event.detail_text, event.header_text]),
].join("\n");
for (const match of sharedText.matchAll(/([一-龯々]{2,5}(?:[ 　][一-龯々]{1,5})?|[A-Z][A-Za-z]+(?:[ 　][A-Z][A-Za-z]+){1,2})(?=さんからの投稿をシェア)/g)) {
  if (!organizationPattern.test(match[1])) contextualPersonNames.add(match[1].trim());
}
const commonNonNames = /^(皆さん|各社|会社|記者|主催者|参加者|関係者|担当者|事務局|メンバー|スタッフ|メンター|初心者)$/;
for (const match of sharedText.matchAll(/([一-龯々]{2,5}(?:[ 　][一-龯々]{1,5})?|[A-Z][A-Za-z]+(?:[ 　][A-Z][A-Za-z]+){1,2})(?=(?:さん|先生)(?:から|が|は|の|、|,|\s|\(|（|$))/g)) {
  const name = match[1].trim();
  if (!organizationPattern.test(name) && !commonNonNames.test(name)) contextualPersonNames.add(name);
}
const exactNames = [...exactPersonNames].sort((a, b) => b.length - a.length);
const contextualNames = [...contextualPersonNames].sort((a, b) => b.length - a.length);
const escapeRegex = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

function removePersonalNames(value = "") {
  let result = String(value);
  for (const name of exactNames) {
    result = result.replaceAll(name, "参加者");
    const compactName = name.replace(/\s+/g, "");
    if (compactName.length >= 3) result = result.replaceAll(compactName, "参加者");
  }
  for (const name of contextualNames) {
    const escaped = escapeRegex(name);
    result = result
      .replace(new RegExp(`${escaped}(?:さん|氏|先生|君|です)`, "g"), "参加者")
      .replace(new RegExp(`(^|\\n)${escaped}(?=\\n|$)`, "g"), "$1参加者");
  }
  return result
    .replace(/[一-龯々ぁ-んァ-ヶーA-Za-z・]{2,20}@(?=[一-龯々ぁ-んァ-ヶーA-Za-z])/g, "参加者・")
    .replace(/参加者(?:さん|氏|先生)/g, "参加者")
    .replace(/参加者(?:[ 　、,・-]*参加者)+/g, "参加者");
}

function cleanText(value = "") {
  return removePersonalNames(value)
    .replace(/https?:\/\/\S+/g, "")
    .replace(/[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/g, "")
    .replace(/(?:\+81[- ]?|0)\d{1,4}[- ]?\d{1,4}[- ]?\d{3,4}/g, "")
    .replace(/(?:私は|当方は|初めまして[^。]*|こんにちは[^。]*)[。！!]?/g, "")
    .replace(/(?:ミーティングID|Meeting ID|パスワード|Passcode)[：:]\s*[A-Za-z0-9 -]{3,30}/gi, "")
    .replace(/【招待リンク】/g, "")
    .replace(/詳しくは[^。\n]{0,40}(?:まで|へ)[。！!]?/g, "")
    .replace(/◆自己紹介[\s\S]*?(?=◆|$)/g, "")
    .replaceAll("\u00a0", " ")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line
      && !/^(初めまして|こんにちは|よろしくお願いします|まだコメントはありません|最初のコメントを投稿しよう|写真の説明はありません|返信する|参加予定)/.test(line)
      && !/^(投稿先|グループ|公開|詳細|Facebook利用者以外|· Facebook)/.test(line)
      && !/^(講師|登壇者|出演者|担当者?|連絡先|問い合わせ先|申込先)[：:]/.test(line)
      && !/(さんがシェア|さんからの投稿をシェア|さんと一緒|さんが作成|さんがグループ)/.test(line)
      && !/^参加者、.+のイベント$/.test(line))
    .join("\n")
    .replace(/(?:このコンテンツは現在ご利用いただけません|所有者がシェアする相手を変更した可能性があります)[。\s]*/g, "")
    .replace(/(?:写真の説明はありません[。.\s]*)+/g, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function compact(value = "", limit = 220) {
  const text = cleanText(value).replace(/\s+/g, " ").trim();
  if (!text) return "";
  return text.length <= limit ? text : `${text.slice(0, limit - 1)}…`;
}

function recordSummary(post, linkedEvent) {
  const base = compact(linkedEvent?.description || post.summary || post.text || post.comments_summary, 200);
  const comments = compact(post.comments_summary || (post.comments || []).map((comment) => comment.text).join(" "), 110);
  if (!comments || base.includes(comments.slice(0, 36))) return base;
  return compact(`${base} コメントでは、${comments}`, 300);
}

function themeData(value = "") {
  const rules = [
    ["mapping", "地図・マッピング", /(openstreetmap|\bosm\b|マッピング|地図|\bgis\b|qgis|地理情報)/i],
    ["open-data", "オープンデータ", /(オープンデータ|open\s*data|データ公開|データ活用)/i],
    ["disaster", "防災・災害対応", /(防災|災害|減災|避難|被災|復興|aed)/i],
    ["civic-tech", "アイデアソン・ハッカソン", /(アイデアソン|ハッカソン|シビックテック|civic\s*tech|地域課題|行政サービス)/i],
    ["community", "Meetup・交流", /(code\s*for|ミートアップ|meetup|勉強会|交流会|もくもく|コミュニティ|ワークショップ)/i],
    ["iot", "IoT・プログラミング", /(arduino|\biot\b|プログラミング|アプリ|webサービス)/i],
    ["sdgs", "SDGs・地域課題", /(sdgs|地域課題|まちづくり|市民協働|公民連携)/i],
  ];
  const matched = rules.filter(([, , pattern]) => pattern.test(value));
  if (matched.length === 0) return { themeKeys: ["other"], themes: ["その他"] };
  return { themeKeys: matched.map(([key]) => key), themes: matched.map(([, label]) => label) };
}

const civicPattern = /(code\s*for|シビックテック|civic\s*tech|オープンデータ|open\s*data|openstreetmap|\bosm\b|マッピング|\bgis\b|qgis|\budc\b|アーバンデータ|アイデアソン|ハッカソン|localwiki|データ活用|公民連携|市民協働|行政サービス|自治体)/i;
const directPattern = /(code\s*for\s*saitama|code4saitama|シビックテックさいたま|さいたま.*(?:オープンデータ|マッピング|gis|アイデアソン|ハッカソン)|埼玉.*(?:オープンデータ|マッピング|gis|udc|cog))/i;
const localPlacePattern = /(埼玉|さいたま|大宮|浦和|熊谷|川越|川口|戸田|所沢|越谷|春日部|杉戸|岩槻|鳩山|秩父|和光|草加|上尾|行田)/i;
const referenceCuePattern = /(こんな(?:事例|イベント|試み)|事例を紹介|ニュース|記事|ご紹介|参考まで|シェアします|からの投稿|で行われ|で開催され|他地域|外部イベント|出版|掲載いただ|プレスリリース)/i;
const localActionPattern = /(当グループ|準備会|私たち|企画(?:して|しよう|しました)|開催(?:します|しました|したい)|参加しました|作成しました|公開しました|報告しました|会議メモ|打ち合わせ|次回の会合|振り返り|活動報告|成果発表)/i;

function recordKind(sourceText) {
  if (directPattern.test(sourceText)) return "activity";
  if (localPlacePattern.test(sourceText) && civicPattern.test(sourceText) && !referenceCuePattern.test(sourceText)) return "activity";
  if (civicPattern.test(sourceText) && localActionPattern.test(sourceText) && !referenceCuePattern.test(sourceText)) return "activity";
  return "reference";
}

function frontmatterValue(source, key) {
  const match = source.match(new RegExp(`^${key}:\\s*(.+)$`, "m"));
  if (!match) return undefined;
  try { return JSON.parse(match[1]); } catch { return match[1].replace(/^["']|["']$/g, ""); }
}

const existingEvents = fs.readdirSync(path.join(repoRoot, "src", "content", "events")).filter((file) => file.endsWith(".md")).map((file) => {
  const source = fs.readFileSync(path.join(repoRoot, "src", "content", "events", file), "utf8");
  return {
    title: frontmatterValue(source, "title") || "",
    date: String(frontmatterValue(source, "date") || "").replaceAll(".", "-"),
    page: frontmatterValue(source, "page") || "",
    fbid: String(frontmatterValue(source, "fbid") || ""),
    groupEventId: String(frontmatterValue(source, "groupEventId") || ""),
    groupPostIds: (frontmatterValue(source, "groupPostIds") || []).map(String),
  };
});
const existingPostIds = new Set(existingEvents.flatMap((event) => event.groupPostIds));
const existingEventIds = new Set(existingEvents.flatMap((event) => [event.fbid, event.groupEventId]).filter(Boolean));
const groupEventById = new Map(groupEvents.map((event) => [String(event.event_id), event]));

function titleFrom(text, themes) {
  const cleaned = cleanText(text);
  if (/このグループ.*(?:Code for SAITAMA|Code for Saitama)/i.test(cleaned)) return "Code for SAITAMA公開グループの発足";
  if (/次回の会合/.test(cleaned)) return "Code for SAITAMA準備会の開催調整";
  if (/2013年.*オープンデータ.*本格的/.test(cleaned)) return "埼玉でのオープンデータ活動を考える";
  if (/ワークショップデザイン.*ファシリテーター/.test(cleaned)) return "アイデアソン運営に向けた知見共有";
  const candidates = cleaned.split(/[。！？!?\n]/).map((item) => item.trim()).filter((item) => item.length >= 8);
  const first = candidates.find((item) => /(開催|企画|報告|記録|勉強会|ミートアップ|マッピング|アイデアソン|ハッカソン|オープンデータ|gis|osm)/i.test(item)) || candidates[0] || "";
  const editorial = first
    .replace(/^(?:昨日の|本日の|先日の|昨日|本日|先日|いよいよ|改めて|ご紹介|シェアします|こんな事例もあります)[、。：: ]*/, "")
    .replace(/(?:ご参加|ご覧)ください.*$/, "")
    .trim();
  if (editorial.length >= 8) return editorial.length <= 84 ? editorial : `${editorial.slice(0, 83)}…`;
  return `${themes[0] || "シビックテック"}に関する活動記録`;
}

const records = [];
const representedEventIds = new Set();
const recordByEventId = new Map();
for (const post of posts) {
  if (existingPostIds.has(String(post.id))) continue;
  const eventId = String(post.fb_event_links?.[0]?.event_id || "");
  if (eventId && existingEventIds.has(eventId)) continue;
  const linkedEvent = eventId ? groupEventById.get(eventId) : null;
  const sourceText = [linkedEvent?.title, linkedEvent?.description, post.text, post.comments_summary].filter(Boolean).join("\n");
  const { themeKeys, themes } = themeData(sourceText);
  const summary = recordSummary(post, linkedEvent);
  const eventTitle = linkedEvent?.title && !/^https?:/.test(linkedEvent.title) ? linkedEvent.title : "";
  const images = [...new Set([
    ...(linkedEvent?.saved_images || []),
    ...(post.saved_images || []),
    ...(post.comments || []).flatMap((comment) => comment.saved_images || []),
  ])];
  if (eventId && recordByEventId.has(eventId)) {
    const record = recordByEventId.get(eventId);
    const additionalSummary = recordSummary(post, null);
    if (additionalSummary && !record.summary.includes(additionalSummary.slice(0, 48))) {
      record.summary = compact(`${record.summary} ${additionalSummary}`, 520);
    }
    record.images = [...new Set([...record.images, ...images])];
    record.image = record.images[0] || "";
    record.commentCount += (post.comments || []).length;
    record.sourceCount += 1;
    record.themeKeys = [...new Set([...record.themeKeys, ...themeKeys])];
    record.themes = [...new Set([...record.themes, ...themes])];
    if (recordKind(sourceText) === "activity") record.kind = "activity";
    continue;
  }
  records.push({
    id: eventId ? `fb-event-${eventId}` : `fb-post-${post.id}`,
    date: linkedEvent?.date || post.date,
    sort: Date.parse(`${linkedEvent?.date || post.date}T00:00:00+09:00`) / 1000,
    title: cleanText(eventTitle || titleFrom(post.text || post.comments_summary, themes)) || `${themes[0] || "シビックテック"}に関する活動記録`,
    summary,
    kind: recordKind(sourceText),
    themeKeys,
    themes,
    sources: ["facebook-group"],
    image: images[0] || "",
    images,
    commentCount: (post.comments || []).length,
    sourceTypes: linkedEvent ? ["event", "post"] : ["post"],
    sourceCount: linkedEvent ? 2 : 1,
  });
  if (eventId) {
    representedEventIds.add(eventId);
    recordByEventId.set(eventId, records.at(-1));
  }
}

for (const event of groupEvents) {
  const eventId = String(event.event_id);
  if (existingEventIds.has(eventId) || representedEventIds.has(eventId)) continue;
  const sourceText = [event.title, event.description, event.detail_text].join("\n");
  const { themeKeys, themes } = themeData(sourceText);
  const images = [...new Set(event.saved_images || [])];
  records.push({
    id: `fb-event-${eventId}`,
    date: event.date || "",
    sort: event.date ? Date.parse(`${event.date}T00:00:00+09:00`) / 1000 : Number.MAX_SAFE_INTEGER,
    title: cleanText(event.title) || "Facebookグループで共有されたイベント",
    summary: compact(event.description || event.detail_text || event.title),
    kind: recordKind(sourceText),
    themeKeys,
    themes,
    sources: ["facebook-group"],
    image: images[0] || "",
    images,
    commentCount: 0,
    sourceTypes: ["event"],
    sourceCount: 1,
  });
}

records.sort((a, b) => a.sort - b.sort || a.title.localeCompare(b.title, "ja"));
fs.writeFileSync(path.join(archiveDir, "public_records.json"), `${JSON.stringify(records, null, 2)}\n`);

for (const post of posts) {
  post.author = "グループ参加者";
  post.url = "";
  post.text = cleanText(post.text);
  post.summary = compact(post.text, 180);
  post.comments_summary = compact((post.comments || []).map((comment) => comment.text).join(" "), 240);
  post.images = [];
  for (const comment of post.comments || []) {
    comment.author = "グループ参加者";
    comment.permalink = "";
    comment.text = cleanText(comment.text);
    comment.summary = compact(comment.text, 140);
    comment.images = [];
  }
}

for (const event of groupEvents) {
  event.description = cleanText(event.description);
  event.summary = compact(event.description || event.detail_text, 220);
  event.detail_text = cleanText(event.detail_text);
  event.header_text = cleanText(event.header_text);
  event.images = [];
}
fs.writeFileSync(postsPath, `${JSON.stringify(posts, null, 2)}\n`);
fs.writeFileSync(eventsPath, `${JSON.stringify(groupEvents, null, 2)}\n`);

for (const file of ["images_manifest.json", "comment_images_manifest.json", "event_images_manifest.json"]) {
  const manifestPath = path.join(archiveDir, file);
  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8")).map((item) => {
    const { author, source_url, photo_url, ...publicItem } = item;
    if (publicItem.alt) publicItem.alt = cleanText(publicItem.alt);
    return publicItem;
  });
  fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
}

const filterPath = path.join(archiveDir, "event_filter_manifest.json");
const filter = JSON.parse(fs.readFileSync(filterPath, "utf8"));
const reasonCounts = Object.entries((filter.removed || []).reduce((counts, item) => ({ ...counts, [item.reason]: (counts[item.reason] || 0) + 1 }), {})).map(([reason, count]) => ({ reason, count }));
fs.writeFileSync(filterPath, `${JSON.stringify({ generated_at: filter.generated_at, criteria: filter.criteria, original_posts: filter.original_posts, kept_posts: filter.kept_posts, removed_posts: filter.removed_posts, removal_reason_counts: reasonCounts }, null, 2)}\n`);

console.log(JSON.stringify({ records: records.length, activity: records.filter((record) => record.kind === "activity").length, reference: records.filter((record) => record.kind === "reference").length, redactedNames: exactNames.length + contextualNames.length }));
