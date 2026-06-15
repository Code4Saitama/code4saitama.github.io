# Code for SAITAMA Archive

Code for SAITAMA の活動記録を整理し、静的なアーカイブサイトとして公開するためのリポジトリです。

Facebook ページのエクスポートデータ、写真素材、補足調査レポートをもとに、イベントを中心とした時系列・テーマ別のアーカイブを Astro で構築しています。

## 概要

- サイト種別: Astro による静的サイト
- 主な内容: イベント一覧、年表、テーマ別整理、イベント詳細、団体紹介、補足資料
- コンテンツ形式: `src/content/` 以下の Markdown
- 画像素材: `public/assets/images/` 以下の original / webp
- 元データ: `data/facebook-export/` 以下の Facebook エクスポートデータ

## ディレクトリ構成

```text
.
├── data/facebook-export/      # Facebook エクスポート由来の元データ
├── docs/                      # 調査・整理済みのMarkdown資料
├── public/
│   ├── assets/images/         # 公開サイトで使用する画像素材
│   └── docs/                  # 公開用に配置した参考資料
├── scripts/                   # コンテンツ生成・整理用スクリプト
├── src/
│   ├── components/            # Astroコンポーネント
│   ├── content/               # Markdownベースのサイトコンテンツ
│   ├── layouts/               # 共通レイアウト
│   ├── lib/                   # 表示用ユーティリティ
│   ├── pages/                 # ページ定義
│   └── styles/                # グローバルCSS
└── dist/                      # ビルド成果物
```

## セットアップ

Node.js と npm が使える環境で実行します。

```sh
npm install
```

## 開発

ローカル開発サーバーを起動します。

```sh
npm run dev
```

デフォルトでは `http://127.0.0.1:4321/` で起動します。ポートが使用中の場合は Astro が別ポートを提示します。

## ビルド

静的サイトを `dist/` に生成します。

```sh
npm run build
```

ビルド済みサイトを確認する場合は次を使います。

```sh
npm run preview
```

## コンテンツ編集

通常の本文・紹介文・補足資料は Markdown を編集します。

- イベント: `src/content/events/`
- 補足資料の年表項目: `src/content/notes/`
- トップページのスライド: `src/content/slides/`
- 団体紹介・関連資料ページ: `src/content/pages/`

イベント詳細ページの URL は、各イベント Markdown のファイル名および frontmatter の `page` に基づきます。公開用のファイル名は、日付と内容が分かる 1 byte 文字のセマンティックな命名にしています。

## コンテンツ再生成

Facebook エクスポートデータや生成ロジックから `src/content/` を再生成する場合は、次を実行します。

```sh
npm run export:content
```

このコマンドは `src/content/events/`、`src/content/notes/`、`src/content/slides/` を生成し直します。手作業で調整した内容がある場合は、実行前に差分を確認してください。

## 画像素材

公開サイトで使用する画像は `public/assets/images/` に配置しています。

- 元画像コピー: `public/assets/images/original/`
- WebP画像: `public/assets/images/webp/`
- 画像一覧: `public/assets/images/images-manifest.csv`
- 詳細な一覧: `public/assets/images/images-manifest.md`

記事ページのメイン写真は、イベントと写真の対応が確認できるものを優先しています。集合写真・記念撮影であることがメタデータから確認できる場合は、記事のメイン写真として優先採用しています。

## 注意事項

- `data/facebook-export/` は Facebook エクスポート由来の元データです。公開に不要な個人情報やシステム情報を不用意にサイトへ出さないよう注意してください。
- 補足調査レポート由来の項目は、サイト上では「関連資料」「補足」として扱い、Facebook由来イベントと混同しないようにしています。
- `dist/` はビルド成果物です。通常は直接編集しません。
- 過去の静的HTML版 `archive-site/` は Astro 移行により廃止しています。

## 主なコマンド

```sh
npm run dev             # 開発サーバー起動
npm run build           # 静的サイトをビルド
npm run preview         # ビルド済みサイトをプレビュー
npm run export:content  # Markdownコンテンツを再生成
```

## 公開前チェック

公開前には、少なくとも次を確認します。

```sh
npm run export:content
npm run build
```

あわせて、トップページ、年表、テーマ別ページ、主要イベント詳細ページ、写真なしイベントのロゴ表示をブラウザで確認してください。
