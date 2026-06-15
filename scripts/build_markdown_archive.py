#!/usr/bin/env python3
import datetime as dt
import json
import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "facebook-export"
DOCS = ROOT / "docs"
OUT = DOCS / "code-for-saitama-facebook-archive.md"

EVENTS_FILE = DATA / "this_profile's_activity_across_facebook/events/events.json"
HOSTED_FILE = DATA / "this_profile's_activity_across_facebook/events/events_you_hosted.json"
POSTS_FILE = DATA / "this_profile's_activity_across_facebook/posts/profile_posts_1.json"
PROFILE_FILE = DATA / "profile_information/profile_information/profile_information.json"


def fix_text(value):
    if isinstance(value, str):
        try:
            return value.encode("latin1").decode("utf-8")
        except UnicodeEncodeError:
            return value
        except UnicodeDecodeError:
            return value
    if isinstance(value, list):
        return [fix_text(item) for item in value]
    if isinstance(value, dict):
        return {fix_text(k): fix_text(v) for k, v in value.items()}
    return value


def load_json(path):
    with path.open(encoding="utf-8") as f:
        return fix_text(json.load(f))


def timestamp(value):
    if not value:
        return ""
    # Facebook exports sometimes use 0 for "not set"; in JST that renders as 1970-01-01 09:00.
    if value == 0:
        return ""
    return dt.datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M")


def date_only(value):
    if not value:
        return ""
    return dt.datetime.fromtimestamp(value).strftime("%Y-%m-%d")


