#!/usr/bin/env python3
import datetime as dt
import json
import pathlib
import re
from collections import Counter, defaultdict


ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "facebook-export"
DOCS = ROOT / "docs"
OUT_DIR = DOCS / "non-event"


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
        fmt = "%Y-%m-%d" if date else "%Y-%m-%d %H:%M"
        return dt.datetime.fromtimestamp(value).strftime(fmt)
    except (TypeError, ValueError, OSError):
        return ""


def clean(value):
    if not value:
        return ""
    return re.sub(r"\n{3,}", "\n\n", str(value).replace("\r\n", "\n")).strip()


def one_line(value, limit=140):
    value = re.sub(r"\s+", " ", clean(value))
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def esc(value):
    value = fb_export_path(value)
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def fb_export_path(value):
    value = str(value or "")
    if value.startswith(("this_profile's_activity_across_facebook/", "profile_information/", "connections/")):
        return f"data/facebook-export/{value}"
    return value


def label_map(item):
    result = {}
    for entry in item.get("label_values", []):
        label = entry.get("label", "")
        if not label:
            continue
        value = entry.get("value")
        if value is None and entry.get("href"):
            value = entry.get("href")
        if value is None and entry.get("dict"):
            value = "; ".join(
                f"{sub.get('label', '')}: {sub.get('value', '')}".strip(": ")
                for sub in entry.get("dict", [])
            )
        result[label] = value
    return result


def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(esc(cell) for cell in row) + " |")
    return lines


def write_doc(filename, title, body):
    path = OUT_DIR / filename
    path.write_text(f"# {title}\n\n" + "\n".join(body).rstrip() + "\n", encoding="utf-8")
    return path


def json_inventory():
    rows = []
    for path in sorted(DATA.rglob("*.json")):
        rel = path.relative_to(DATA).as_posix()
        try:
            data = load_json(rel)
        except Exception as exc:
            rows.append((rel, "読み込みエラー", str(exc)))
            continue
        if isinstance(data, list):
            summary = f"list: {len(data)}件"
        elif isinstance(data, dict):
            arrs = [f"{key}: {len(value)}件" for key, value in data.items() if isinstance(value, list)]
            summary = "dict"
            if arrs:
                summary += " / " + ", ".join(arrs)
        else:
            summary = type(data).__name__
        rows.append((rel, summary, ""))
    return rows


def profile_doc():
    profile = load_json("profile_information/profile_information/profile_information.json").get("profile_v2", {})
    contact = label_map(load_json("profile_information/profile_information/contact_info.json"))
    websites = label_map(load_json("profile_information/profile_information/websites.json"))
    predicted = label_map(load_json("profile_information/profile_information/predicted_languages.json"))
    sync = load_json("profile_information/profile_information/contacts_sync_settings.json")
    devices = load_json("profile_information/profile_information/your_devices.json")
    updates = load_json("profile_information/profile_information/profile_update_history.json").get("profile_updates_v2", [])

    addr = profile.get("address", {})
    address = " ".join(part for part in [addr.get("region"), addr.get("city"), addr.get("street"), addr.get("zipcode")] if part)
    site_list = ", ".join(site.get("address", "") for site in profile.get("websites", []))

    body = [
        "Code for SAITAMAのプロフィール、連絡先、更新履歴、端末関連情報を整理したファイルです。公開サイトで使える基本情報と、公開前に確認すべき管理系情報を分けています。",
        "",
        "## 公開アーカイブに使いやすい基本情報",
        "",
        *md_table(
            ["項目", "内容"],
            [
                ("名称", profile.get("name", {}).get("full_name", "")),
                ("Facebookページ", profile.get("profile_uri", "")),
                ("ユーザー名", profile.get("username", "")),
                ("Webサイト", site_list),
                ("カテゴリ", profile.get("profile_category", "")),
                ("所在地表記", address),
                ("Facebook登録日", ts(profile.get("registration_timestamp"))),
            ],
        ),
        "",
        "## 連絡先・Web関連",
        "",
        "Facebookエクスポートには連絡先・Webサイト関連の設定項目が含まれます。公開に使う場合は、現在も有効な連絡先か確認が必要です。",
        "",
        *md_table(["項目", "値"], sorted(contact.items()) + sorted(websites.items())),
        "",
        "## 推定言語",
        "",
        *md_table(["項目", "値"], sorted(predicted.items())),
        "",
        "## プロフィール更新履歴",
        "",
        f"- 更新履歴件数: {len(updates)}件",
        f"- 記録期間: {ts(min((u.get('timestamp') for u in updates if u.get('timestamp')), default=None), True)}〜{ts(max((u.get('timestamp') for u in updates if u.get('timestamp')), default=None), True)}",
        "",
        *md_table(
            ["日時", "内容", "関連メディア"],
            [
                (
                    ts(item.get("timestamp")),
                    item.get("title", ""),
                    ", ".join(
                        data.get("media", {}).get("uri", "")
                        for att in item.get("attachments", [])
                        for data in att.get("data", [])
                        if data.get("media", {}).get("uri")
                    ),
                )
                for item in updates
            ],
        ),
        "",
        "## 端末・同期設定",
        "",
        f"- 連絡先同期設定レコード: {len(sync)}件",
        f"- プロフィール情報側の端末レコード: {len(devices)}件",
        "",
        "これらはアーカイブサイトの公開情報としては原則不要です。管理履歴の確認やバックアップ完全性の確認用途に留めるのがよさそうです。",
    ]
    return write_doc("01-profile-and-identity.md", "プロフィール・基本情報", body)


