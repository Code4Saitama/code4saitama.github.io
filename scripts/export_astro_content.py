#!/usr/bin/env python3
import json
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_archive_site as archive  # noqa: E402

CONTENT = ROOT / "src" / "content"


SLIDER_ITEMS = [
    ("cfs-image-0169", "2014.10.18", "まち歩き型マッピングの集合風景", "地域を歩き、情報を記録する活動の入口となる場面です。", "2014.10.18"),
    ("cfs-image-0001", "2015.01.16", "オープンデータをテーマにしたワークショップの記録", "アイデアを出し合い、公共データの活用を考える場の記録です。", "2015.01.16"),
    ("cfs-image-0005", "2015.01.16", "ワークショップ会場の記録", "参加者が集まり、意見を交わしている様子です。", "2015.01.16"),
    ("cfs-image-0010", "2015.01.16", "グループ作業の様子", "机を囲んで話し合いながら作業を進める場面です。", "2015.01.16"),
    ("cfs-image-0016", "2015.01.16", "発表・共有の場面", "活動の途中で考えを共有している記録です。", "2015.01.16"),
    ("cfs-image-0021", "2015.01.16", "参加者による検討の記録", "地域やデータについて、参加者が検討している様子です。", "2015.01.16"),
    ("cfs-image-0024", "2015.01.31", "オープンデータハッカソンの記録", "アイデアを具体化するため、参加者が手を動かした活動の記録です。", "2015.01.31"),
    ("cfs-image-0028", "2015.01.31", "ハッカソン会場の作業風景", "チームごとに作業を進めている場面です。", "2015.01.31"),
    ("cfs-image-0031", "2015.01.31", "資料を見ながら進める活動", "参加者が資料や画面を確認しながら進めている記録です。", "2015.01.31"),
    ("cfs-image-0035", "2015.01.31", "成果共有の様子", "活動の成果や考えを共有する場面です。", "2015.01.31"),
    ("cfs-image-0040", "2015.01.31", "会場全体の雰囲気", "イベント会場の空気感が伝わる写真です。", "2015.01.31"),
    ("cfs-image-0046", "2015.09.05", "街歩きに関する活動記録", "地域を実際に見ながら情報を集める活動の記録です。", "2015.09.05"),
    ("cfs-image-0059", "2015.11.08", "マッピングパーティに関する資料共有", "地図づくりの知見を共有する資料写真です。", ""),
    ("cfs-image-0060", "2015.11.08", "地図づくりに関する資料", "活動内容を説明するための資料写真です。", ""),
    ("cfs-image-0062", "2015.11.08", "マッピング活動の説明資料", "地図づくりの考え方を共有している記録です。", ""),
    ("cfs-image-0212", "2015.12.12", "アイデア共有の場面", "参加者が地域課題やアイデアについて話し合う場面です。", "2015.12.12"),
    ("cfs-image-0214", "2015.12.12", "グループでの検討風景", "机を囲み、意見を整理している様子です。", "2015.12.12"),
    ("cfs-image-0216", "2016.01.16", "地域課題を考える活動記録", "テーマに沿って考えを出し合う場面です。", "2016.01.16"),
    ("cfs-image-0218", "2016.01.16", "参加者による作業風景", "会場で参加者が手を動かしている記録です。", "2016.01.16"),
    ("cfs-image-0222", "2016.03.05", "オープンデータデイ関連の活動記録", "各地の活動と呼応しながら、埼玉でオープンデータに取り組んだ記録です。", "2016.03.05"),
    ("cfs-image-0225", "2016.04.03", "街を歩いて記録する活動", "地域を歩きながら情報を確認する活動の記録です。", "2016.04.03"),
    ("cfs-image-0067", "2016.07.16", "地域課題を考えるワークショップの様子", "関心ごとをもとにチームを作り、地域課題を整理する場面です。", "2016.07.16"),
    ("cfs-image-0066", "2016.07.16", "ワークショップの検討風景", "参加者がテーマごとに考えをまとめている様子です。", "2016.07.16"),
    ("cfs-image-0068", "2016.07.16", "会場での共有風景", "話し合った内容を共有している場面です。", "2016.07.16"),
    ("cfs-image-0079", "2016.07.30", "地域テーマの作業記録", "参加者がテーマに沿って作業を進めている記録です。", "2016.07.30"),
    ("cfs-image-0080", "2016.07.30", "チーム作業の様子", "会場でチームごとに検討している場面です。", "2016.07.30"),
    ("cfs-image-0081", "2016.07.30", "発表に向けた準備風景", "資料や意見を整理している活動の記録です。", "2016.07.30"),
    ("cfs-image-0095", "2016.09.22", "データを使った作業風景", "発表に向けて資料やアイデアをまとめる活動の様子です。", "2016.09.22"),
    ("cfs-image-0096", "2016.09.22", "検討内容の共有場面", "参加者が検討した内容を共有している記録です。", "2016.09.22"),
    ("cfs-image-0107", "2017.03.04", "オープンデータデイでの記念写真", "参加者が集まり、成果や活動を共有した場面です。", "2017.03.04"),
    ("cfs-image-0111", "2017", "活動会場の雰囲気", "イベントと直接結びつけず、活動の雰囲気を伝える写真として掲載しています。", ""),
    ("cfs-image-0115", "2017", "参加者が集う場面", "会場で人が集まり、交流している雰囲気がわかる写真です。", ""),
    ("cfs-image-0122", "2019.03.03", "マッピング方法を共有する場面", "参加者にマッピングの進め方を説明している記録です。", "2019.03.03"),
    ("cfs-image-0126", "2019.04.07", "地図を使った活動記録", "地図や地域情報を扱う活動の様子です。", "2019.04.07"),
    ("cfs-image-0127", "2019.04.07", "地域情報を確認する場面", "参加者が情報を確認しながら活動している記録です。", "2019.04.07"),
    ("cfs-image-0136", "2020.01.29", "交流・勉強会の記録", "参加者が集まり、知見を共有している場面です。", "2020.01.29"),
    ("cfs-image-0149", "2020.07.11", "オンライン期の活動記録", "状況に合わせて活動を続けた時期の記録です。", "2020.07.11"),
    ("cfs-image-0160", "2020.08.01", "オンラインを交えた活動記録", "社会状況に合わせながら活動を継続した時期の記録です。", "2020.08.01"),
    ("cfs-image-0165", "2021.11.09", "オンラインでの共有活動", "オンラインを活用して情報共有を行った時期の記録です。", "2021.11.09"),
]


