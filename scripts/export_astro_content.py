#!/usr/bin/env python3
import json
import pathlib
import re
import shutil
import sys
import datetime as dt

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_archive_site as archive  # noqa: E402

CONTENT = ROOT / "src" / "content"
GROUP_POSTS_FILE = ROOT / "fb_group_archive" / "posts.json"
GROUP_EVENTS_FILE = ROOT / "fb_group_archive" / "group_events.json"


SLIDER_ITEMS = [
    ("cfs-image-0169", "2014.10.18", "浦和防災マッピングパーティー", "地域を歩き、防災に必要な情報を地図へ記録した活動です。", "2014.10.18"),
    ("cfs-image-0001", "2015.01.16", "さいたま市オープンデータ・アイデアソン", "公共データを地域課題の解決に生かすアイデアを参加者で検討しました。", "2015.01.16"),
    ("cfs-image-0005", "2015.01.16", "ワークショップ会場の記録", "参加者が集まり、意見を交わしている様子です。", "2015.01.16"),
    ("cfs-image-0010", "2015.01.16", "グループ作業の様子", "机を囲んで話し合いながら作業を進める場面です。", "2015.01.16"),
    ("cfs-image-0016", "2015.01.16", "発表・共有の場面", "活動の途中で考えを共有している記録です。", "2015.01.16"),
    ("cfs-image-0021", "2015.01.16", "参加者による検討の記録", "地域やデータについて、参加者が検討している様子です。", "2015.01.16"),
    ("cfs-image-0024", "2015.01.31", "オープンデータハッカソンの記録", "アイデアを具体化するため、参加者が手を動かした活動の記録です。", "2015.01.31"),
    ("cfs-image-0028", "2015.01.31", "ハッカソン会場の作業風景", "チームごとに作業を進めている場面です。", "2015.01.31"),
    ("cfs-image-0031", "2015.01.31", "資料を見ながら進める活動", "参加者が資料や画面を確認しながら進めている記録です。", "2015.01.31"),
    ("cfs-image-0035", "2015.01.31", "成果共有の様子", "活動の成果や考えを共有する場面です。", "2015.01.31"),
    ("cfs-image-0040", "2015.01.31", "会場全体の雰囲気", "イベント会場の空気感が伝わる写真です。", "2015.01.31"),
    ("cfs-image-0046", "2015.09.05", "オープンデータアイデアソン2015", "地域を見つめ、データを使った解決策を考えた活動の記録です。", "2015.09.05"),
    ("cfs-image-0059", "2015.11.08", "マッピングパーティに関する資料共有", "地図づくりの知見を共有する資料写真です。", ""),
    ("cfs-image-0060", "2015.11.08", "地図づくりに関する資料", "活動内容を説明するための資料写真です。", ""),
    ("cfs-image-0062", "2015.11.08", "マッピング活動の説明資料", "地図づくりの考え方を共有している記録です。", ""),
    ("cfs-image-0212", "2015.12.12", "第2回オープンデータアイデアソン", "参加者が地域課題とデータ活用のアイデアを共有しました。", "2015.12.12"),
    ("cfs-image-0214", "2015.12.12", "グループでの検討風景", "机を囲み、意見を整理している様子です。", "2015.12.12"),
    ("cfs-image-0216", "2016.01.16", "第2回オープンデータハッカソン", "アイデアソンの成果をもとに、チームで具体化を進めました。", "2016.01.16"),
    ("cfs-image-0218", "2016.01.16", "参加者による作業風景", "会場で参加者が手を動かしている記録です。", "2016.01.16"),
    ("cfs-image-0222", "2016.03.05", "オープンデータデイ関連の活動記録", "各地の活動と呼応しながら、埼玉でオープンデータに取り組んだ記録です。", "2016.03.05"),
    ("cfs-image-0225", "2016.04.03", "街を歩いて記録する活動", "地域を歩きながら情報を確認する活動の記録です。", "2016.04.03"),
    ("cfs-image-0067", "2016.07.16", "主題図・オープンデータワークショップ", "関心ごとをもとにチームを作り、地域課題を地図とデータで整理しました。", "2016.07.16"),
    ("cfs-image-0066", "2016.07.16", "ワークショップの検討風景", "参加者がテーマごとに考えをまとめている様子です。", "2016.07.16"),
    ("cfs-image-0068", "2016.07.16", "会場での共有風景", "話し合った内容を共有している場面です。", "2016.07.16"),
    ("cfs-image-0079", "2016.07.30", "地域テーマの作業記録", "参加者がテーマに沿って作業を進めている記録です。", "2016.07.30"),
    ("cfs-image-0080", "2016.07.30", "チーム作業の様子", "会場でチームごとに検討している場面です。", "2016.07.30"),
    ("cfs-image-0081", "2016.07.30", "発表に向けた準備風景", "資料や意見を整理している活動の記録です。", "2016.07.30"),
    ("cfs-image-0095", "2016.09.22", "アーバンデータチャレンジ2016埼玉", "地域データを使い、発表に向けて資料やアイデアをまとめました。", "2016.09.22"),
    ("cfs-image-0096", "2016.09.22", "検討内容の共有場面", "参加者が検討した内容を共有している記録です。", "2016.09.22"),
    ("cfs-image-0107", "2017.03.04", "オープンデータデイでの記念写真", "参加者が集まり、成果や活動を共有した場面です。", "2017.03.04"),
    ("cfs-image-0111", "2017", "活動会場の雰囲気", "イベントと直接結びつけず、活動の雰囲気を伝える写真として掲載しています。", ""),
    ("cfs-image-0115", "2017", "参加者が集う場面", "会場で人が集まり、交流している雰囲気がわかる写真です。", ""),
    ("cfs-image-0122", "2019.03.03", "車いす街歩きマッピングパーティー", "街を歩く前に、参加者でマッピング方法を共有しました。", "2019.03.03"),
    ("cfs-image-0126", "2019.04.07", "地図を使った活動記録", "地図や地域情報を扱う活動の様子です。", "2019.04.07"),
    ("cfs-image-0127", "2019.04.07", "地域情報を確認する場面", "参加者が情報を確認しながら活動している記録です。", "2019.04.07"),
    ("cfs-image-0136", "2020.01.29", "交流・勉強会の記録", "参加者が集まり、知見を共有している場面です。", "2020.01.29"),
    ("cfs-image-0149", "2020.07.11", "オンライン期の活動記録", "状況に合わせて活動を続けた時期の記録です。", "2020.07.11"),
    ("cfs-image-0160", "2020.08.01", "オンラインを交えた活動記録", "社会状況に合わせながら活動を継続した時期の記録です。", "2020.08.01"),
    ("cfs-image-0165", "2021.11.09", "UDC2021埼玉ミートアップ", "オンラインを活用し、地域課題とデータ活用について情報共有しました。", "2021.11.09"),
]

