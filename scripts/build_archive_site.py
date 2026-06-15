#!/usr/bin/env python3
import datetime as dt
import html
import json
import pathlib
import re
from collections import Counter, defaultdict


ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "facebook-export"
DOCS = ROOT / "docs"
SITE = ROOT / "archive-site"
SITE_IMAGE_DIR = ROOT / "public" / "assets" / "images"


SUPPLEMENTAL_TIMELINE = [
    {
        "date": "2014.01",
        "sort": dt.datetime(2014, 1, 1).timestamp(),
        "title": "Code for SAITAMA発足",
        "theme": "団体史",
        "text": "補足レポートでは、Code for SAITAMAは2014年1月に発足した、埼玉県全域を活動範囲とするシビックテック団体として整理されています。",
    },
    {
        "date": "2014.11",
        "sort": dt.datetime(2014, 11, 1).timestamp(),
        "title": "Qiitaアドベントカレンダー「Code for SAITAMAのこれまで」",
        "theme": "外部記事・記録",
        "text": "初期のコミュニティ形成や活動の試行錯誤を整理した外部記事として、関連資料に記録されています。本文情報は継続して確認します。",
    },
    {
        "date": "2016.10.18",
        "sort": dt.datetime(2016, 10, 18).timestamp(),
        "title": "レジリナイト関連資料",
        "theme": "登壇資料・防災",
        "text": "災害時の地域レジリエンス向上に関する資料公開が補足レポートで挙げられています。防災と地理情報をつなぐ活動の外部記録として扱います。",
    },
    {
        "date": "2016.11",
        "sort": dt.datetime(2016, 11, 1).timestamp(),
        "title": "Code for Japan Summit 2016への参加",
        "theme": "外部イベント・登壇",
        "text": "Code for Japan Summit 2016およびOSMカンファレンス文脈で、uMapを用いたマッピングデータの可視化が補足レポートに記録されています。",
    },
    {
        "date": "2017.06.25",
        "sort": dt.datetime(2017, 6, 25).timestamp(),
        "title": "Code for Kumagaya 観光を考えるアイデアソン",
        "theme": "他コミュニティ交流",
        "text": "熊谷市観光協会やNPO支援センターと連携した観光資源のデジタル化活動として、補足レポートに記載されています。",
    },
    {
        "date": "2017.08.06",
        "sort": dt.datetime(2017, 8, 6).timestamp(),
        "title": "Code for Kusatsu 真夏のマッピングパーティー支援",
        "theme": "他コミュニティ交流",
        "text": "滋賀県草津市でのマッピング活動を現地支援した事例として補足レポートに挙げられています。県外コミュニティとの交流記録です。",
    },
    {
        "date": "2017.09.23",
        "sort": dt.datetime(2017, 9, 23).timestamp(),
        "title": "シビックパワーバトル2017",
        "theme": "外部イベント・オープンデータ",
        "text": "オープンデータを活用し、市民が地域の魅力を競うプレゼン大会として補足レポートに記載されています。",
    },
    {
        "date": "2017.12.09",
        "sort": dt.datetime(2017, 12, 9).timestamp(),
        "title": "GISキャンプ2017 / ブラトヨハシ関連",
        "theme": "他コミュニティ交流・GIS",
        "text": "Code for GIFUや愛知大学などとの文脈で、Wikipedia編集とOSMマッピングを組み合わせた活動への参加が補足レポートに記録されています。",
    },
    {
        "date": "2018.01.08",
        "sort": dt.datetime(2018, 1, 8).timestamp(),
        "title": "本庄中山道マッピングパーティー",
        "theme": "他コミュニティ交流・マッピング",
        "text": "Code for Kumagayaとの連携で、本庄中山道周辺の蔵めぐりとOSM・LocalWiki編集を行った活動として補足レポートに挙げられています。",
    },
    {
        "date": "2018.02.12",
        "sort": dt.datetime(2018, 2, 12).timestamp(),
        "title": "e-Todaオープンデータ・アイデアソン / ハッカソン",
        "theme": "他コミュニティ交流・オープンデータ",
        "text": "戸田市、JIPDEC、Code for TODAなどとの行政課題解決に向けた活動として、補足レポートに記載されています。",
    },
    {
        "date": "2018.06.02",
        "sort": dt.datetime(2018, 6, 2).timestamp(),
        "title": "CIVIC TECH FORUM 2018登壇",
        "theme": "登壇・活動報告",
        "text": "共同代表による「埼玉での活動を通して得たもの」の成果報告として、関連資料に記録されています。外部登壇資料として継続して整理します。",
    },
    {
        "date": "2021",
        "sort": dt.datetime(2021, 1, 1).timestamp(),
        "title": "AI災害早期検知に関する研究発表",
        "theme": "研究発表・防災",
        "text": "5mDEMや点群データ、機械学習を用いた被災総額早期検知の研究発表として補足レポートに記載されています。学術資料の確認後に詳細化します。",
    },
]


EVENT_PAGE_SLUGS = {
    1: "hack-for-criterium",
    2: "urawa-mapping-party-canceled",
    3: "d3js-study-meetup",
    4: "urawa-disaster-mapping-party",
    5: "open-data-ideathon",
    6: "open-data-hackathon",
    7: "open-data-day-mokumoku-2015",
    8: "kawagoe-hanami-mapping-portal-hackathon",
    9: "arduino-workshop-beginner",
    10: "arduino-workshop-02",
    11: "omiya-bonsai-mapping-localwiki-osm",
    12: "arduino-workshop-03",
    13: "open-data-ideathon-2015-saitama",
    14: "open-data-hackathon-2015-saitama",
    15: "arduino-workshop-04",
    16: "mapping-party-2015-iwatsuki",
    17: "ikebukuro-mapping-party-code-for-toshima",
    18: "open-data-ideathon-2015-02",
    19: "open-data-hackathon-2015-02",
    20: "open-data-day-2016-saitama",
    21: "kumagaya-hanami-mapping-party",
    22: "beer-mapping-party-keyaki-hiroba",
    23: "thematic-map-open-data-workshop",
    24: "tsukutama-openstreetmap-workshop",
    25: "thematic-map-open-data-hackathon",
    26: "iot-mokumoku-adult-summer-project",
    27: "issue-solving-night-01",
    28: "urban-data-challenge-2016-saitama",
    29: "map-study-new-year",
    30: "urban-data-challenge-prep-mokumoku",
    31: "map-study-02",
    32: "open-data-day-2017-saitama",
    33: "map-study-03",
    34: "programming-electronics-class",
    35: "toda-hanami-mapping-party-2017",
    36: "map-study-04",
    37: "map-study-05-urawa",
    38: "kumagaya-tourism-pre-ideathon-hackathon",
    39: "map-study-06-urawa",
    40: "kumagaya-tourism-ideathon-hackathon",
    41: "map-study-07-gis-mokumoku",
    42: "wheelchair-mapping-party",
    43: "iwatsuki-hanami-mapping-party",
    44: "suisui-kai",
    45: "code-for-saitama-meetup-2020-01",
    46: "code-for-saitama-meetup-2020-02",
    47: "open-data-day-2020-saitama-besshonuma",
    48: "online-hanami-mapping-party-2020",
    49: "code-for-saitama-meetup-2020-05",
    50: "code-for-saitama-meetup-2020-06",
    51: "sdgs-ideathon-hare-to-ke",
    52: "sdgs-hackathon-hare-to-ke",
    53: "code-for-japan-summit-2020-kanto-meetup",
    54: "code-for-saitama-meetup-2020-12-udc",
    55: "open-data-day-2021-saitama-online",
    56: "cog2021-kumagaya-meetup",
    57: "udc2021-saitama-meetup-code-for-saitama",
    58: "cog2021-kumagaya-meetup-vol-2",
    59: "udc2021-saitama-meetup-02",
    60: "cog2022-kumagaya-kickoff-udc2022",
    61: "noto-earthquake-osm-mokumoku",
}


