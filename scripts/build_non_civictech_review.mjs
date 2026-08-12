import fs from "node:fs";
import path from "node:path";

const archiveDir = path.resolve("fb_group_archive");
const posts = JSON.parse(fs.readFileSync(path.join(archiveDir, "posts.json"), "utf8"));

const systemPost = /(?:グループ|プライバシー設定|管理者|タグ|カバー写真|ドキュメント|イベント).*(?:作成|変更|指定|編集|追加|削除)/;
const publicContext = /介護|社会問題|社会課題|防犯|埼玉県警|県庁|見守り|地域|公共|自治体|行政|市民|福祉|教育|災害|防災/i;
const civicContext = /シビック|civic|code for|オープン.?データ|open.?data|市民|行政|自治体|市役所|県庁|公共|地域課題|社会課題|まちづくり|街づくり|地域活性|地域コミュニティ|防災|災害|避難|減災|NPO|非営利|ボランティア|市民活動|ハッカソン|アイデアソン|マッピング|GIS|OpenStreetMap|LocalWiki|福祉|介護|子ども|教育|交通|環境|観光|選挙|議会|政策|オープンソース|データ活用/i;
const commercialContext = /チャンネル登録|車検|鈑金|保険付き|結婚式|住宅メーカー|レンタル|弊社|当社|採用|求人|ブログ更新|商品|販売|購入|キャンペーン|集客|販促|広告|展示会|パーティ/i;

const explicitHigh = new Map([
  ["253212251546588", "アイス商品のマーケティング記事の共有で、シビックテックとの接点が見当たらない"],
  ["1707362069464925", "自動車販売・整備サービスの宣伝で、地域課題や市民参加との接点が見当たらない"],
  ["1773299519537846", "個人紹介記事の共有で、シビックテックとの接点が見当たらない"],
  ["1779582518909546", "グループの主題と関係しない国際会議・運動の告知とみられる"],
  ["490694657798345", "焼酎商品の公式ページ共有で、本文にシビックテック文脈がない"],
]);

const explicitCivic = new Set([
  "1789626091238522", // ごみ削減活動を可視化する「さいたまごみゼロ365」
]);

const explicitReview = new Map([
  ["529672683900542", "WordPress書籍の販売告知。地域IT人材との関連はあるが、市民課題解決が主題か要確認"],
  ["591444651056678", "起業家育成プログラムの募集。社会課題領域を含むが、グループとの直接的関連は要確認"],
  ["761087960759012", "起業家育成プログラムの募集。社会課題領域を含むが、グループとの直接的関連は要確認"],
  ["1272939142907222", "地域連携研究から生まれた清酒の販売告知。地域活動として残すか要確認"],
  ["1962477060620090", "大学研究・農福連携に由来する商品の販売告知。公共的背景を含むため要確認"],
]);

const candidates = [];

for (const post of posts) {
  if (explicitCivic.has(post.id)) continue;

  const text = post.text.trim();
  let confidence = null;
  let reason = null;
  let category = null;

  if (explicitHigh.has(post.id)) {
    confidence = "high";
    category = "明確な宣伝・スパム";
    reason = explicitHigh.get(post.id);
  } else if (explicitReview.has(post.id)) {
    confidence = "review";
    category = "商業・募集告知";
    reason = explicitReview.get(post.id);
  } else if (post.author.includes("Seikaku Robo PRteam")) {
    category = "企業製品PR";
    if (text.length < 30) {
      confidence = "review";
      reason = "本文を取得できていないが、継続的な企業製品PR投稿群に属するため内容確認が必要";
    } else if (publicContext.test(text)) {
      confidence = "review";
      reason = "Pepper／ロボット事業のPRだが、公共・福祉・防犯などの文脈を含むため要確認";
    } else {
      confidence = "high";
      reason = "Pepper／ロボット製品・レンタル事例の企業PRで、市民参加や公共課題解決が主題ではない";
    }
  } else if (!text && !systemPost.test(post.author)) {
    confidence = "unresolved";
    category = "本文未取得";
    reason = "本文が保存されていないため自動判定不可。画像とFacebook投稿を開いて確認が必要";
  } else if (commercialContext.test(text) && !civicContext.test(text)) {
    confidence = "review";
    category = "商業・募集告知";
    reason = "商業・採用・販売の表現があり、シビックテックを示す語が見当たらないため要確認";
  }

  if (!confidence) continue;

  candidates.push({
    delete: false,
    confidence,
    category,
    reason,
    date: post.date,
    id: post.id,
    author: post.author,
    url: post.url,
    text: post.text,
    excerpt: post.text.replace(/\s+/g, " ").trim().slice(0, 500),
    image_count: post.saved_images.length,
    image_paths: post.saved_images,
  });
}

const confidenceOrder = { high: 0, review: 1, unresolved: 2 };
candidates.sort((a, b) => confidenceOrder[a.confidence] - confidenceOrder[b.confidence] || a.date.localeCompare(b.date) || a.id.localeCompare(b.id));