def posts_doc():
    posts = load_json("this_profile's_activity_across_facebook/posts/profile_posts_1.json")
    post_rows = []
    type_counts = Counter()
    link_rows = []
    media_rows = []
    for post in sorted(posts, key=lambda p: p.get("timestamp", 0), reverse=True):
        title = post.get("title", "")
        text = "\n\n".join(clean(d.get("post", "")) for d in post.get("data", []) if d.get("post"))
        kind = "投稿"
        if "写真" in title:
            kind = "写真"
        elif "リンク" in title:
            kind = "リンク"
        elif "イベント" in title:
            kind = "イベント共有"
        elif "シェア" in title:
            kind = "シェア"
        type_counts[kind] += 1
        urls = []
        media = []
        shared_events = []
        for att in post.get("attachments", []):
            for data in att.get("data", []):
                url = data.get("external_context", {}).get("url")
                if url:
                    urls.append(url)
                if data.get("media", {}).get("uri"):
                    media.append(data["media"]["uri"])
                if data.get("event", {}).get("name"):
                    shared_events.append(data["event"]["name"])
        post_rows.append((ts(post.get("timestamp")), kind, title, one_line(text), len(urls), len(media), "; ".join(shared_events)))
        for url in urls:
            link_rows.append((ts(post.get("timestamp")), title, url, one_line(text)))
        for item in media:
            media_rows.append((ts(post.get("timestamp")), title, item, one_line(text)))

    body = [
        "ページ投稿、リンク共有、写真投稿、イベント共有をイベント以外の観点から整理しています。イベントそのものの詳細は `docs/code-for-saitama-facebook-archive.md` 側に集約済みです。",
        "",
        "## 件数",
        "",
        *md_table(["種類", "件数"], sorted(type_counts.items())),
        "",
        "## 投稿一覧",
        "",
        *md_table(["日時", "種類", "タイトル", "本文概要", "URL数", "画像数", "共有イベント"], post_rows),
        "",
        "## 共有リンク一覧",
        "",
        *md_table(["日時", "投稿タイトル", "URL", "本文概要"], link_rows),
        "",
        "## 投稿に紐づく画像",
        "",
        *md_table(["日時", "投稿タイトル", "画像パス", "本文概要"], media_rows),
    ]
    return write_doc("02-posts-links-and-shares.md", "投稿・リンク・シェア", body)