def fix_text(value):
    if isinstance(value, str):
        try:
            return value.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return value
    if isinstance(value, list):
        return [fix_text(item) for item in value]
    if isinstance(value, dict):
        return {fix_text(k): fix_text(v) for k, v in value.items()}
    return value


def load_json(relative_path):
    with (DATA / relative_path).open(encoding="utf-8") as f:
        return fix_text(json.load(f))


def ts(value, date=False):
    if not value:
        return ""
    try:
        return dt.datetime.fromtimestamp(value).strftime("%Y.%m.%d" if date else "%Y.%m.%d %H:%M")
    except (TypeError, ValueError, OSError):
        return ""


def iso_date(value):
    if not value:
        return ""
    try:
        return dt.datetime.fromtimestamp(value).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OSError):
        return ""


def clean(value):
    return re.sub(r"\n{3,}", "\n\n", str(value or "").replace("\r\n", "\n")).strip()


def excerpt(value, limit=150):
    value = re.sub(r"\s+", " ", clean(value))
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def h(value):
    return html.escape(str(value or ""), quote=True)


def detail_page_name(idx, event):
    date = iso_date(event.get("start_timestamp")) or f"event-{idx:03d}"
    page_slug = EVENT_PAGE_SLUGS.get(idx, "event")
    page_slug = re.sub(r"[^a-z0-9-]+", "-", page_slug.lower()).strip("-") or "event"
    return f"event-{date}-{page_slug}.html"


def site_image(path):
    if not path:
        return ""
    return path


def verified_image_html(path, alt="", class_name=""):
    if not path:
        cls = f" {class_name}" if class_name else ""
        logo = "assets/images/webp/cfs-image-0051.webp"
        return f'<div class="verified-placeholder{cls}"><img src="{logo}" alt="Code for SAITAMA" loading="lazy" /></div>'
    cls = f' class="{class_name}"' if class_name else ""
    return f'<img{cls} src="{site_image(path)}" alt="{h(alt)}" loading="lazy" />'


def theme_for(name, description):
    text = f"{name}\n{description}"
    rules = [
        ("mapping", "地図・マッピング", ["OpenStreetMap", "OSM", "マッピング", "地図", "主題図"]),
        ("open-data", "オープンデータ", ["オープンデータ", "UDC", "アーバンデータ", "COG", "オープンガバナンス"]),
        ("civic-tech", "アイデアソン・ハッカソン", ["アイデアソン", "アイディアソン", "ハッカソン", "hackathon"]),
        ("disaster", "防災・災害対応", ["防災", "災害", "ハザード", "能登半島地震", "クライシス"]),
        ("community", "Meetup・交流", ["Meetup", "ミートアップ", "交流", "もくもく", "勉強会"]),
        ("iot", "IoT・電子工作", ["Arduino", "IoT", "電子工作", "アルディーノ"]),
        ("sdgs", "SDGs・地域課題", ["SDGs", "SDGｓ", "観光", "子ども", "農産物", "暑さ", "スポーツ"]),
    ]
    hits = [(key, label) for key, label, words in rules if any(word in text for word in words)]
    return hits or [("other", "その他")]


def place_text(place):
    if not place:
        return ""
    if isinstance(place, str):
        return place
    name = place.get("name", "")
    address = place.get("address", "")
    if name and address:
        return f"{name} / {address}"
    return name or address


def load_image_manifest():
    data = json.load(open(SITE_IMAGE_DIR / "images-manifest.json", encoding="utf-8"))
    by_title = defaultdict(list)
    by_type = defaultdict(list)
    by_id = {}
    for row in data:
        by_id[row["asset_id"]] = row
        if row.get("source_title"):
            by_title[row["source_title"]].append(row)
        by_type[row.get("source_type", "")].append(row)
    return data, by_title, by_type, by_id


def representative_image(title, images, by_title, fallback_index=0):
    candidates = []
    if title in by_title:
        candidates.extend(by_title[title])
    for key, rows in by_title.items():
        if title and (title in key or key in title):
            candidates.extend(rows)
    keywords = [word for word in re.split(r"[\s　/・、。:：()（）【】\[\]~〜-]+", title or "") if len(word) >= 3]
    if keywords:
        scored = []
        for row in images:
            haystack = f"{row.get('source_title', '')} {row.get('description', '')}"
            score = sum(1 for word in keywords if word in haystack)
            if score:
                scored.append((score, row))
        if scored:
            candidates.extend(row for _, row in sorted(scored, key=lambda item: item[0], reverse=True))
    if candidates:
        return candidates[0]["webp_asset_path"]
    if images:
        return images[fallback_index % len(images)]["webp_asset_path"]
    return ""


def prefer_group_photo(rows):
    group_words = ("集合写真", "記念撮影", "記念写真")
    for row in rows:
        text = f"{row.get('description', '')} {row.get('source_title', '')}"
        if any(word in text for word in group_words):
            return row
    return rows[0] if rows else None


def build_data():
    image_manifest, by_title, by_type, by_id = load_image_manifest()
    hosted = load_json("this_profile's_activity_across_facebook/events/events_you_hosted.json")
    hosted_by_title = {item.get("title"): item for item in hosted}
    events_raw = load_json("this_profile's_activity_across_facebook/events/events.json").get("your_events_v2", [])

    def curated_asset_ids(name, date):
        rules = [
            (lambda n, d: d == "2014.10.18", ["cfs-image-0169"]),
            (lambda n, d: d == "2015.01.16", [f"cfs-image-{i:04d}" for i in range(1, 24)] + ["cfs-image-0171"]),
            (lambda n, d: d == "2015.01.31", [f"cfs-image-{i:04d}" for i in range(24, 42)]),
            (lambda n, d: d == "2015.02.21", ["cfs-image-0189"]),
            (lambda n, d: d == "2015.04.11", ["cfs-image-0200"]),
            (lambda n, d: d == "2015.09.05", ["cfs-image-0046"]),
            (lambda n, d: d == "2015.11.07", ["cfs-image-0059", "cfs-image-0060", "cfs-image-0061", "cfs-image-0062"]),
            (lambda n, d: d == "2015.12.12", ["cfs-image-0212", "cfs-image-0213", "cfs-image-0214"]),
            (lambda n, d: d == "2016.01.16", ["cfs-image-0216", "cfs-image-0218"]),
            (lambda n, d: d == "2016.03.05", ["cfs-image-0222"]),
            (lambda n, d: d == "2016.04.03", ["cfs-image-0225"]),
            (lambda n, d: d == "2016.07.16", ["cfs-image-0068", "cfs-image-0066", "cfs-image-0067"]),
            (lambda n, d: d == "2016.07.30", ["cfs-image-0081", "cfs-image-0079", "cfs-image-0080"]),
            (lambda n, d: d == "2016.09.22", ["cfs-image-0095", "cfs-image-0096"]),
            (lambda n, d: d == "2017.03.04", ["cfs-image-0107"]),
            (lambda n, d: d == "2019.03.03", ["cfs-image-0122"]),
            (lambda n, d: d == "2019.04.07", ["cfs-image-0127", "cfs-image-0126"]),
            (lambda n, d: d == "2020.01.29", ["cfs-image-0136"]),
            (lambda n, d: d == "2020.07.11", ["cfs-image-0149"]),
            (lambda n, d: d == "2020.08.01", ["cfs-image-0160"]),
            (lambda n, d: d == "2021.11.09", ["cfs-image-0165"]),
        ]
        for predicate, asset_ids in rules:
            if predicate(name, date):
                return [asset_id for asset_id in asset_ids if asset_id in by_id]
        return []

    events = []
    for idx, event in enumerate(sorted(events_raw, key=lambda item: item.get("start_timestamp", 0)), start=1):
        name = event.get("name", "")
        description = clean(event.get("description", ""))
        themes = theme_for(name, description)
        fbid = hosted_by_title.get(name, {}).get("fbid", "")
        page = detail_page_name(idx, event)
        date = ts(event.get("start_timestamp"), True)
        asset_ids = curated_asset_ids(name, date)
        curated_images = [by_id[asset_id] for asset_id in asset_ids]
        primary_image = prefer_group_photo(curated_images)
        has_detail = len(description) >= 40
        events.append(
            {
                "id": f"event-{idx:03d}",
                "name": name,
                "description": description,
                "date": date,
                "start": ts(event.get("start_timestamp")),
                "end": ts(event.get("end_timestamp")),
                "sort": event.get("start_timestamp", 0),
                "place": place_text(event.get("place")),
                "themes": themes,
                "fbid": fbid,
                "page": page,
                "image": primary_image["webp_asset_path"] if primary_image else "",
                "images": curated_images,
                "has_detail": has_detail,
            }
        )
    return events, image_manifest, by_id