fs.writeFileSync(path.join(archiveDir, "non_civictech_candidates.json"), `${JSON.stringify(candidates, null, 2)}\n`);

const csvEscape = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
const csv = [
  ["delete", "confidence", "category", "date", "post_id", "author", "reason", "excerpt", "post_url", "image_count", "image_paths"].map(csvEscape).join(","),
  ...candidates.map((item) => ["", item.confidence, item.category, item.date, item.id, item.author, item.reason, item.excerpt, item.url, item.image_count, item.image_paths.join(" | ")].map(csvEscape).join(",")),
].join("\n");
fs.writeFileSync(path.join(archiveDir, "non_civictech_review.csv"), `${csv}\n`);

const labels = { high: "削除候補（高確度）", review: "要確認", unresolved: "判定不能（本文未取得）" };
const markdown = [
  "# シビックテック非関連投稿の確認リスト",
  "",
  "チェックは削除の最終判断用です。このファイルを編集する場合、削除する投稿だけ `[x]` にしてください。",
  "",
  ...Object.keys(labels).flatMap((confidence) => [
    `## ${labels[confidence]}`,
    "",
    ...candidates.filter((item) => item.confidence === confidence).flatMap((item) => [
      `- [ ] ${item.date} — ${item.author} — ${item.category}`,
      `  - 投稿ID: ${item.id}`,
      `  - 理由: ${item.reason}`,
      `  - 投稿URL: ${item.url}`,
      `  - 画像 (${item.image_count}): ${item.image_paths.join(", ") || "なし"}`,
      `  - 抜粋: ${item.excerpt || "（本文なし）"}`,
      "",
    ]),
  ]),
].join("\n");
fs.writeFileSync(path.join(archiveDir, "non_civictech_review.md"), `${markdown}\n`);