def photos_doc():
    albums = []
    photo_rows = []
    for path in sorted((DATA / "this_profile's_activity_across_facebook/posts/album").glob("*.json")):
        rel = path.relative_to(DATA).as_posix()
        album = load_json(rel)
        photos = album.get("photos", [])
        albums.append(
            (
                path.stem,
                album.get("name", ""),
                len(photos),
                ts(album.get("last_modified_timestamp")),
                one_line(album.get("description", ""), 180),
                album.get("cover_photo", {}).get("uri", ""),
            )
        )
        for photo in photos:
            photo_rows.append((album.get("name", ""), ts(photo.get("creation_timestamp")), photo.get("title", ""), photo.get("uri", "")))

    uncategorized = load_json("this_profile's_activity_across_facebook/posts/uncategorized_photos.json").get("other_photos_v2", [])
    uncategorized_rows = [
        (ts(photo.get("creation_timestamp")), photo.get("uri", ""), one_line(photo.get("description", ""), 180))
        for photo in sorted(uncategorized, key=lambda p: p.get("creation_timestamp", 0))
    ]

    image_count = len(list(DATA.rglob("*.jpg"))) + len(list(DATA.rglob("*.jpeg"))) + len(list(DATA.rglob("*.png")))
    body = [
        "写真・アルバムは、活動の雰囲気や成果物を伝えるうえで重要な素材です。EXIFやアップロードIPが含まれる写真メタデータもあるため、公開サイトでは画像本体と説明文を使い、詳細メタデータは公開しない方針が安全です。",
        "",
        "## 全体件数",
        "",
        f"- 画像ファイル数: {image_count}件",
        f"- アルバム数: {len(albums)}件",
        f"- アルバム内写真数: {len(photo_rows)}件",
        f"- 未分類写真数: {len(uncategorized)}件",
        "",
        "## アルバム一覧",
        "",
        *md_table(["ID", "アルバム名", "写真数", "最終更新", "説明概要", "カバー画像"], albums),
        "",
        "## アルバム内写真一覧",
        "",
        *md_table(["アルバム", "作成日時", "タイトル", "画像パス"], photo_rows),
        "",
        "## 未分類写真一覧",
        "",
        *md_table(["作成日時", "画像パス", "説明概要"], uncategorized_rows),
    ]
    return write_doc("03-photos-and-albums.md", "写真・アルバム", body)


def reactions_doc():
    comments = load_json("this_profile's_activity_across_facebook/comments_and_reactions/comments.json").get("comments_v2", [])
    likes_label = load_json("this_profile's_activity_across_facebook/comments_and_reactions/likes_and_reactions.json")
    likes_simple = load_json("this_profile's_activity_across_facebook/comments_and_reactions/likes_and_reactions_1.json")

    comment_rows = [(ts(item.get("timestamp")), item.get("title", "")) for item in comments]
    reaction_rows = []
    reaction_counts = Counter()
    for item in likes_label:
        labels = label_map(item)
        reaction = labels.get("リアクション", "")
        reaction_counts[reaction or "不明"] += 1
        reaction_rows.append((ts(item.get("timestamp")), reaction, labels.get("名前", ""), labels.get("URL", "")))
    simple_counts = Counter()
    simple_rows = []
    for item in likes_simple:
        reaction = ""
        actor = ""
        for data in item.get("data", []):
            if data.get("reaction"):
                reaction = data["reaction"].get("reaction", "")
                actor = data["reaction"].get("actor", "")
        simple_counts[reaction or "不明"] += 1
        simple_rows.append((ts(item.get("timestamp")), reaction, actor, item.get("title", "")))

    body = [
        "コメントとリアクションは、Code for SAITAMAページが他の投稿・写真・ページに対して行った反応の記録です。公開アーカイブでは、個別の相手先よりも、活動領域や関心の広がりを読むための補助資料として扱うのが向いています。",
        "",
        "## コメント",
        "",
        f"- コメント記録: {len(comments)}件",
        "",
        *md_table(["日時", "内容"], comment_rows),
        "",
        "## リアクション件数",
        "",
        *md_table(["リアクション", "件数"], sorted((k, v) for k, v in (reaction_counts + simple_counts).items())),
        "",
        "## リアクション詳細（URL付き）",
        "",
        *md_table(["日時", "リアクション", "対象名", "URL"], reaction_rows),
        "",
        "## リアクション詳細（簡易ログ）",
        "",
        *md_table(["日時", "リアクション", "主体", "タイトル"], simple_rows[:250]),
        "",
        f"簡易ログは全{len(simple_rows)}件あります。上表はMarkdownの可読性を優先して先頭250件に抑えています。完全なデータは `likes_and_reactions_1.json` を参照してください。",
    ]
    return write_doc("04-comments-and-reactions.md", "コメント・リアクション", body)