def nav(active=""):
    items = [
        ("index.html", "トップ"),
        ("timeline.html", "時系列"),
        ("themes.html", "テーマ別"),
        ("research.html", "関連資料"),
        ("about.html", "紹介"),
    ]
    links = []
    for href, label in items:
        cls = ' class="active"' if href == active else ""
        links.append(f'<a{cls} href="{href}">{label}</a>')
    logo = "assets/images/webp/cfs-image-0051.webp"
    return f"""
<header class="site-header">
  <a class="brand" href="index.html" aria-label="Code for SAITAMA アーカイブ">
    <img src="{logo}" alt="Code for SAITAMA" />
    <span>Archive</span>
  </a>
  <nav>{''.join(links)}</nav>
</header>
"""


def layout(title, active, body, extra_class=""):
    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{h(title)} | Code for SAITAMA Archive</title>
  <link rel="stylesheet" href="assets/styles.css?v=research1" />
  <script defer src="assets/site.js?v=research1"></script>
</head>
<body class="{extra_class}">
{nav(active)}
<main>
{body}
</main>
<footer class="site-footer">
  <p>Code for SAITAMA 公式アーカイブ</p>
  <p><a href="../docs/code-for-saitama-facebook-archive.md">アーカイブ資料</a> / <a href="../docs/deepresearch-code-for-saitama-analysis.md">関連資料メモ</a> / <a href="assets/images/images-manifest.md">画像一覧</a></p>
</footer>
</body>
</html>
"""


def stat_block(events, images):
    years = [event["date"][:4] for event in events if event["date"]]
    detailed = [event for event in events if event.get("has_detail")]
    photographed = [event for event in events if event.get("images")]
    return f"""
<section class="stats-band">
  <div><strong>{len(events)}</strong><span>Events</span></div>
  <div><strong>{len(detailed)}</strong><span>Detail Pages</span></div>
  <div><strong>{len(photographed)}</strong><span>With Photos</span></div>
  <div><strong>{min(years)}-{max(years)}</strong><span>Recorded Years</span></div>
</section>
"""


def card(item, kind="event"):
    title = item.get("name") or item.get("title")
    meta = item.get("date") or ""
    page = item.get("page")
    theme = " / ".join(label for _, label in item.get("themes", [])[:2])
    image = item.get("image")
    text = excerpt(item.get("description") or item.get("text"), 110)
    has_detail = item.get("has_detail", True)
    title_html = f'<a href="{page}">{h(title)}</a>' if has_detail else h(title)
    thumb_html = f'<a class="thumb" href="{page}">{verified_image_html(image)}</a>' if has_detail else f'<div class="thumb">{verified_image_html(image)}</div>'
    note = "" if has_detail else '<span class="timeline-only">年表のみ</span>'
    return f"""
<article class="archive-card">
  {thumb_html}
  <div>
    <p class="meta">{h(meta)} · {h(theme)} {note}</p>
    <h3>{title_html}</h3>
    <p>{h(text)}</p>
  </div>
</article>
"""


def make_index(events, images, by_id):
    event_by_date = {event["date"]: event for event in events if event.get("has_detail")}
    slider_items = [
        ("cfs-image-0169", "2014.10.18", "まち歩き型マッピングの集合風景", "地域を歩き、情報を記録する活動の入口となる場面です。", event_by_date.get("2014.10.18")),
        ("cfs-image-0001", "2015.01.16", "オープンデータをテーマにしたワークショップの記録", "アイデアを出し合い、公共データの活用を考える場の記録です。", event_by_date.get("2015.01.16")),
        ("cfs-image-0005", "2015.01.16", "ワークショップ会場の記録", "参加者が集まり、意見を交わしている様子です。", event_by_date.get("2015.01.16")),
        ("cfs-image-0010", "2015.01.16", "グループ作業の様子", "机を囲んで話し合いながら作業を進める場面です。", event_by_date.get("2015.01.16")),
        ("cfs-image-0016", "2015.01.16", "発表・共有の場面", "活動の途中で考えを共有している記録です。", event_by_date.get("2015.01.16")),
        ("cfs-image-0021", "2015.01.16", "参加者による検討の記録", "地域やデータについて、参加者が検討している様子です。", event_by_date.get("2015.01.16")),
        ("cfs-image-0024", "2015.01.31", "オープンデータハッカソンの記録", "アイデアを具体化するため、参加者が手を動かした活動の記録です。", event_by_date.get("2015.01.31")),
        ("cfs-image-0028", "2015.01.31", "ハッカソン会場の作業風景", "チームごとに作業を進めている場面です。", event_by_date.get("2015.01.31")),
        ("cfs-image-0031", "2015.01.31", "資料を見ながら進める活動", "参加者が資料や画面を確認しながら進めている記録です。", event_by_date.get("2015.01.31")),
        ("cfs-image-0035", "2015.01.31", "成果共有の様子", "活動の成果や考えを共有する場面です。", event_by_date.get("2015.01.31")),
        ("cfs-image-0040", "2015.01.31", "会場全体の雰囲気", "イベント会場の空気感が伝わる写真です。", event_by_date.get("2015.01.31")),
        ("cfs-image-0046", "2015.09.05", "街歩きに関する活動記録", "地域を実際に見ながら情報を集める活動の記録です。", event_by_date.get("2015.09.05")),
        ("cfs-image-0059", "2015.11.08", "マッピングパーティに関する資料共有", "地図づくりの知見を共有する資料写真です。", None),
        ("cfs-image-0060", "2015.11.08", "地図づくりに関する資料", "活動内容を説明するための資料写真です。", None),
        ("cfs-image-0062", "2015.11.08", "マッピング活動の説明資料", "地図づくりの考え方を共有している記録です。", None),
        ("cfs-image-0212", "2015.12.12", "アイデア共有の場面", "参加者が地域課題やアイデアについて話し合う場面です。", event_by_date.get("2015.12.12")),
        ("cfs-image-0214", "2015.12.12", "グループでの検討風景", "机を囲み、意見を整理している様子です。", event_by_date.get("2015.12.12")),
        ("cfs-image-0216", "2016.01.16", "地域課題を考える活動記録", "テーマに沿って考えを出し合う場面です。", event_by_date.get("2016.01.16")),
        ("cfs-image-0218", "2016.01.16", "参加者による作業風景", "会場で参加者が手を動かしている記録です。", event_by_date.get("2016.01.16")),
        ("cfs-image-0222", "2016.03.05", "オープンデータデイ関連の活動記録", "各地の活動と呼応しながら、埼玉でオープンデータに取り組んだ記録です。", event_by_date.get("2016.03.05")),
        ("cfs-image-0225", "2016.04.03", "街を歩いて記録する活動", "地域を歩きながら情報を確認する活動の記録です。", event_by_date.get("2016.04.03")),
        ("cfs-image-0067", "2016.07.16", "地域課題を考えるワークショップの様子", "関心ごとをもとにチームを作り、地域課題を整理する場面です。", event_by_date.get("2016.07.16")),
        ("cfs-image-0066", "2016.07.16", "ワークショップの検討風景", "参加者がテーマごとに考えをまとめている様子です。", event_by_date.get("2016.07.16")),
        ("cfs-image-0068", "2016.07.16", "会場での共有風景", "話し合った内容を共有している場面です。", event_by_date.get("2016.07.16")),
        ("cfs-image-0079", "2016.07.30", "地域テーマの作業記録", "参加者がテーマに沿って作業を進めている記録です。", event_by_date.get("2016.07.30")),
        ("cfs-image-0080", "2016.07.30", "チーム作業の様子", "会場でチームごとに検討している場面です。", event_by_date.get("2016.07.30")),
        ("cfs-image-0081", "2016.07.30", "発表に向けた準備風景", "資料や意見を整理している活動の記録です。", event_by_date.get("2016.07.30")),
        ("cfs-image-0095", "2016.09.22", "データを使った作業風景", "発表に向けて資料やアイデアをまとめる活動の様子です。", event_by_date.get("2016.09.22")),
        ("cfs-image-0096", "2016.09.22", "検討内容の共有場面", "参加者が検討した内容を共有している記録です。", event_by_date.get("2016.09.22")),
        ("cfs-image-0107", "2017.03.04", "オープンデータデイでの記念写真", "参加者が集まり、成果や活動を共有した場面です。", event_by_date.get("2017.03.04")),
        ("cfs-image-0111", "2017", "活動会場の雰囲気", "イベントと直接結びつけず、活動の雰囲気を伝える写真として掲載しています。", None),
        ("cfs-image-0115", "2017", "参加者が集う場面", "会場で人が集まり、交流している雰囲気がわかる写真です。", None),
        ("cfs-image-0122", "2019.03.03", "マッピング方法を共有する場面", "参加者にマッピングの進め方を説明している記録です。", event_by_date.get("2019.03.03")),
        ("cfs-image-0126", "2019.04.07", "地図を使った活動記録", "地図や地域情報を扱う活動の様子です。", event_by_date.get("2019.04.07")),
        ("cfs-image-0127", "2019.04.07", "地域情報を確認する場面", "参加者が情報を確認しながら活動している記録です。", event_by_date.get("2019.04.07")),
        ("cfs-image-0136", "2020.01.29", "交流・勉強会の記録", "参加者が集まり、知見を共有している場面です。", event_by_date.get("2020.01.29")),
        ("cfs-image-0149", "2020.07.11", "オンライン期の活動記録", "状況に合わせて活動を続けた時期の記録です。", event_by_date.get("2020.07.11")),
        ("cfs-image-0160", "2020.08.01", "オンラインを交えた活動記録", "社会状況に合わせながら活動を継続した時期の記録です。", event_by_date.get("2020.08.01")),
        ("cfs-image-0165", "2021.11.09", "オンラインでの共有活動", "オンラインを活用して情報共有を行った時期の記録です。", event_by_date.get("2021.11.09")),
    ]
    highlights = [event for event in events if event.get("has_detail")][:6]
    slides = []
    for i, (asset_id, date, caption, text, event) in enumerate(slider_items):
        if asset_id not in by_id:
            continue
        button = f'<a class="button" href="{event["page"]}">詳細を見る</a>' if event else ""
        slides.append(
            f"""
