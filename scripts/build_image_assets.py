#!/usr/bin/env python3
import csv
import datetime as dt
import json
import pathlib
import re
import shutil
import subprocess


ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "facebook-export"
SITE = ROOT / "archive-site"
MEDIA_DIR = DATA / "this_profile's_activity_across_facebook/posts/media"
OUT_DIR = SITE / "assets" / "images"
ORIGINAL_DIR = OUT_DIR / "original"
WEBP_DIR = OUT_DIR / "webp"


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


def ts(value):
    if not value:
        return ""
    try:
        return dt.datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M")
    except (TypeError, ValueError, OSError):
        return ""


def clean(value, limit=None):
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(value) > limit:
        return value[: limit - 1] + "…"
    return value


def rel(path):
    return path.relative_to(ROOT).as_posix()


def data_rel(path):
    return path.relative_to(DATA).as_posix()


def site_rel(path):
    return path.relative_to(SITE).as_posix()


def fb_export_path(value):
    value = str(value or "")
    if value.startswith(("this_profile's_activity_across_facebook/", "profile_information/", "connections/")):
        return f"data/facebook-export/{value}"
    return value


def add_ref(refs, uri, source_type, source_title="", source_date="", description="", source_file=""):
    if not uri:
        return
    refs.setdefault(uri, []).append(
        {
            "source_type": source_type,
            "source_title": clean(source_title),
            "source_date": source_date,
            "description": clean(description),
            "source_file": source_file,
        }
    )


def collect_refs():
    refs = {}

    album_dir = DATA / "this_profile's_activity_across_facebook/posts/album"
    for path in sorted(album_dir.glob("*.json")):
        source_file = data_rel(path)
        source_display_file = fb_export_path(source_file)
        album = load_json(source_file)
        album_name = album.get("name", "")
        album_description = album.get("description", "")
        cover = album.get("cover_photo", {})
        add_ref(refs, cover.get("uri"), "album_cover", album_name, ts(cover.get("creation_timestamp")), cover.get("title") or album_description, source_display_file)
        for photo in album.get("photos", []):
            add_ref(
                refs,
                photo.get("uri"),
                "album_photo",
                album_name,
                ts(photo.get("creation_timestamp")),
                photo.get("title") or album_description,
                source_display_file,
            )

    uncategorized = load_json("this_profile's_activity_across_facebook/posts/uncategorized_photos.json").get("other_photos_v2", [])
    for photo in uncategorized:
        add_ref(
            refs,
            photo.get("uri"),
            "uncategorized_photo",
            "未分類写真",
            ts(photo.get("creation_timestamp")),
            photo.get("description", ""),
            "data/facebook-export/this_profile's_activity_across_facebook/posts/uncategorized_photos.json",
        )

    posts = load_json("this_profile's_activity_across_facebook/posts/profile_posts_1.json")
    for post in posts:
        text = "\n\n".join(d.get("post", "") for d in post.get("data", []) if d.get("post"))
        for attachment in post.get("attachments", []):
            for data in attachment.get("data", []):
                media = data.get("media", {})
                add_ref(
                    refs,
                    media.get("uri"),
                    "post_attachment",
                    post.get("title", ""),
                    ts(post.get("timestamp")),
                    text or media.get("title", ""),
                    "data/facebook-export/this_profile's_activity_across_facebook/posts/profile_posts_1.json",
                )

    updates = load_json("profile_information/profile_information/profile_update_history.json").get("profile_updates_v2", [])
    for update in updates:
        for attachment in update.get("attachments", []):
            for data in attachment.get("data", []):
                media = data.get("media", {})
                add_ref(
                    refs,
                    media.get("uri"),
                    "profile_update",
                    update.get("title", ""),
                    ts(update.get("timestamp")),
                    media.get("title", ""),
                    "data/facebook-export/profile_information/profile_information/profile_update_history.json",
                )

    return refs