def connections_doc():
    followers = load_json("connections/followers/people_who_followed_you.json").get("followers_v3", [])
    following = load_json("connections/followers/who_you've_followed.json").get("following_v3", [])
    pages = load_json("this_profile's_activity_across_facebook/pages/pages.json").get("page_likes_v2", [])
    group_membership = load_json("this_profile's_activity_across_facebook/groups/group_membership_activity.json").get("groups_joined_v2", [])
    audiences = label_map(load_json("connections/friends/your_post_audiences.json"))

    follower_rows = [(ts(item.get("timestamp")), item.get("name", ""), item.get("url", "")) for item in followers]
    following_rows = [(ts(item.get("timestamp")), item.get("name", ""), item.get("url", "")) for item in following]
    pages_rows = [(ts(item.get("timestamp")), item.get("name", ""), item.get("url", "")) for item in pages]
    group_rows = [(ts(item.get("timestamp")), item.get("title", ""), item.get("name", "")) for item in group_membership]

    body = [
        "フォロワー、フォロー、ページいいね、グループ参加など、Code for SAITAMAがFacebook上でどのようなネットワークを持っていたかを整理します。個人名が含まれるため、公開時は原則として件数・傾向の紹介に留めることを推奨します。",
        "",
        "## 件数",
        "",
        *md_table(
            ["区分", "件数"],
            [
                ("フォロワー", len(followers)),
                ("フォロー中", len(following)),
                ("いいねしたページ", len(pages)),
                ("グループ参加記録", len(group_membership)),
            ],
        ),
        "",
        "## 投稿オーディエンス設定",
        "",
        *md_table(["項目", "値"], sorted(audiences.items())),
        "",
        "## いいねしたページ",
        "",
        *md_table(["日時", "ページ名", "URL"], pages_rows),
        "",
        "## フォロー中",
        "",
        *md_table(["日時", "名前", "URL"], following_rows),
        "",
        "## フォロワー",
        "",
        "フォロワー一覧には個人名が多数含まれるため、公開アーカイブへの掲載は慎重に扱う必要があります。ここでは完全性確認のため一覧化しています。",
        "",
        *md_table(["日時", "名前", "URL"], follower_rows),
        "",
        "## グループ参加",
        "",
        *md_table(["日時", "タイトル", "名前"], group_rows),
    ]
    return write_doc("05-pages-connections-and-network.md", "ページ・つながり・ネットワーク", body)