<article class="slide{' is-active' if i == 0 else ''}">
  <div class="slide-media">
    <img src="{site_image(by_id[asset_id]['webp_asset_path'])}" alt="" />
  </div>
  <div class="slide-copy">
    <p class="eyebrow">{h(date)}</p>
    <h1>{h(caption)}</h1>
    <p>{h(text)}</p>
    {button}
  </div>
</article>
"""
        )
    body = f"""
<section class="hero-slider" data-slider data-interval="5000">
  {''.join(slides)}
  <button class="carousel-control prev" type="button" data-slider-prev aria-label="前の写真">‹</button>
  <button class="carousel-control next" type="button" data-slider-next aria-label="次の写真">›</button>
  <div class="slider-dots" aria-hidden="true">{''.join('<span></span>' for _ in slides)}</div>
</section>
{stat_block(events, images)}
<section class="intro-band">
  <div>
    <p class="eyebrow">Code for SAITAMA Archive</p>
    <h2>イベント記録からたどる、地図とデータの活動史。</h2>
  </div>
  <p>Facebookバックアップに残るイベント情報を中心に、OpenStreetMap、オープンデータ、アイデアソン、ハッカソン、防災、UDC/COGなどの流れを整理しました。写真は内容との対応を確認できるものだけを詳細に掲載しています。</p>
</section>
<section class="section-head"><h2>初期の主なイベント</h2><a href="timeline.html">年表を見る</a></section>
<div class="card-grid">{''.join(card(event) for event in highlights)}</div>
"""
    return layout("トップ", "index.html", body, "home")


def make_timeline(events):
    combined = []
    for event in events:
        combined.append(
            {
                "kind": "イベント",
                "sort": event["sort"],
                "date": event["date"],
                "title": event["name"],
                "page": event["page"],
                "theme": " / ".join(label for _, label in event["themes"][:2]),
                "text": event.get("description", ""),
                "has_detail": event.get("has_detail"),
            }
        )
    for item in SUPPLEMENTAL_TIMELINE:
        combined.append(
            {
                "kind": "補足",
                "sort": item["sort"],
                "date": item["date"],
                "title": item["title"],
                "page": "",
                "theme": item["theme"],
                "text": item["text"],
                "has_detail": False,
                "source": "関連資料",
                "supplemental": True,
            }
        )
    by_year = defaultdict(list)
    for row in sorted(combined, key=lambda item: item["sort"]):
        year = row["date"][:4] or "不明"
        by_year[year].append(row)
    parts = ['<section class="page-title"><p class="eyebrow">Timeline</p><h1>年表</h1><p>Code for SAITAMAのイベント記録に、関連資料から確認した外部イベント、登壇資料、他コミュニティとの交流を加えて古い順に並べています。本文情報がないもの、または詳細を継続整理中のものは年表のみの掲載です。</p></section>']
    for year in sorted(by_year.keys()):
        parts.append(f'<section class="timeline-year"><h2>{h(year)}</h2><div class="timeline-list">')
        for item in by_year[year]:
            title_html = f'<a href="{item["page"]}">{h(item["title"])}</a>' if item.get("has_detail") else h(item["title"])
            note = "" if item.get("has_detail") else '<span class="timeline-only">年表のみ</span>'
            source = f' <span class="timeline-source">{h(item["source"])}</span>' if item.get("source") else ""
            cls = "timeline-item is-supplemental" if item.get("supplemental") else "timeline-item"
            parts.append(f"""
<article class="{cls}">
  <time>{h(item["date"])}</time>
  <div>
    <p class="meta">{h(item["kind"])} · {h(item["theme"])} {note}{source}</p>
    <h3>{title_html}</h3>
    <p>{h(excerpt(item["text"], 130))}</p>
  </div>
