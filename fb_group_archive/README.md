# Facebook group archive

Facebookグループの投稿を古い順に保存したアーカイブです。

- `posts_oldest_first.md`: 本文と画像を古い順に閲覧
- `posts.json`: 構造化データ
- `posts.csv`: 表計算ソフト向け
- `images_manifest.json`: 画像の出典URL・投稿ID・保存先
- `images/`: 投稿画像

## シビックテック非関連投稿の確認

- `non_civictech_review.html`: 検索・絞り込み・画像確認・チェックができるレビュー画面
- `non_civictech_review.md`: Markdownのチェックリスト
- `non_civictech_review.csv`: 表計算ソフト向けの確認表
- `non_civictech_candidates.json`: 判定理由と画像パスを含む構造化データ

レビュー画面のチェック状態はブラウザに保存されます。「選択結果をJSON保存」で、投稿ID・投稿URL・関連画像パスをまとめた削除対象リストを出力できます。この一覧は機械判定を含むため、特に「要確認」と「判定不能」は元投稿と画像を目視してから判断してください。ファイル生成時点では投稿・画像を削除していません。

候補件数: 456件（削除候補・高確度: 38件、要確認: 40件、本文未取得で判定不能: 378件）

取得件数: 941件、画像: 603件