const counts = Object.fromEntries(Object.keys(labels).map((key) => [key, candidates.filter((item) => item.confidence === key).length]));
const embedded = JSON.stringify(candidates).replaceAll("<", "\\u003c");
const html = `<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>シビックテック非関連投稿レビュー</title>
<style>
:root{color-scheme:light dark;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;--bg:#f5f6f8;--panel:#fff;--text:#1d2433;--muted:#657086;--border:#d9deea;--accent:#1769aa;--high:#b42318;--review:#9a6700;--unresolved:#536273}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text)}header{position:sticky;top:0;z-index:2;background:color-mix(in srgb,var(--panel) 94%,transparent);border-bottom:1px solid var(--border);padding:16px}.wrap{max-width:1180px;margin:auto}.summary,.controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.summary{margin:10px 0}.pill{border:1px solid var(--border);border-radius:999px;padding:5px 10px;font-size:14px}.controls input,.controls select,.controls button{font:inherit;padding:8px 10px;border:1px solid var(--border);border-radius:7px;background:var(--panel);color:var(--text)}.controls input{min-width:280px;flex:1}.controls button{cursor:pointer}.controls .primary{background:var(--accent);color:#fff;border-color:var(--accent)}main{max-width:1180px;margin:18px auto;padding:0 16px}.item{background:var(--panel);border:1px solid var(--border);border-left:5px solid var(--unresolved);border-radius:9px;padding:14px;margin:12px 0}.item.high{border-left-color:var(--high)}.item.review{border-left-color:var(--review)}.item-head{display:flex;gap:10px;align-items:flex-start}.item-head input{width:20px;height:20px;margin-top:2px}.meta{display:flex;gap:8px;flex-wrap:wrap;color:var(--muted);font-size:14px}.badge{border:1px solid currentColor;border-radius:999px;padding:2px 8px}.reason{margin:9px 0}.excerpt{white-space:pre-wrap;overflow-wrap:anywhere;color:var(--muted)}.images{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px;margin-top:10px}.images img{width:100%;height:150px;object-fit:contain;background:#1111;border-radius:6px}.paths{font:12px ui-monospace,SFMono-Regular,monospace;overflow-wrap:anywhere;color:var(--muted)}details{margin-top:8px}a{color:var(--accent)}.hidden{display:none!important}@media(prefers-color-scheme:dark){:root{--bg:#101318;--panel:#171b22;--text:#edf1f7;--muted:#aab3c3;--border:#343b48;--accent:#79b8ef;--high:#ff8a80;--review:#ffd166;--unresolved:#aab3c3}}@media(max-width:560px){header{position:static}.controls input{min-width:100%}.images{grid-template-columns:repeat(2,1fr)}}
</style>
</head>
<body>
<header><div class="wrap"><strong>シビックテック非関連投稿レビュー</strong><div class="summary"><span class="pill">高確度 ${counts.high}</span><span class="pill">要確認 ${counts.review}</span><span class="pill">判定不能 ${counts.unresolved}</span><span class="pill">選択 <b id="selectedCount">0</b></span></div><div class="controls"><input id="search" type="search" placeholder="投稿者・本文・ID・理由を検索"><select id="filter"><option value="all">全候補</option><option value="high">高確度</option><option value="review">要確認</option><option value="unresolved">判定不能</option><option value="selected">チェック済みのみ</option></select><button id="export" class="primary">選択結果をJSON保存</button><button id="copy">画像パスをコピー</button><button id="clear">チェック解除</button></div></div></header>
<main id="list"></main>
<script>
const candidates=${embedded};
const storageKey="code4saitama-non-civictech-review-v1";
function loadSelected(){try{return new Set(JSON.parse(localStorage.getItem(storageKey)||"[]"))}catch{return new Set()}}
const selected=loadSelected();
const list=document.getElementById("list"), search=document.getElementById("search"), filter=document.getElementById("filter"), selectedCount=document.getElementById("selectedCount");
const label={high:"削除候補・高確度",review:"要確認",unresolved:"判定不能"};
function save(){try{localStorage.setItem(storageKey,JSON.stringify([...selected]))}catch{}selectedCount.textContent=selected.size}
async function copyText(value){if(navigator.clipboard?.writeText){await navigator.clipboard.writeText(value);return}const area=document.createElement("textarea");area.value=value;area.style.position="fixed";area.style.opacity="0";document.body.append(area);area.select();document.execCommand("copy");area.remove()}
function render(){const q=search.value.trim().toLowerCase(),f=filter.value;list.textContent="";for(const item of candidates){const hay=[item.id,item.author,item.reason,item.text,item.category].join(" ").toLowerCase();if(q&&!hay.includes(q))continue;if(f!=="all"&&f!=="selected"&&item.confidence!==f)continue;if(f==="selected"&&!selected.has(item.id))continue;const article=document.createElement("article");article.className="item "+item.confidence;const head=document.createElement("div");head.className="item-head";const check=document.createElement("input");check.type="checkbox";check.checked=selected.has(item.id);check.setAttribute("aria-label","投稿 "+item.id+" を削除対象として選択");check.addEventListener("change",()=>{check.checked?selected.add(item.id):selected.delete(item.id);save();if(filter.value==="selected")render()});const body=document.createElement("div");body.style.flex="1";const title=document.createElement("div");const link=document.createElement("a");link.href=item.url;link.target="_blank";link.rel="noopener";link.textContent=item.date+" — "+item.author;title.append(link);const meta=document.createElement("div");meta.className="meta";meta.innerHTML='<span class="badge">'+label[item.confidence]+"</span><span>"+item.category+"</span><span>ID: "+item.id+"</span><span>画像: "+item.image_count+"</span>";const reason=document.createElement("div");reason.className="reason";reason.textContent=item.reason;const excerpt=document.createElement("div");excerpt.className="excerpt";excerpt.textContent=item.excerpt||"（本文なし）";body.append(title,meta,reason,excerpt);if(item.image_paths.length){const images=document.createElement("div");images.className="images";for(const [index,p] of item.image_paths.entries()){const a=document.createElement("a");a.href=p;a.target="_blank";const img=document.createElement("img");img.src=p;img.loading="lazy";img.alt="投稿 "+item.id+" の画像 "+(index+1);a.append(img);images.append(a)}body.append(images);const paths=document.createElement("details");paths.innerHTML='<summary>画像パス</summary><div class="paths"></div>';paths.querySelector("div").textContent=item.image_paths.join("\\n");body.append(paths)}if(item.text){const details=document.createElement("details");const summary=document.createElement("summary");summary.textContent="保存された本文全文";const pre=document.createElement("pre");pre.className="excerpt";pre.textContent=item.text;details.append(summary,pre);body.append(details)}head.append(check,body);article.append(head);list.append(article)}save()}
search.addEventListener("input",render);filter.addEventListener("change",render);
document.getElementById("export").addEventListener("click",()=>{const chosen=candidates.filter(x=>selected.has(x.id));const payload={created_at:new Date().toISOString(),group_id:"186097664924714",selected_count:chosen.length,posts:chosen.map(x=>({post_id:x.id,date:x.date,author:x.author,url:x.url,image_paths:x.image_paths,reason:x.reason}))};const blob=new Blob([JSON.stringify(payload,null,2)],{type:"application/json"});const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="facebook-posts-selected-for-deletion.json";a.click();URL.revokeObjectURL(a.href)});
document.getElementById("copy").addEventListener("click",async()=>{const paths=candidates.filter(x=>selected.has(x.id)).flatMap(x=>x.image_paths);await copyText(paths.join("\\n"));alert(paths.length+"件の画像パスをコピーしました")});
document.getElementById("clear").addEventListener("click",()=>{if(confirm("すべてのチェックを解除しますか？")){selected.clear();save();render()}});
render();
</script>
</body>
</html>`;
fs.writeFileSync(path.join(archiveDir, "non_civictech_review.html"), html);

console.log(JSON.stringify({ total: candidates.length, ...counts }));