</article>
""")
        parts.append("</div></section>")
    return layout("時系列", "timeline.html", "\n".join(parts))


def make_themes(events):
    theme_labels = {}
    grouped = defaultdict(list)
    for item in events:
        for key, label in item["themes"]:
            theme_labels[key] = label
            grouped[key].append(("イベント", item))
    parts = ['<section class="page-title"><p class="eyebrow">Themes</p><h1>テーマ別に見る</h1><p>活動のまとまりを、地図、データ、防災、学びなどの観点で整理しています。</p></section>']
    for key, label in sorted(theme_labels.items(), key=lambda kv: kv[1]):
        rows = sorted(grouped[key], key=lambda row: row[1]["sort"])
        parts.append(f'<section class="theme-section" id="{key}"><div class="section-head"><h2>{h(label)}</h2><span>{len(rows)}件</span></div><div class="compact-list">')
        for kind, item in rows:
            title = item.get("name") or item.get("title")
            label_html = "詳細" if item.get("has_detail") else "年表のみ"
            if item.get("has_detail"):
                parts.append(f'<a href="{item["page"]}"><time>{h(item.get("date"))}</time><strong>{h(title)}</strong><span>{label_html}</span></a>')
            else:
                parts.append(f'<div class="theme-row"><time>{h(item.get("date"))}</time><strong>{h(title)}</strong><span>{label_html}</span></div>')
        parts.append("</div></section>")
    return layout("テーマ別", "themes.html", "\n".join(parts))


def source_link(url, label):
    return f'<a href="{h(url)}" target="_blank" rel="noopener">{h(label)}</a>'


def make_research(events):
    body = f"""
<section class="page-title research-title">
  <p class="eyebrow">Reference Notes</p>
  <h1>関連資料</h1>
  <p>Code for SAITAMAの活動記録を、公式サイト、GitHub、Code for Japanネットワーク、外部発表資料などの関連情報とあわせて整理しています。追加確認中の情報は参考メモとして掲載します。</p>
</section>
<section class="text-page research-summary">
  <h2>基礎情報</h2>
  <p>Code for SAITAMAは、「埼玉県を活動範囲とするシビックテック団体」として、GISやOpenStreetMapの要素を多く含む活動を行ってきました。2014年1月の発足以降、マッピングパーティ、アイデアソン、ハッカソン、勉強会などを継続的に開催しています。</p>
  <p>設立趣旨は「SAITAMAのITの力で、社会課題の解決を図ることで、市民をわくわくさせる」ことです。ロゴは埼玉の勾玉とマップピンを表し、地域性と地理情報への関心を重ねたものです。</p>
  <div class="source-grid">
    <div><strong>Code for SAITAMAサイト</strong><span>設立趣旨、活動範囲、GIS/OSM志向、ロゴの意味を掲載。</span>{source_link("https://www.code4saitama.org/", "code4saitama.org")}</div>
    <div><strong>GitHub</strong><span>公開リポジトリ、drone_tilesなどの技術的アウトプットを掲載。</span>{source_link("https://github.com/Code4Saitama", "github.com/Code4Saitama")}</div>
    <div><strong>Code for Japan</strong><span>ブリゲードネットワークと県内各コミュニティとの関係を整理。</span>{source_link("https://www.code4japan.org/brigade/all", "ブリゲード一覧")}</div>
  </div>
  <h2>Code for SAITAMAの位置づけ</h2>
  <p>このアーカイブでは、Code for SAITAMAを、さいたま市単位のCode for Saitama-Cityとは別の、埼玉県全域を視野に入れた広域的なシビックテック活動として整理しています。Code for Japanのブリゲード一覧にはCode for Saitama-CityとCode for TODAが掲載されていますが、Code for SAITAMAはそれらとは異なる活動単位として記録しています。</p>
  <p>そのため、県内の自治体別ブリゲードと並列に比較するよりも、GIS、OpenStreetMap、オープンデータ、マッピングの知見を持つ広域コミュニティとして、各地の活動を補完してきたレイヤーとして読むのが自然です。</p>
  <h2>技術的な特徴</h2>
  <p>Facebookバックアップ内のイベントを見ても、マッピングパーティ、地図の勉強会、主題図、LocalWiki、OpenStreetMap、UDC/COG、防災、SDGsなど、地理情報と地域課題をつなぐ活動が目立ちます。GitHub上の公開リポジトリにも、ドローンタイルサーバ、避難所データ、地図表示、フードバンクなど、イベントから派生した可能性のある技術的アウトプットが残っています。</p>
</section>
<section class="theme-section">
  <div class="section-head"><h2>関連資料から見える活動</h2><span>参考情報</span></div>
  <div class="research-list">
    <article><time>2014</time><div><h3>初期コミュニティ形成の記録</h3><p>Qiitaアドベントカレンダー「Code for SAITAMAのこれまで」など、初期活動を説明する外部記事が関連資料として残されています。</p></div></article>
    <article><time>2016-2018</time><div><h3>外部イベント・登壇資料</h3><p>Code for Japan Summit 2016、CIVIC TECH FORUM 2018、レジリナイト、GISキャンプなどへの参加・登壇を、活動の広がりとして整理しています。</p></div></article>
    <article><time>県内外連携</time><div><h3>Code for TODA / Kumagaya / Kusatsu / GIFUなどとの接続</h3><p>各地域コミュニティとの相互補完関係を、Code for SAITAMAの広域的な活動の一部として記録しています。</p></div></article>
    <article><time>2021</time><div><h3>AI災害早期検知研究</h3><p>5mDEMや点群データ、災害被害推定に関する研究発表を、防災・GISの発展的成果として整理しています。</p></div></article>
  </div>
</section>
<section class="text-page">
  <h2>アーカイブ構築上の注意</h2>
  <p>「Code for SAITAMA」は、検索時に金融コードなどの無関係な情報が混入しやすい名称です。このサイトでは、単純なキーワード一致ではなく、公式サイト、Facebookバックアップ、GitHub、Code for Japanネットワーク、イベント名、地図・OpenStreetMap文脈の一致を重視して整理しています。</p>
  <p>個人名、役職、兼任関係、研究発表、外部登壇などは、公開資料と活動記録に基づき、公開に適した範囲で掲載します。</p>
  <p><a class="button text-button" href="../docs/deepresearch-code-for-saitama-analysis.md">関連資料メモを開く</a></p>
</section>
"""
    return layout("関連資料", "research.html", body)


def make_activities(activities):
    parts = ['<section class="page-title"><p class="eyebrow">Activities</p><h1>投稿・アルバム・リンク</h1><p>イベントページ以外に残された日々の共有、写真、リンク、アルバムをまとめています。</p></section>']
    parts.append('<div class="card-grid">')
    for item in activities:
        parts.append(card(item, "activity"))
    parts.append("</div>")
    return layout("アクティビティ", "activities.html", "\n".join(parts))


def make_gallery(images):
    usable = [row for row in images if row.get("webp_asset_path")]
    parts = ['<section class="page-title"><p class="eyebrow">Gallery</p><h1>写真で見る活動</h1><p>バックアップから抽出・WebP変換した写真素材です。</p></section>']
    parts.append('<div class="gallery-grid">')
    for row in usable:
        parts.append(f"""
<figure>
  <img src="{site_image(row['webp_asset_path'])}" alt="" loading="lazy" />
  <figcaption><strong>{h(row['asset_id'])}</strong><span>{h(row.get('source_title'))}</span></figcaption>
</figure>
""")
    parts.append("</div>")
    return layout("写真", "gallery.html", "\n".join(parts))


def make_about(events, images):
    body = f"""
<section class="page-title about-title">
  <p class="eyebrow">About</p>
  <h1>Code for SAITAMAとは</h1>
  <p>埼玉県を拠点に、テクノロジー、オープンデータ、地図、地域課題解決をつなぐ活動を行ってきた非営利団体です。</p>
</section>
{stat_block(events, images)}
<section class="text-page">
  <h2>アーカイブの視点</h2>
  <p>このサイトは、Code for SAITAMAのFacebookバックアップに残るイベント情報を中心に再構成した公式アーカイブです。イベント本文が存在するものは詳細ページを作り、本文情報がないものは年表のみの掲載にしています。</p>
  <p>写真はイベントとの対応を確認できるものだけを詳細ページに掲載しています。トップのスライダーでは、イベントと直接紐づかない写真も活動の雰囲気を伝える素材として使っていますが、キャプションは写真から安全に言える範囲に限定しています。</p>
  <p>外部発表資料、GitHub、Code for Japanネットワークなどから整理した関連情報は、<a href="research.html">関連資料</a>に分けて掲載しています。</p>
  <h2>掲載範囲</h2>
  <p>Messenger、フォロワー、端末情報、IPを含むメタデータなど、公開に適さない情報はこのサイトには掲載していません。</p>