def image_dimensions(path):
    try:
        result = subprocess.run(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return "", ""
    width = height = ""
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("pixelWidth:"):
            width = line.split(":", 1)[1].strip()
        elif line.startswith("pixelHeight:"):
            height = line.split(":", 1)[1].strip()
    return width, height


def convert_webp(src, dest):
    result = subprocess.run(
        ["cwebp", "-quiet", "-q", "82", str(src), "-o", str(dest)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False, result.stderr.strip() or result.stdout.strip()
    return True, ""


def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return lines


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ORIGINAL_DIR.mkdir(parents=True, exist_ok=True)
    WEBP_DIR.mkdir(parents=True, exist_ok=True)

    refs = collect_refs()
    source_images = sorted(
        path
        for path in MEDIA_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )

    manifest = []
    for index, src in enumerate(source_images, start=1):
        asset_id = f"cfs-image-{index:04d}"
        original_dest = ORIGINAL_DIR / f"{asset_id}{src.suffix.lower()}"
        webp_dest = WEBP_DIR / f"{asset_id}.webp"
        shutil.copy2(src, original_dest)
        ok, error = convert_webp(original_dest, webp_dest)
        width, height = image_dimensions(original_dest)
        uri = data_rel(src)
        source_refs = refs.get(uri, [])
        first_ref = source_refs[0] if source_refs else {}
        manifest.append(
            {
                "asset_id": asset_id,
                "original_backup_path": f"data/facebook-export/{uri}",
                "original_asset_path": site_rel(original_dest),
                "webp_asset_path": site_rel(webp_dest) if ok else "",
                "webp_status": "ok" if ok else f"failed: {error}",
                "width": width,
                "height": height,
                "source_type": first_ref.get("source_type", "unreferenced_media_file"),
                "source_title": first_ref.get("source_title", ""),
                "source_date": first_ref.get("source_date", ""),
                "description": clean(first_ref.get("description", ""), 180),
                "reference_count": len(source_refs),
                "all_references": source_refs,
            }
        )

    (OUT_DIR / "images-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    with (OUT_DIR / "images-manifest.csv").open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "asset_id",
            "original_backup_path",
            "original_asset_path",
            "webp_asset_path",
            "webp_status",
            "width",
            "height",
            "source_type",
            "source_title",
            "source_date",
            "description",
            "reference_count",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in manifest:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

    by_type = {}
    for row in manifest:
        by_type[row["source_type"]] = by_type.get(row["source_type"], 0) + 1
    failed = [row for row in manifest if row["webp_status"] != "ok"]
    table_rows = [
        (
            row["asset_id"],
            row["source_date"],
            row["source_type"],
            row["source_title"],
            row["width"],
            row["height"],
            row["original_asset_path"],
            row["webp_asset_path"],
            row["description"],
        )
        for row in manifest
    ]
    md_lines = [
        "# 画像素材一覧",
        "",
        "Facebookバックアップ内の画像を、アーカイブサイト用素材として `original/` にコピーし、`webp/` にWebP変換した一覧です。",
        "",
        "## 概要",
        "",
        f"- 元画像数: {len(source_images)}件",
        f"- WebP変換成功: {len(manifest) - len(failed)}件",
        f"- WebP変換失敗: {len(failed)}件",
        "- WebP品質設定: `cwebp -q 82`",
        "",
        "## 種類別件数",
        "",
        *md_table(["種類", "件数"], sorted(by_type.items())),
        "",
        "## ファイル",
        "",
        "- JSON: `archive-site/assets/images/images-manifest.json`",
        "- CSV: `archive-site/assets/images/images-manifest.csv`",
        "- 元画像コピー: `archive-site/assets/images/original/`",
        "- WebP画像: `archive-site/assets/images/webp/`",
        "",
        "## 一覧",
        "",
        *md_table(
            ["ID", "日付", "種別", "由来", "幅", "高さ", "元画像", "WebP", "説明"],
            table_rows,
        ),
    ]
    if failed:
        md_lines.extend(["", "## 変換失敗", ""])
        md_lines.extend(md_table(["ID", "元画像", "状態"], [(row["asset_id"], row["original_backup_path"], row["webp_status"]) for row in failed]))

    (OUT_DIR / "images-manifest.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(OUT_DIR / "images-manifest.md")
    print(f"images={len(source_images)} webp_ok={len(manifest) - len(failed)} webp_failed={len(failed)}")


if __name__ == "__main__":
    main()