def admin_doc():
    admin = label_map(load_json("this_profile's_activity_across_facebook/pages/admin_activity.json"))
    invites = label_map(load_json("this_profile's_activity_across_facebook/pages/sent_page_invites.json"))
    places = label_map(load_json("this_profile's_activity_across_facebook/your_places/cities_you_have_checked_into.json"))
    tagged_places = load_json("this_profile's_activity_across_facebook/posts/places_you_have_been_tagged_in.json")
    nav_shortcuts = load_json("this_profile's_activity_across_facebook/navigation_bar/navigation_bar_shortcut_history.json")
    nav_device = load_json("this_profile's_activity_across_facebook/navigation_bar/device_navigation_bar_information.json")
    nav_tabs = label_map(load_json("this_profile's_activity_across_facebook/navigation_bar/your_tab_notifications.json"))
    gaming_settings = label_map(load_json("this_profile's_activity_across_facebook/facebook_gaming/bookmark_and_app_settings.json"))
    badges = load_json("this_profile's_activity_across_facebook/facebook_gaming/your_page_or_groups_badges.json")
    fund_viewed = label_map(load_json("this_profile's_activity_across_facebook/fundraisers/fundraiser_posts_you_likely_viewed.json"))
    fund_donations = label_map(load_json("this_profile's_activity_across_facebook/fundraisers/your_fundraiser_donations_information.json"))
    editor = load_json("this_profile's_activity_across_facebook/posts/facebook_editor.json")

    shortcut_rows = []
    for item in nav_shortcuts:
        labels = label_map(item)
        shortcut_rows.append((ts(item.get("timestamp")), labels.get("ショートカット", ""), labels.get("アクション", ""), labels.get("プラットフォーム", "")))
    device_rows = []
    for item in nav_device:
        labels = label_map(item)
        device_rows.append((labels.get("デバイス", ""), labels.get("プラットフォーム", ""), labels.get("ショートカット", ""), labels.get("表示順", "")))
    tagged_rows = [(label_map(item).get("場所", ""), label_map(item).get("投稿", ""), item.get("fbid", "")) for item in tagged_places]
    badge_rows = [(label_map(item).get("バッジ", ""), label_map(item).get("グループまたはページ", ""), item.get("fbid", "")) for item in badges]

    body = [
        "ページ管理、ナビゲーションバー、場所、Facebook Gaming、ファンドレイザーなど、活動本文ではない管理・設定系の情報です。アーカイブサイトの公開本文には基本的に不要ですが、バックアップ全体の説明には含めておくと全体像が明確になります。",
        "",
        "## ページ管理",
        "",
        *md_table(["項目", "値"], sorted(admin.items())),
        "",
        "## 送信したページ招待",
        "",
        *md_table(["項目", "値"], sorted(invites.items())),
        "",
        "## Facebook Editor",
        "",
        f"- データ: `{editor}`",
        "",
        "## 場所・タグ付け",
        "",
        *md_table(["項目", "値"], sorted(places.items())),
        "",
        *md_table(["場所", "投稿", "fbid"], tagged_rows),
        "",
        "## ナビゲーションバー",
        "",
        *md_table(["項目", "値"], sorted(nav_tabs.items())),
        "",
        *md_table(["日時", "ショートカット", "アクション", "プラットフォーム"], shortcut_rows),
        "",
        *md_table(["デバイス", "プラットフォーム", "ショートカット", "表示順"], device_rows),
        "",
        "## Facebook Gaming・バッジ",
        "",
        *md_table(["項目", "値"], sorted(gaming_settings.items())),
        "",
        *md_table(["バッジ", "グループまたはページ", "fbid"], badge_rows),
        "",
        "## ファンドレイザー",
        "",
        *md_table(["項目", "値"], sorted(fund_viewed.items()) + sorted(fund_donations.items())),
    ]
    return write_doc("06-admin-settings-and-system-records.md", "管理・設定・システム記録", body)


def messages_doc():
    settings = label_map(load_json("this_profile's_activity_across_facebook/messages/messaging_settings.json"))
    platform = label_map(load_json("this_profile's_activity_across_facebook/messages/messenger_active_status_platform_settings.json"))
    active = label_map(load_json("this_profile's_activity_across_facebook/messages/messenger_active_status_settings.json"))
    install = label_map(load_json("this_profile's_activity_across_facebook/messages/your_messenger_app_install_information.json"))
    devices = load_json("this_profile's_activity_across_facebook/messages/information_about_your_devices.json")

    threads = []
    for path in sorted((DATA / "this_profile's_activity_across_facebook/messages").glob("*/*/message_1.json")):
        rel = path.relative_to(DATA).as_posix()
        data = load_json(rel)
        messages = data.get("messages", [])
        times = [m.get("timestamp_ms", 0) / 1000 for m in messages if m.get("timestamp_ms")]
        category = path.parts[-3]
        threads.append(
            (
                category,
                f"thread-{len(threads) + 1}",
                len(data.get("participants", [])),
                len(messages),
                ts(min(times), True) if times else "",
                ts(max(times), True) if times else "",
                rel,
            )
        )

    category_counts = Counter(row[0] for row in threads)
    body = [
        "Messenger関連の情報です。個人名、本文、端末情報を含む可能性が高いため、公開アーカイブでは本文を掲載しない方針が安全です。このファイルでは、存在するスレッド数、メッセージ数、設定項目、公開可否の判断材料を整理します。",
        "",
        "## スレッド件数",
        "",
        *md_table(["区分", "件数"], sorted(category_counts.items())),
        "",
        "## スレッド一覧（本文非掲載）",
        "",
        *md_table(["区分", "匿名ID", "参加者数", "メッセージ数", "開始日", "終了日", "元ファイル"], threads),
        "",
        "## Messenger設定",
        "",
        *md_table(["項目", "値"], sorted(settings.items())),
        "",
        "## アクティブステータス設定",
        "",
        *md_table(["項目", "値"], sorted(active.items()) + sorted(platform.items())),
        "",
        "## アプリインストール・端末情報",
        "",
        *md_table(["項目", "値"], sorted(install.items())),
        "",
        f"- メッセージ関連端末情報レコード: {len(devices)}件",
        "",
        "公開判断: Messenger本文・参加者名・端末情報は、アーカイブサイトでは非公開推奨です。必要であれば、活動に関係する問い合わせだけを本人確認・許諾後に別途引用する形がよさそうです。",
    ]
    return write_doc("07-messages-and-private-records.md", "メッセージ・非公開性の高い記録", body)