</section>
"""
    return layout("紹介", "about.html", body)


def detail_meta(rows):
    return "<dl class=\"detail-meta\">" + "".join(f"<div><dt>{h(k)}</dt><dd>{h(v)}</dd></div>" for k, v in rows if v) + "</dl>"


def format_description(description):
    lines = [line.strip() for line in clean(description).splitlines()]
    html_parts = []
    paragraph = []
    schedule = []

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            html_parts.append("<p>" + "<br>".join(h(line) for line in paragraph) + "</p>")
            paragraph = []

    def flush_schedule():
        nonlocal schedule
        if schedule:
            html_parts.append('<ul class="schedule-list">' + "".join(f"<li>{h(line)}</li>" for line in schedule) + "</ul>")
            schedule = []

    for line in lines:
        if not line:
            flush_paragraph()
            flush_schedule()
            continue
        is_heading = line.startswith("■") or (line.startswith("【") and line.endswith("】"))
        is_schedule = bool(re.match(r"^\\d{1,2}[:：]\\d{2}[-－〜~]", line)) or bool(re.match(r"^\\d{1,2}時", line))
        if is_heading:
            flush_paragraph()
            flush_schedule()
            html_parts.append(f"<h2>{h(line.strip('■'))}</h2>")
        elif is_schedule:
            flush_paragraph()
            schedule.append(line)
        else:
            flush_schedule()
            paragraph.append(line)
    flush_paragraph()
    flush_schedule()
    return "\n".join(html_parts) or "<p>詳細説明はバックアップ内にありません。</p>"


def make_event_detail(event):
    fb = f"https://www.facebook.com/events/{event['fbid']}/" if event.get("fbid") else ""
    gallery = ""
    if event.get("images"):
        gallery = '<section class="detail-gallery">' + "".join(
            f'<figure><img src="{site_image(row["webp_asset_path"])}" alt="" loading="lazy" /><figcaption>関連写真 / {h(row["asset_id"])}</figcaption></figure>'
            for row in event["images"][:24]
        ) + "</section>"
    body = f"""
<article class="detail-page">
  <div class="detail-hero">
    {verified_image_html(event.get('image'))}
    <div>
      <p class="eyebrow">Event / {h(event['date'])}</p>
      <h1>{h(event['name'])}</h1>
      <p>{h(excerpt(event['description'], 210))}</p>
    </div>
  </div>
  {detail_meta([('開始', event['start']), ('終了', event['end']), ('場所', event['place']), ('テーマ', ' / '.join(label for _, label in event['themes'])), ('Facebookイベント', fb)])}
  <section class="text-page">
    <h2>詳細</h2>
    {format_description(event['description'])}
  </section>
  {gallery}
</article>
"""
    return layout(event["name"], "", body)


def make_activity_detail(item, images):
    linked_images = []
    media_set = set(item.get("media", []))
    for row in images:
        if row.get("original_backup_path") in media_set:
            linked_images.append(row)
    if not linked_images and item.get("image"):
        linked_images = [row for row in images if row.get("webp_asset_path") == item["image"]]
    image_html = ""
    if linked_images:
        image_html = '<section class="detail-gallery">' + "".join(
            f'<figure><img src="{site_image(row["webp_asset_path"])}" alt="" loading="lazy" /><figcaption>{h(row["asset_id"])} / {h(row.get("source_title"))}</figcaption></figure>'
            for row in linked_images[:24]
        ) + "</section>"
    urls = "".join(f'<li><a href="{h(url)}">{h(url)}</a></li>' for url in item.get("urls", []))
    shared = "".join(f"<li>{h(name)}</li>" for name in item.get("shared_events", []))
    body = f"""
<article class="detail-page">
  <div class="detail-hero">
    <img src="{site_image(item['image'])}" alt="" />
    <div>
      <p class="eyebrow">{h(item['kind'])} / {h(item['date'])}</p>
      <h1>{h(item['title'])}</h1>
      <p>{h(excerpt(item['text'], 210))}</p>
    </div>
  </div>
  {detail_meta([('日時', item['time']), ('種別', item['kind']), ('テーマ', ' / '.join(label for _, label in item['themes']))])}
  <section class="text-page">
    <h2>本文・説明</h2>
    {''.join(f'<p>{h(p)}</p>' for p in clean(item['text']).split('\\n\\n') if p.strip()) or '<p>本文はありません。</p>'}
    {'<h2>リンク</h2><ul>' + urls + '</ul>' if urls else ''}
    {'<h2>共有イベント</h2><ul>' + shared + '</ul>' if shared else ''}
  </section>
  {image_html}
</article>
"""
    return layout(item["title"], "", body)


def css():
    return r"""