TOP_SLIDE_IDS = {
    "cfs-image-0169", "cfs-image-0001", "cfs-image-0024", "cfs-image-0046",
    "cfs-image-0212", "cfs-image-0216", "cfs-image-0222", "cfs-image-0067",
    "cfs-image-0095", "cfs-image-0107", "cfs-image-0122", "cfs-image-0165",
}


def frontmatter(data):
    lines = ["---"]
    for key, value in data.items():
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.append("---")
    return "\n".join(lines)


def md_body(text):
    text = re.sub(r"https?://[^\s]*(?:zoom\.us|discord\.gg)[^\s]*", "", str(text or ""), flags=re.I)
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "", text)
    text = re.sub(r"(?<![\d/])(?:\+81[- ]?|0\d{1,4}[- ]\d{1,4}[- ]\d{3,4})(?!\d)", "", text)
    text = re.sub(r"(?:ミーティングID|Meeting ID|パスワード|Passcode)[：:]\s*[A-Za-z0-9 -]{3,30}", "", text, flags=re.I)
    lines = [line.strip() for line in archive.clean(text).splitlines()]
    lines = [line for line in lines if not re.search(r"(?:E-?mail|メール|TEL|FAX|電話番号|連絡先|問い合わせ先|ミーティングID|Meeting ID|パスワード|Passcode)", line, re.I)]
    lines = [line for line in lines if not re.match(r"^(?:【招待リンク】|※?zoomのURLはこちらです|Zoomミーティングに参加する|場所[：:]?)$", line, re.I)]
    parts = []
    paragraph = []
    schedule = []

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            parts.append("\n".join(paragraph))
            paragraph = []

    def flush_schedule():
        nonlocal schedule
        if schedule:
            parts.extend(f"- {line}" for line in schedule)
            schedule = []

    for line in lines:
        if not line:
            flush_paragraph()
            flush_schedule()
            continue
        is_heading = line.startswith("■") or (line.startswith("【") and line.endswith("】"))
        is_schedule = bool(re.match(r"^\d{1,2}[:：]\d{2}[-－〜~]", line)) or bool(re.match(r"^\d{1,2}時", line))
        if is_heading:
            flush_paragraph()
            flush_schedule()
            parts.append(f"## {line.strip('■')}")
        elif is_schedule:
            flush_paragraph()
            schedule.append(line)
        else:
            flush_schedule()
            paragraph.append(line)
    flush_paragraph()
    flush_schedule()
    return "\n\n".join(parts).strip()