def frontmatter(data):
    lines = ["---"]
    for key, value in data.items():
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.append("---")
    return "\n".join(lines)


def md_body(text):
    lines = [line.strip() for line in archive.clean(text).splitlines()]
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
    content = f"{frontmatter(data)}\n\n{body.strip()}\n"
    path.write_text(content, encoding="utf-8")


def main():
    events, images, by_id = archive.build_data()
    for dirname in ("events", "notes", "slides"):
        target = CONTENT / dirname
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)

    for event in events:
        stem = pathlib.Path(event["page"]).stem
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
            "images": [row["webp_asset_path"] for row in event["images"]],
            "fbid": event["fbid"],
            "hasDetail": event["has_detail"],
        }
        write_markdown(CONTENT / "events" / f"{stem}.md", data, md_body(event["description"]))

    for idx, note in enumerate(archive.SUPPLEMENTAL_TIMELINE, start=1):
        slug = re.sub(r"[^a-z0-9]+", "-", note["title"].lower()).strip("-") or f"note-{idx:02d}"
        data = {
            "title": note["title"],
            "date": note["date"],
            "sort": note["sort"],
            "theme": note["theme"],
            "source": "関連資料",
        }
        write_markdown(CONTENT / "notes" / f"{idx:02d}-{slug}.md", data, note["text"])

    for idx, (asset_id, date, caption, text, event_date) in enumerate(SLIDER_ITEMS, start=1):
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

    print(f"events={len(events)} notes={len(archive.SUPPLEMENTAL_TIMELINE)} slides={len(SLIDER_ITEMS)} images={len(images)}")


if __name__ == "__main__":
    main()