:root {
  --ink: #22201d;
  --muted: #6d6a63;
  --line: #d8d3ca;
  --paper: #f7f5ef;
  --panel: #ffffff;
  --orange: #e95518;
  --teal: #176b72;
  --green: #536d42;
  --steel: #3d4752;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic", "YuGothic", "Noto Sans JP", sans-serif;
  color: var(--ink);
  background: var(--paper);
  line-height: 1.65;
  letter-spacing: 0;
}
a { color: inherit; text-decoration: none; }
.site-header {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 28px;
  min-height: 76px;
  padding: 10px clamp(18px, 4vw, 56px);
  background: rgba(247, 245, 239, .94);
  border-bottom: 1px solid var(--line);
  backdrop-filter: blur(16px);
}
.brand { display: flex; align-items: center; gap: 14px; font-weight: 700; color: var(--steel); }
.brand img { width: 176px; height: 48px; object-fit: contain; object-position: left center; mix-blend-mode: multiply; }
.brand span { border-left: 1px solid var(--line); padding-left: 14px; text-transform: uppercase; font-size: 13px; letter-spacing: .08em; }
nav { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }
nav a { padding: 8px 10px; font-size: 15px; border-bottom: 2px solid transparent; color: var(--muted); }
nav a.active, nav a:hover { color: var(--ink); border-color: var(--orange); }
main { min-height: 70vh; }
.hero-slider {
  position: relative;
  min-height: min(86vh, 820px);
  overflow: hidden;
  background: #181714;
  border-bottom: 1px solid var(--line);
}
.slide {
  position: absolute;
  top: clamp(28px, 4vw, 54px);
  left: 50%;
  bottom: clamp(82px, 8vw, 122px);
  width: min(78vw, 1120px);
  opacity: 0;
  pointer-events: none;
  transform: translateX(-50%) scale(.88);
  transition: transform 900ms ease, opacity 900ms ease, filter 900ms ease;
  filter: saturate(.88) contrast(.86) brightness(.78);
}
.slide.is-active {
  opacity: 1;
  pointer-events: auto;
  transform: translateX(-50%) scale(1);
  filter: none;
  z-index: 3;
}
.slide.is-prev {
  opacity: .54;
  transform: translateX(calc(-50% - min(72vw, 940px))) scale(.88);
  z-index: 1;
}
.slide.is-next {
  opacity: .54;
  transform: translateX(calc(-50% + min(72vw, 940px))) scale(.88);
  z-index: 1;
}
.slide-media {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  padding: clamp(16px, 2.8vw, 34px);
  background:
    radial-gradient(circle at 18% 15%, rgba(233, 85, 24, .18), transparent 34%),
    linear-gradient(135deg, #24221f, #11100f);
  border: 1px solid rgba(255,255,255,.22);
  box-shadow: 0 22px 60px rgba(0,0,0,.42);
}
.slide-media img {
  max-width: 100%;
  max-height: min(72vh, 690px);
  width: auto;
  height: auto;
  object-fit: contain;
  filter: saturate(1.34) contrast(1.26) brightness(1.06);
  background: #fff;
}
.slide-copy {
  position: absolute;
  left: clamp(20px, 4vw, 56px);
  right: clamp(20px, 4vw, 56px);
  bottom: clamp(20px, 4vw, 52px);
  z-index: 2;
  width: auto;
  padding: clamp(18px, 3vw, 34px);
  color: #fff;
  background: linear-gradient(90deg, rgba(10,10,10,.82), rgba(10,10,10,.62), rgba(10,10,10,.24));
  border: 1px solid rgba(255,255,255,.24);
  backdrop-filter: blur(10px);
}
.eyebrow { margin: 0 0 10px; color: var(--orange); font-weight: 700; text-transform: uppercase; font-size: 14px; letter-spacing: .08em; }
.slide-copy .eyebrow {
  display: inline-flex;
  align-items: center;
  min-height: 42px;
  padding: 4px 14px;
  margin-bottom: 14px;
  color: #fff;
  background: rgba(233,85,24,.94);
  font-size: clamp(22px, 3.2vw, 38px);
  line-height: 1;
  letter-spacing: .03em;
}
.slide-copy h1 { font-size: clamp(30px, 3.5vw, 48px); line-height: 1.16; margin: 0 0 16px; max-width: 780px; }
.slide-copy p:not(.eyebrow) { max-width: 660px; color: rgba(255,255,255,.86); font-size: 17px; }
.button { display: inline-flex; align-items: center; min-height: 46px; padding: 9px 18px; background: var(--orange); color: #fff; font-weight: 700; margin-top: 10px; font-size: 16px; }
.slider-dots { position: absolute; left: 50%; transform: translateX(-50%); bottom: 30px; z-index: 5; display: flex; gap: 7px; max-width: min(92vw, 900px); flex-wrap: wrap; justify-content: center; }
.slider-dots span { width: 22px; height: 3px; background: rgba(255,255,255,.34); }
.slider-dots span.is-active { background: var(--orange); }
.carousel-control {
  position: absolute;
  z-index: 6;
  top: 50%;
  transform: translateY(-50%);
  width: 44px;
  height: 56px;
  border: 1px solid rgba(255,255,255,.32);
  background: rgba(20,20,20,.58);
  color: #fff;
  font-size: 34px;
  line-height: 1;
  cursor: pointer;
}
.carousel-control:hover { background: rgba(233,85,24,.92); }
.carousel-control.prev { left: clamp(12px, 2.5vw, 34px); }
.carousel-control.next { right: clamp(12px, 2.5vw, 34px); }
.stats-band {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border-block: 1px solid var(--line);
  background: #fff;
}
.stats-band div { min-height: 104px; padding: 20px clamp(18px, 4vw, 42px); border-right: 1px solid var(--line); }
.stats-band strong { display: block; font-size: clamp(32px, 3.7vw, 46px); line-height: 1; color: var(--teal); white-space: nowrap; }
.stats-band span { color: var(--muted); font-size: 14px; text-transform: uppercase; }
.intro-band, .section-head, .page-title, .text-page, .theme-section, .timeline-year {
  width: min(1160px, calc(100% - 36px));
  margin-inline: auto;
}
.intro-band {
  display: grid;
  grid-template-columns: 1.1fr .9fr;
  gap: 36px;
  padding: 70px 0 48px;
}
.intro-band h2, .page-title h1 { margin: 0; font-size: clamp(30px, 4.6vw, 54px); line-height: 1.18; }
.intro-band > p, .page-title p { font-size: 18px; color: var(--muted); margin: 0; }
.section-head { display: flex; justify-content: space-between; align-items: end; gap: 18px; padding: 48px 0 20px; border-bottom: 1px solid var(--line); }
.section-head h2 { margin: 0; font-size: 30px; }
.section-head a, .section-head span { color: var(--teal); font-weight: 700; }
.card-grid, .activity-strip {
  width: min(1160px, calc(100% - 36px));
  margin: 24px auto 52px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
}
.activity-strip { grid-template-columns: repeat(4, 1fr); }
.archive-card {
  background: var(--panel);
  border: 1px solid var(--line);
  display: grid;
  grid-template-rows: auto 1fr;
  min-width: 0;
}
.archive-card .thumb { display: block; aspect-ratio: 4 / 3; overflow: hidden; background: #ddd; }
.archive-card img { width: 100%; height: 100%; object-fit: cover; transition: transform 500ms ease; }
.verified-placeholder { width: 100%; height: 100%; min-height: 220px; display: grid; place-items: center; padding: 22px; background: linear-gradient(135deg, #fff, #eee8dc); color: var(--muted); font-weight: 700; border: 1px solid var(--line); }
.verified-placeholder img { width: min(78%, 420px); height: auto; object-fit: contain; mix-blend-mode: multiply; }
.archive-card:hover img { transform: scale(1.035); }
.archive-card div { padding: 16px; }
.meta { margin: 0 0 8px; color: var(--muted); font-size: 14px; }
.timeline-only { display: inline-block; margin-left: 6px; color: var(--green); font-weight: 700; }
.archive-card h3 { margin: 0 0 8px; font-size: 20px; line-height: 1.35; }
.archive-card p { margin: 0; color: var(--muted); font-size: 16px; }
.page-title { padding: 64px 0 28px; border-bottom: 1px solid var(--line); }
.timeline-year { padding: 30px 0; display: grid; grid-template-columns: 140px 1fr; gap: 28px; border-bottom: 1px solid var(--line); }
.timeline-year h2 { margin: 0; color: var(--teal); font-size: 38px; }
.timeline-list { display: grid; gap: 14px; }
.timeline-item { display: grid; grid-template-columns: 120px 1fr; gap: 20px; padding: 18px; background: #fff; border-left: 4px solid var(--green); }
.timeline-item.is-supplemental { border-left-color: var(--orange); background: #fffdfa; }
.timeline-item time { color: var(--muted); font-weight: 700; font-size: 17px; }
.timeline-item h3 { margin: 0 0 6px; line-height: 1.4; font-size: 22px; }
.timeline-item p { margin: 0; color: var(--muted); font-size: 16px; }
.timeline-source {
  display: inline-block;
  margin-left: 6px;
  color: var(--teal);
  font-weight: 700;
}
.theme-section { padding: 14px 0 34px; }
.compact-list { display: grid; background: #fff; border: 1px solid var(--line); }
.compact-list a, .compact-list .theme-row { display: grid; grid-template-columns: 110px 1fr 110px; gap: 14px; padding: 13px 16px; border-bottom: 1px solid var(--line); align-items: center; }
.compact-list a:hover { background: #f0ede6; }
.compact-list time, .compact-list span { color: var(--muted); font-size: 15px; }
.compact-list strong { font-size: 17px; }
.compact-list .theme-row { color: var(--muted); }
.source-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin: 22px 0 10px;
}
.source-grid div {
  display: grid;
  gap: 8px;
  padding: 16px;
  border: 1px solid var(--line);
  background: #fbfaf6;
}
.source-grid strong { font-size: 18px; }
.source-grid span { color: var(--muted); font-size: 15px; }
.source-grid a, .text-page a:not(.button) { color: var(--teal); font-weight: 700; text-decoration: underline; text-underline-offset: 3px; }
.research-list {
  display: grid;
  gap: 12px;
  margin: 18px 0 44px;
}
.research-list article {
  display: grid;
  grid-template-columns: 150px 1fr;
  gap: 20px;
  padding: 18px;
  border-left: 4px solid var(--orange);
  background: #fff;
}
.research-list time {
  color: var(--teal);
  font-size: 20px;
  font-weight: 800;
}
.research-list h3 { margin: 0 0 6px; font-size: 22px; }
.research-list p { margin: 0; color: var(--muted); font-size: 16px; }
.text-button { margin-top: 14px; text-decoration: none; }
.gallery-grid {
  width: min(1280px, calc(100% - 24px));
  margin: 28px auto 64px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}
.gallery-grid figure { margin: 0; background: #fff; border: 1px solid var(--line); }
.gallery-grid img { width: 100%; aspect-ratio: 1 / 1; object-fit: cover; display: block; }
.gallery-grid figcaption { display: grid; gap: 2px; padding: 8px; font-size: 12px; color: var(--muted); }
.gallery-grid strong { color: var(--ink); }
.detail-page { width: min(1120px, calc(100% - 36px)); margin: 44px auto 72px; }
.detail-hero { display: grid; grid-template-columns: minmax(280px, 48%) 1fr; gap: 34px; align-items: end; border-bottom: 1px solid var(--line); padding-bottom: 28px; }
.detail-hero img, .detail-hero .verified-placeholder { width: 100%; aspect-ratio: 4 / 3; object-fit: cover; border: 1px solid var(--line); background: #fff; min-height: 260px; }
.detail-hero h1 { margin: 0 0 14px; font-size: clamp(30px, 4vw, 50px); line-height: 1.18; }
.detail-hero p:not(.eyebrow) { color: var(--muted); }
.detail-meta { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; background: var(--line); margin: 28px 0; border: 1px solid var(--line); }
.detail-meta div { background: #fff; padding: 14px; min-width: 0; }
.detail-meta dt { font-size: 14px; color: var(--muted); }
.detail-meta dd { margin: 3px 0 0; font-weight: 700; overflow-wrap: anywhere; font-size: 16px; }
.text-page { background: #fff; border: 1px solid var(--line); padding: clamp(22px, 4vw, 44px); margin-top: 24px; }
.text-page h2 { margin-top: 0; }
.text-page h2:not(:first-child) { margin-top: 30px; padding-top: 22px; border-top: 1px solid var(--line); }
.text-page p { color: #3c3934; font-size: 17px; }
.schedule-list { list-style: none; padding: 0; margin: 12px 0 24px; border: 1px solid var(--line); background: #fbfaf6; }
.schedule-list li { padding: 10px 14px; border-bottom: 1px solid var(--line); }
.schedule-list li:last-child { border-bottom: 0; }
.detail-gallery { margin-top: 28px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.detail-gallery figure { margin: 0; background: #fff; border: 1px solid var(--line); }
.detail-gallery img { width: 100%; aspect-ratio: 4 / 3; object-fit: cover; display: block; }
.detail-gallery figcaption { padding: 8px; font-size: 12px; color: var(--muted); }
.site-footer { border-top: 1px solid var(--line); padding: 28px clamp(18px, 4vw, 56px); color: var(--muted); display: flex; justify-content: space-between; gap: 18px; flex-wrap: wrap; background: #fff; }
.site-footer p { margin: 0; font-size: 14px; }
.site-footer a { color: var(--teal); font-weight: 700; }
@media (max-width: 900px) {
  .site-header { align-items: flex-start; flex-direction: column; gap: 8px; }
  nav { justify-content: flex-start; }
  .hero-slider { min-height: 760px; }
  .slide { top: 24px; bottom: 86px; width: min(84vw, 760px); }
  .slide.is-prev { transform: translateX(calc(-50% - 78vw)) scale(.88); }
  .slide.is-next { transform: translateX(calc(-50% + 78vw)) scale(.88); }
  .slide-media { padding: 16px; }
  .slide-media img { max-height: 70vh; }
  .slide-copy { left: 18px; right: 18px; bottom: 58px; width: auto; padding: 20px; }
  .slide-copy .eyebrow { font-size: clamp(22px, 6vw, 34px); }
  .slide-copy h1 { font-size: clamp(28px, 8vw, 42px); }
  .carousel-control { top: 46%; }
  .carousel-control.next { right: 18px; }
  .stats-band, .intro-band, .card-grid, .activity-strip, .detail-hero, .detail-meta { grid-template-columns: 1fr 1fr; }
  .activity-strip, .card-grid, .gallery-grid, .detail-gallery { grid-template-columns: 1fr 1fr; }
  .timeline-year { grid-template-columns: 1fr; }
  .source-grid { grid-template-columns: 1fr; }
  .research-list article { grid-template-columns: 1fr; gap: 6px; }
}
@media (max-width: 620px) {
  .brand img { width: 148px; height: 40px; }
  nav a { padding: 6px 7px; font-size: 14px; }
  .hero-slider { min-height: 760px; }
  .slide { width: 86vw; bottom: 92px; }
  .slide.is-prev { transform: translateX(calc(-50% - 82vw)) scale(.88); }
  .slide.is-next { transform: translateX(calc(-50% + 82vw)) scale(.88); }
  .slide-copy { bottom: 46px; padding: 16px; }
  .slide-copy p:not(.eyebrow) { display: none; }
  .stats-band, .intro-band, .card-grid, .activity-strip, .gallery-grid, .detail-hero, .detail-meta, .detail-gallery { grid-template-columns: 1fr; }
  .compact-list a, .compact-list .theme-row, .timeline-item { grid-template-columns: 1fr; gap: 6px; }
}
"""


def js():
    return r"""
(() => {
  const slider = document.querySelector("[data-slider]");
  if (!slider) return;
  const slides = Array.from(slider.querySelectorAll(".slide"));
  const dots = Array.from(slider.querySelectorAll(".slider-dots span"));
  const prev = slider.querySelector("[data-slider-prev]");
  const next = slider.querySelector("[data-slider-next]");
  const interval = Number(slider.dataset.interval || 5000);
  let index = 0;
  let timer = null;
  const applyState = () => {
    const previousIndex = (index - 1 + slides.length) % slides.length;
    const nextIndex = (index + 1) % slides.length;
    slides.forEach((slide, i) => {
      slide.classList.toggle("is-active", i === index);
      slide.classList.toggle("is-prev", i === previousIndex);
      slide.classList.toggle("is-next", i === nextIndex);
    });
    dots.forEach((dot, i) => dot.classList.toggle("is-active", i === index));
  };
  const show = (nextIndex) => {
    index = (nextIndex + slides.length) % slides.length;
    applyState();
  };
  const restart = () => {
    window.clearInterval(timer);
    timer = window.setInterval(() => show(index + 1), interval);
  };
  applyState();
  if (prev) prev.addEventListener("click", () => { show(index - 1); restart(); });
  if (next) next.addEventListener("click", () => { show(index + 1); restart(); });
  timer = window.setInterval(() => show(index + 1), interval);
})();
"""


def write(path, content):
    (SITE / path).write_text(content, encoding="utf-8")


def prepare_site_dir():
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "assets").mkdir(parents=True, exist_ok=True)
    for path in SITE.glob("*.html"):
        path.unlink()
    for filename in ("styles.css", "site.js"):
        path = SITE / "assets" / filename
        if path.exists():
            path.unlink()


def main():
    prepare_site_dir()
    events, images, by_id = build_data()
    write("assets/styles.css", css())
    write("assets/site.js", js())
    write("index.html", make_index(events, images, by_id))
    write("timeline.html", make_timeline(events))
    write("themes.html", make_themes(events))
    write("research.html", make_research(events))
    write("about.html", make_about(events, images))
    for event in events:
        if event.get("has_detail"):
            write(event["page"], make_event_detail(event))
    print(SITE)
    print(f"events={len(events)} detail_pages={sum(1 for event in events if event.get('has_detail'))} images={len(images)} pages={len(list(SITE.glob('*.html')))}")


if __name__ == "__main__":
    main()