def write_markdown(path, data, body=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = f"{frontmatter(data)}\n"
    if body.strip():
        content += f"\n{body.strip()}\n"
    path.write_text(content, encoding="utf-8")


def normalize_match_text(value):
    value = str(value or "").lower()
    value = re.sub(r"第[0-9０-９]+回", "", value)
    return re.sub(r"[\s　【】\[\]（）()「」『』・:：!！?？☆★♪●〜~\-－]", "", value)


def load_public_group_posts():
    # posts.json はレビュー済みの公開対象だけを保持する。
    return json.loads(GROUP_POSTS_FILE.read_text(encoding="utf-8"))


def related_group_post_ids(title, event_date, posts, event_ids=()):
    normalized_title = normalize_match_text(title)
    event_day = dt.date.fromisoformat(event_date.replace(".", "-"))
    event_ids = {str(event_id) for event_id in event_ids if event_id}
    matches = []
    for post in posts:
        linked_event_ids = {
            str(link.get("event_id", ""))
            for link in post.get("fb_event_links", [])
        }
        explicit_match = bool(event_ids & linked_event_ids)
        title_match = (
            len(normalized_title) >= 8
            and normalized_title in normalize_match_text(post.get("text", ""))
            and abs((dt.date.fromisoformat(post["date"]) - event_day).days) <= 60
        )
        if explicit_match or title_match:
            matches.append(str(post["id"]))
    return list(dict.fromkeys(matches))


def matching_group_event(title, event_date, group_events):
    normalized_title = normalize_match_text(title)
    event_day = dt.date.fromisoformat(event_date.replace(".", "-"))
    candidates = []
    for event in group_events:
        if not event.get("date"):
            continue
        group_day = dt.date.fromisoformat(event["date"])
        if abs((group_day - event_day).days) > 7:
            continue
        candidate_title = normalize_match_text(event.get("title", ""))
        overlap = normalized_title in candidate_title or candidate_title in normalized_title
        if overlap and min(len(normalized_title), len(candidate_title)) >= 8:
            candidates.append((abs((group_day - event_day).days), -min(len(normalized_title), len(candidate_title)), event))
    return sorted(candidates, key=lambda item: (item[0], item[1]))[0][2] if candidates else None


def main():
    events, images, by_id = archive.build_data()
    group_posts = load_public_group_posts()
    group_events = json.loads(GROUP_EVENTS_FILE.read_text(encoding="utf-8")) if GROUP_EVENTS_FILE.exists() else []
    integrated_notes = {
        note["integrated_page"]: note
        for note in archive.SUPPLEMENTAL_TIMELINE
        if note.get("integrated_page")
    }
    for dirname in ("events", "notes", "slides"):
        target = CONTENT / dirname
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)

    for event in events:
        stem = pathlib.Path(event["page"]).stem
        group_event = matching_group_event(event["name"], event["date"], group_events)
        event_ids = [event.get("fbid", "")]
        if group_event:
            event_ids.append(group_event.get("event_id", ""))
        group_post_ids = related_group_post_ids(event["name"], event["date"], group_posts, event_ids)
        related_group_posts = [post for post in group_posts if str(post["id"]) in group_post_ids]
        integrated_note = integrated_notes.get(event["page"])
        sources = ["facebook-page"]
        if group_post_ids or group_event:
            sources.append("facebook-group")
        if integrated_note:
            sources.append("deep-research")
        group_media = []
        for post in related_group_posts:
            group_media.extend(post.get("saved_images", []))
            for comment in post.get("comments", []):
                group_media.extend(comment.get("saved_images", []))
        if group_event:
            group_media.extend(group_event.get("saved_images", []))
        group_media_urls = [f"/group-media/{item.removeprefix('images/')}" for item in dict.fromkeys(group_media)]
        data = {
            "title": event["name"],
            "eventId": event["id"],
            "date": event["date"],
            "start": event["start"],
            "end": event["end"],
            "sort": event["sort"],
            "place": event["place"],
            "themes": [label for _, label in event["themes"]],
            "themeKeys": [key for key, _ in event["themes"]],
            "page": event["page"],
            "image": event["image"],
            "images": [row["webp_asset_path"] for row in event["images"]] + group_media_urls,
            "fbid": event["fbid"] or (group_event.get("event_id", "") if group_event else ""),
            "groupEventId": group_event.get("event_id", "") if group_event else "",
            "sources": sources,
            "groupPostIds": group_post_ids,
            "hasDetail": event["has_detail"] or bool(group_post_ids) or bool(integrated_note),
        }
        body = md_body(event["description"])
        if related_group_posts:
            group_notes = []
            for post in related_group_posts:
                post_summary = post.get("summary") or post.get("text") or ""
                comment_summary = post.get("comments_summary") or ""
                note = post_summary
                if comment_summary and comment_summary not in post_summary:
                    note = f"{note} コメントでは、{comment_summary}".strip()
                comment_count = len(post.get("comments", []))
                comment_note = f"（コメント{comment_count}件を要約）" if comment_count else ""
                group_notes.append(f"- {post['date']}{comment_note}: {note}")
            body = f"{body}\n\n## Facebookグループでの記録\n\n" + "\n".join(group_notes)
        if group_event and group_event.get("description") and normalize_match_text(group_event["description"]) not in normalize_match_text(body):
            body = f"{body}\n\n## Facebookグループイベント補足\n\n{group_event['description']}".strip()
        if integrated_note:
            body = f"{body}\n\n## DeepResearch補足\n\n{integrated_note['text']}".strip()
        write_markdown(CONTENT / "events" / f"{stem}.md", data, body)

    for idx, note in enumerate(archive.SUPPLEMENTAL_TIMELINE, start=1):
        if note.get("integrated_page"):
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", note["title"].lower()).strip("-") or f"note-{idx:02d}"
        data = {
            "title": note["title"],
            "date": note["date"],
            "sort": note["sort"],
            "theme": note["theme"],
            "source": "DeepResearch",
            "sources": ["deep-research"],
        }
        write_markdown(CONTENT / "notes" / f"{idx:02d}-{slug}.md", data, note["text"])

    top_slider_items = [item for item in SLIDER_ITEMS if item[0] in TOP_SLIDE_IDS]
    for idx, (asset_id, date, caption, text, event_date) in enumerate(top_slider_items, start=1):
        if asset_id not in by_id:
            continue
        data = {
            "assetId": asset_id,
            "date": date,
            "caption": caption,
            "text": text,
            "eventDate": event_date,
            "sort": idx,
        }
        write_markdown(CONTENT / "slides" / f"{idx:02d}-{asset_id}.md", data)

    note_count = sum(1 for note in archive.SUPPLEMENTAL_TIMELINE if not note.get("integrated_page"))
    print(f"events={len(events)} notes={note_count} slides={len(top_slider_items)} images={len(images)} group_posts={len(group_posts)}")


if __name__ == "__main__":
    main()