def inventory_doc(generated):
    rows = json_inventory()
    theme_rows = [(path.name, path.relative_to(ROOT).as_posix()) for path in generated]
    body = [
        "イベント以外のFacebookバックアップをテーマ別に整理したMarkdown群の目次です。",
        "",
        "## 生成ファイル",
        "",
        *md_table(["ファイル", "パス"], theme_rows),
        "",
        "## JSONファイル棚卸し",
        "",
        *md_table(["元ファイル", "概要", "備考"], rows),
    ]
    return write_doc("00-index-and-inventory.md", "イベント以外の資料整理 目次・棚卸し", body)


def summary_doc():
    body = [
        "Facebookバックアップ全体をイベント以外の観点から見ると、Code for SAITAMAの活動は、イベント告知だけでなく、プロフィール、写真、投稿、ページ間のつながり、リアクション、管理履歴、メッセージなど、多層的な記録として残っています。",
        "",
        "もっとも公開アーカイブに活用しやすいのは、プロフィール情報、投稿本文、共有リンク、写真・アルバム、ページがいいねした団体や関連ページの情報です。これらは、Code for SAITAMAがどのようなテーマに関心を持ち、どの地域・団体・活動と接点を持ってきたかを補足する材料になります。イベント年表だけでは見えにくい、日々の共有、学習、連携、告知、記録写真の積み重ねが、活動の厚みを伝えてくれます。",
        "",
        "写真・アルバムは特に価値があります。2015年のオープンデータアイデアソンやハッカソン、Code for Japan Summitでのワークショップ資料、浦和や大宮周辺でのマッピング活動など、イベント本文だけでは伝わりにくい現場感を補えます。アーカイブサイトでは、写真を単に並べるのではなく、イベント年表やテーマ別ページと結びつけることで、活動の流れを視覚的に伝えられます。",
        "",
        "投稿・リンク・シェアからは、Code for SAITAMAが継続的にオープンデータ、OpenStreetMap、防災、協働型災害訓練、UDC、地域コミュニティに関心を寄せていたことが読み取れます。2020年以降のオンライン化、2024年の能登半島地震に関するクライシスマッピング、UDC2024への関心など、イベントデータの空白を補う動きも投稿側に残っています。",
        "",
        "一方で、フォロワー一覧、Messenger、端末、同期、IPを含む写真メタデータなどは、公開アーカイブとしては慎重に扱うべき情報です。これらはバックアップの完全性確認には有用ですが、公開サイトでは原則として件数やカテゴリの説明に留め、個人名・本文・端末情報・IPなどは出さない構成が適しています。",
        "",
        "全体として、Code for SAITAMAのFacebookバックアップは、単なるSNSの記録ではなく、埼玉におけるシビックテック活動の実践ログです。イベントを軸に、投稿、写真、リンク、団体間のつながりを重ねて見せることで、「地図とデータを使って地域を見つめ、考え、手を動かしてきたコミュニティ」という姿を、アーカイブサイト上で立体的に表現できます。",
    ]
    return write_doc("99-overall-summary.md", "全体サマリー", body)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generated = [
        profile_doc(),
        posts_doc(),
        photos_doc(),
        reactions_doc(),
        connections_doc(),
        admin_doc(),
        messages_doc(),
    ]
    summary = summary_doc()
    index = inventory_doc(generated + [summary])
    print(index)
    for path in generated + [summary]:
        print(path)


if __name__ == "__main__":
    main()