def md_escape(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def fb_export_path(value):
    value = str(value or "")
    if value.startswith(("this_profile's_activity_across_facebook/", "profile_information/", "connections/")):
        return f"data/facebook-export/{value}"
    return value


def clean_description(value):
    if not value:
        return ""
    lines = [line.rstrip() for line in value.replace("\r\n", "\n").split("\n")]
    return "\n".join(lines).strip()


def summarize(value, limit=150):
    value = re.sub(r"\s+", " ", value or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def event_theme(name, description):
    text = f"{name}\n{description}"
    rules = [
        ("OpenStreetMap / マッピング", ["OpenStreetMap", "OSM", "マッピング", "地図"]),
        ("オープンデータ / UDC / COG", ["オープンデータ", "UDC", "アーバンデータ", "COG", "オープンガバナンス"]),
        ("防災 / 災害対応", ["防災", "災害", "ハザード", "能登半島地震"]),
        ("アイデアソン / ハッカソン", ["アイデアソン", "ハッカソン", "hackathon"]),
        ("Meetup / 交流", ["Meetup", "ミートアップ", "交流会", "もくもく"]),
        ("IoT / 電子工作", ["Arduino", "IoT", "電子工作"]),
        ("SDGs", ["SDGs", "SDGｓ"]),
    ]
    matched = [label for label, keys in rules if any(key in text for key in keys)]
    return "、".join(matched) if matched else "その他"


def place_text(place):
    if not place:
        return ""
    if isinstance(place, str):
        return place
    name = place.get("name", "")
    address = place.get("address", "")
    if name and address:
        return f"{name}（{address}）"
    return name or address


def extract_post_text(post):
    texts = []
    for item in post.get("data", []):
        if item.get("post"):
            texts.append(clean_description(item["post"]))
    return "\n\n".join(texts).strip()


def extract_post_attachments(post):
    events = []
    urls = []
    media = []
    for attachment in post.get("attachments", []):
        for item in attachment.get("data", []):
            if item.get("event"):
                events.append(item["event"])
            url = item.get("external_context", {}).get("url")
            if url:
                urls.append(url)
            if item.get("media", {}).get("uri"):
                media.append(item["media"]["uri"])
    return events, urls, media


def make_event_url(fbid):
    return f"https://www.facebook.com/events/{fbid}/" if fbid else ""


def main():
    profile = load_json(PROFILE_FILE).get("profile_v2", {})
    events = load_json(EVENTS_FILE).get("your_events_v2", [])
    hosted = load_json(HOSTED_FILE)
    posts = load_json(POSTS_FILE)

    hosted_by_title = {item.get("title"): item for item in hosted}
    events = sorted(events, key=lambda item: item.get("start_timestamp", 0), reverse=True)
    posts = sorted(posts, key=lambda item: item.get("timestamp", 0), reverse=True)

    for event in events:
        hosted_item = hosted_by_title.get(event.get("name"), {})
        event["fbid"] = hosted_item.get("fbid", "")
        event["theme"] = event_theme(event.get("name", ""), event.get("description", ""))

    theme_counts = {}
    year_counts = {}
    for event in events:
        year = date_only(event.get("start_timestamp"))[:4] or "不明"
        year_counts[year] = year_counts.get(year, 0) + 1
        for theme in event["theme"].split("、"):
            theme_counts[theme] = theme_counts.get(theme, 0) + 1

    lines = []
    lines.append("# Code for SAITAMA Facebookアーカイブ")
    lines.append("")
    lines.append("FacebookバックアップJSONから抽出した、Code for SAITAMAの活動記録です。イベント情報を中心に、関連する投稿・写真・リンクも後続のアーカイブ化に使えるようMarkdownで整理しています。")
    lines.append("")
    lines.append("## 基本情報")
    lines.append("")
    lines.append(f"- 名称: {profile.get('name', {}).get('full_name', 'Code for SAITAMA')}")
    lines.append(f"- Facebook: {profile.get('profile_uri', '')}")
    lines.append(f"- ユーザー名: {profile.get('username', '')}")
    lines.append(f"- Web: {', '.join(site.get('address', '') for site in profile.get('websites', []))}")
    addr = profile.get("address", {})
    address = " ".join(part for part in [addr.get("region", ""), addr.get("city", ""), addr.get("street", ""), addr.get("zipcode", "")] if part)
    if address:
        lines.append(f"- 所在地表記: {address}")
    if profile.get("profile_category"):
        lines.append(f"- カテゴリ: {profile.get('profile_category')}")
    if profile.get("registration_timestamp"):
        lines.append(f"- Facebook登録日: {timestamp(profile.get('registration_timestamp'))}")
    lines.append("")

    lines.append("## 抽出サマリー")
    lines.append("")
    lines.append(f"- イベント件数: {len(events)}件")
    lines.append(f"- ページ主催として記録されているイベント: {len(hosted)}件")
    lines.append(f"- 投稿件数: {len(posts)}件")
    lines.append(f"- 対象期間: {date_only(min(e.get('start_timestamp', 0) for e in events if e.get('start_timestamp')))}〜{date_only(max(e.get('start_timestamp', 0) for e in events if e.get('start_timestamp')))}")
    lines.append("")
    lines.append("### 年別イベント件数")
    lines.append("")
    lines.append("| 年 | 件数 |")
    lines.append("|---|---:|")
    for year in sorted(year_counts, reverse=True):
        lines.append(f"| {year} | {year_counts[year]} |")
    lines.append("")
    lines.append("### テーマ別イベント件数")
    lines.append("")
    lines.append("| テーマ | 件数 |")
    lines.append("|---|---:|")
    for theme, count in sorted(theme_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| {theme} | {count} |")
    lines.append("")

    lines.append("## イベント年表")
    lines.append("")
    lines.append("| 日時 | イベント | 場所 | テーマ | Facebookイベント |")
    lines.append("|---|---|---|---|---|")
    for event in events:
        url = make_event_url(event.get("fbid"))
        link = f"[{event.get('fbid')}]({url})" if url else ""
        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(timestamp(event.get("start_timestamp"))),
                    md_escape(event.get("name", "")),
                    md_escape(place_text(event.get("place"))),
                    md_escape(event.get("theme", "")),
                    md_escape(link),
                ]
            )
            + " |"
        )
    lines.append("")

    lines.append("## イベント詳細")
    lines.append("")
    for event in events:
        lines.append(f"### {date_only(event.get('start_timestamp'))} {event.get('name', '')}")
        lines.append("")
        lines.append(f"- 開始: {timestamp(event.get('start_timestamp'))}")
        if timestamp(event.get("end_timestamp")):
            lines.append(f"- 終了: {timestamp(event.get('end_timestamp'))}")
        if place_text(event.get("place")):
            lines.append(f"- 場所: {place_text(event.get('place'))}")
        if event.get("theme"):
            lines.append(f"- テーマ: {event.get('theme')}")
        if event.get("create_timestamp"):
            lines.append(f"- Facebookイベント作成日時: {timestamp(event.get('create_timestamp'))}")
        if event.get("fbid"):
            lines.append(f"- FacebookイベントID: [{event.get('fbid')}]({make_event_url(event.get('fbid'))})")
        if event.get("description"):
            lines.append("")
            lines.append(clean_description(event.get("description")))
        lines.append("")

    related_posts = []
    grouped_posts = {}
    for post in posts:
        text = extract_post_text(post)
        shared_events, urls, media = extract_post_attachments(post)
        if not (text or shared_events or urls or media):
            continue
        key = (
            post.get("timestamp"),
            post.get("title", ""),
            tuple(event.get("name", "") for event in shared_events),
            tuple(urls),
            tuple(media),
        )
        if key not in grouped_posts:
            grouped_posts[key] = [post, [], shared_events, urls, media]
        if text and text not in grouped_posts[key][1]:
            grouped_posts[key][1].append(text)
    for post, texts, shared_events, urls, media in grouped_posts.values():
        related_posts.append((post, "\n\n".join(texts), shared_events, urls, media))

    lines.append("## 関連投稿・写真・リンク")
    lines.append("")
    lines.append("イベントページ以外の投稿から、本文・リンク・写真パス・共有イベントを抽出しています。画像パスは `data/facebook-export/` 配下のFacebookバックアップ内相対パスです。")
    lines.append("")
    lines.append(f"抽出対象: {len(related_posts)}件（同一内容の重複投稿は除外）")
    lines.append("")
    for post, text, shared_events, urls, media in related_posts:
        lines.append(f"### {timestamp(post.get('timestamp'))} {post.get('title', '')}")
        lines.append("")
        if text:
            lines.append(text)
            lines.append("")
        for event in shared_events:
            name = event.get("name", "")
            start = timestamp(event.get("start_timestamp"))
            end = timestamp(event.get("end_timestamp"))
            lines.append(f"- 共有イベント: {name}（{start}〜{end}）")
        for url in urls:
            lines.append(f"- URL: {url}")
        for item in media:
            lines.append(f"- 画像: `{fb_export_path(item)}`")
        lines.append("")

    lines.append("## 元データ")
    lines.append("")
    lines.append("| 内容 | ファイル |")
    lines.append("|---|---|")
    lines.append("| イベント一覧 | `data/facebook-export/this_profile's_activity_across_facebook/events/events.json` |")
    lines.append("| 主催イベントメタ情報 | `data/facebook-export/this_profile's_activity_across_facebook/events/events_you_hosted.json` |")
    lines.append("| ページ投稿 | `data/facebook-export/this_profile's_activity_across_facebook/posts/profile_posts_1.json` |")
    lines.append("| 基本プロフィール | `data/facebook-export/profile_information/profile_information/profile_information.json` |")
    lines.append("")

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
