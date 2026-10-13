[English](./README.md)

# Krea2 Character Catalog v0.9

Krea2で生成したキャラクターとスタイルの見本を、検索・比較しながらプロンプトや元タグと一緒に使うためのローカルカタログです。Windows向けの画像追加・編集ツールも含みます。

**このカタログは Incomplete / 不完全です。** 名前や作品との対応、色・形・雰囲気を目視で確認していますが、似ているという理由で残したものもあります。全画像を人間が十分に確認できたものではなく、生成結果が適切でない画像や、誤ったキャラクター・作風も含まれる可能性があります。キャラクター・スタイルとも暫定です。ダウンロード後も利用者自身で再確認し、必要に応じて編集・非表示・再生成して修正してください。修正や改善の報告を歓迎します。

## ダウンロードとライブデモ

- **[v0.9のZIPと不合格再生成用JSON](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/releases/tag/v0.9)**
- **[最新版のRelease](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/releases/latest)**
- **[閲覧用ライブデモ](https://ukr8b3g-cmyk.github.io/Krea2-Character-Catalog/)**

通常はReleaseの `Krea2-Character-Catalog-v0.9.zip` をダウンロードしてください。合格として残した画像・元タグCSV・ワークフロー見本・Editorをまとめて含みます。展開すると `Krea2-Character-Catalog` フォルダーができます。Python本体と生成モデルは同梱していません。

GitHubの **Code → Download ZIP / Source code** は開発用ソースです。画像を含む完成したカタログはReleaseの上記ZIPにあります。各バージョンのReleaseから、その版のZIPを引き続きダウンロードできます。

## すぐに使う

1. ZIPをすべて展開します。ZIPの中から直接実行しないでください。
2. `open_review.cmd` をダブルクリックします。
3. ブラウザーでカタログが開きます。キャラクター／スタイルを切り替え、名前・作品・外見タグで絞り込めます。
4. 画像をクリックすると詳細が開き、Krea2用プロンプトや元タグをコピーできます。

初期アドレスは `http://127.0.0.1:8790/` です。使用中なら空いているポートを選び、実際のアドレスをブラウザーで開きます。別のアプリを停止・置換しません。同じカタログが起動済みならそのサービスを再利用します。公開インターネットに待ち受けを作らず、ローカルPCで使います。

Python **3.10以上**とPillow **10以上13未満・WebP対応**を確認します。利用できる既存Pythonを優先し、必要なら検出したPythonで専用 `.venv` を作ります。システム全体へPillowを追加しません。初回の依存導入にはインターネット接続が必要です。Python本体がない場合は、[Python公式サイト](https://www.python.org/downloads/windows/)から用意してください。

特定のPythonを使う場合は `KREA2_CATALOG_PYTHON` 環境変数を設定するか、フォルダー内で次を実行します。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/open_review.ps1 -Python "C:\Python\python.exe"
```

検索条件・表示設定・ページ位置はブラウザーへ、非表示・お気に入り・星評価はローカルファイルへ保存します。同じカタログを再び開くと保存済み状態を使います。ZIPに個人のお気に入り・星評価・入力途中の下書きは含めていません。

## カタログの操作

画像を選択してまとめて非表示にできます。**非表示は画像ファイルの削除ではありません。** 「非表示一覧」「再表示」やUndoで戻せます。Undoは直前の非表示操作をまとめて戻します。非表示を除く一覧はCSV、非表示の一覧はTXTに保存できます。作品順は現在の条件に該当する件数の多い順です。

詳しい操作は [カタログとEditorの使い方](review/README.md)を参照してください。

## 自分の画像を追加・編集する

**Krea2 Catalog Editor** は、自分で生成した画像を登録し、名前・作品・再利用プロンプト・タグを整えるための標準ツールです。画像の生成やAIによる自動合否判定は行いません。

1. カタログ上部の「画像を追加」、または `open_editor.cmd` を開きます。
2. 画像を選択・ドロップします。**WebP推奨**、PNG・JPEGにも対応します。1枚64MBまでです。
3. 必要な情報だけ入力し、「登録」を押します。

画像だけでも登録できます。名前・作品・プロンプト・タグはすべて任意です。空欄の名前にはファイル名、作品には「未分類」を使います。入力欄が空だから登録できない、という仕様ではありません。選んだ画像はカタログへコピーし、再圧縮しません。

「CSV・保存JSON（任意）」では、同梱CSVや自分のCSVから候補を検索できます。未知のCSVでは列の対応を選べます。CSVを選ぶだけで勝手に登録しません。JSONなしでも登録でき、不要なJSONは外せます。同じ画像がある場合は、既存項目を使うか別項目として追加するか確認します。

登録済みカードの詳細パネルで「編集」を押すと、そのパネル内の情報を直せます。

|操作|動作|
|---|---|
|登録／緑の「変更を保存」|入力内容をカタログへ確定します。|
|青の「閉じる（入力を残す）」／Esc|下書きを残して閉じます。未保存の変更は確定しません。|
|オレンジの「キャンセル（変更を破棄）」|未保存の入力と下書きを消し、保存済みの情報へ戻ります。|
|「入力欄を空にする」|文字欄だけを空にして、編集を続けます。|

変更した項目だけを別ファイルに保存します。空の追加ファイルで既存カタログ全体をクリアしません。画像・元の生成記録・非表示・お気に入り・星評価は保持します。

## 画像・タグ・保存場所

|場所|内容|
|---|---|
|`outputs/staging/<run>/images/`|同梱した合格画像、コピー用プロンプト、元タグ。|
|`outputs/staging/<run>/generation_manifest.json`|同梱画像と情報の対応。|
|`outputs/user_items/<uuid>/`|Editorで追加した画像と任意JSON。|
|`outputs/user_catalog.json`|追加した項目。|
|`outputs/user_catalog_edits.json`|既存項目の編集内容。|
|`outputs/review_state.json`|自分の非表示・お気に入り・星評価。|
|`original_tags/anima_characters.csv`|既存のキャラクター元タグCSV。|
|`original_tags/styles/selected_all_styles.csv`|スタイル候補のCSV。|
|`comfyui/workflows/`|ComfyUI用の共通ワークフロー見本。|
|`lists/`|今回の合格・不合格一覧と件数。|

元タグCSVの列は `tag,category,count,insert_mode` です。`tag` の先頭にキャラクター名・作品名、続いて外見などのタグがあります。生成用サンプル `comfyui/inputs/thumbnail_prompts.csv` は `id,prompt` で、元タグCSVとは別の形式です。コピー用プロンプト、元タグ、実際の生成文は区別しています。

バックアップ・PC移行ではカタログフォルダーごとコピーしてください。更新版は別フォルダーに展開し、旧版を保持してから、追加項目・編集内容・選別状態を移してください。詳細は [更新とバックアップ](docs/UPGRADING.md)を参照してください。

## 生成・再生成

[生成・追加の説明](README_GENERATION.md)と [ComfyUIのワークフロー](comfyui/README.md)を用意しています。使用モデル・解像度・ステップ等も記載しています。自分の環境で必要なモデル・ノードを用意し、出力した画像をEditorで登録してください。

詳細パネルの「元画像を開く」「画像の場所を開く」から、生成情報を持つWebPを取り出せます。対応するComfyUIへドラッグ＆ドロップするとワークフローを読み込めます。

v0.9では、配布コピーのメタデータから元PCのCSVパスを外しました。キャラクター画像のCSVノードは、保存済みの生成文を `manual_prompt` として直接使います。同梱の `ComfyUI-Krea2-Catalog-Tools` を利用者のComfyUIの `custom_nodes` に置き、ComfyUIを再起動してください。モデル名や不足ノードは各自の環境に合わせます。元の画像の圧縮画素データは変更していません。古い画像など生成情報のない例もあり、すべての画像で条件が完全復元できるわけではありません。

不合格画像はカタログ・ZIPに含めていません。再生成用JSONは別の `Krea2-Character-Catalog-Rejected-Workflows-v0.9.zip` です。13,486件は保存された生成情報に基づき、旧版11件は元情報がない編集用テンプレートです。不合格のJSONを実行しても合格を保証するものではありません。画像やブランクのカードを本体へ復活させずに、必要なレシピだけを使えます。

## 簡易ライブデモ

GitHub Pagesのデモは**閲覧用の簡易版であり、フル機能版ではありません。** カタログのPythonバックエンドを使わず、生成済みの静的データを表示します。ZIP版とは機能・保存動作が異なります。

検索・絞り込み・並べ替え・キャラクター／スタイル切替・拡大・コピーを試せます。公開データの削除・非表示・登録・編集はできず、その操作ボタンや保存APIもありません。自分の画像の追加・情報修正にはローカルZIP版を使います。オンラインのデモは、前回スタイルを見ていても開くたびにキャラクター一覧から始まります。その他の表示条件は利用者自身のブラウザー内だけに保存します。ローカル版は前回のタブを保持できます。

[静的デモの作成方法](docs/LIVE_DEMO.md)も同梱しています。

## 任意のAnimaDex比較連携

画面構成・情報の整理方法は [AnimaDex](https://animadex.net/)を参考にしています。通常の登録・編集にAnimaDexやCodexは不要です。

AnimaDexとの比較が必要な場合は、両方をローカルへ用意し、任意の [krea2-animadex-reviewスキル](skills/krea2-animadex-review/SKILL.md)を使えます。固定のPCパス・ポートを使わず、自分の環境設定で既存インストールを再利用します。詳細は [導入・比較・判定反映](docs/COMPARISON_SKILL.md)を参照してください。

AIは候補を提案し、人間が最後に判断します。選択して確定した合格・不合格だけを反映し、未選択・保留・空データは既存状態を変更しません。名前だけで参照を決めず、CSV識別タグと両画像の一致を確認します。スキルの照合処理そのものはAIの目視判定ではありません。現在の比較アダプターはキャラクター用で、スタイルの参照対応は別途確認が必要です。

## 合否一覧とチェック件数

|対象|合格|不合格|確認対象総数|
|---|---:|---:|---:|
|キャラクター|3,809|13,122|16,931|
|スタイル|110|375|485|
|合計|3,919|13,497|17,416|

- [キャラクター合格一覧](lists/character-pass.csv)
- [キャラクター不合格一覧](lists/character-fail.csv)
- [スタイル合格一覧](lists/style-pass.csv)
- [スタイル不合格一覧](lists/style-fail.csv)
- [件数データ](lists/summary.json)

件数は今回の現行カタログに対応する画像候補単位です。同一キャラクターの衣装違いなどは別候補になり、以前の廃止・重複スタイル見本はこの集計に含みません。保留・未判定は今回の対象では0件です。「合格」は暫定的な選別結果で、正確な再現の保証ではありません。

スタイルの確認では、Pixiv・Danbooruに掲載される絵師の作風が再現されにくい例が多く、有名な漫画家・イラストレーターの一部には似た例がありました。これはこのカタログでの観察であり、モデルの学習データの収録有無を確定したものではありません。

キャラクター・作品・モデル・第三者のタグデータ等の権利は各権利者に帰属します。必要な利用条件は各提供元を確認してください。誤った名前・タグ・生成結果を見つけたら、対象名と版を添えてIssuesから報告できます。

## English quick start

Download **Krea2-Character-Catalog-v0.9.zip** from [Releases](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/releases/latest), extract it, then double-click `open_review.cmd`. A working Python 3.10+ is reused; a private virtual environment is created when needed. The catalog supports Japanese and English UI. Add your own WebP, PNG or JPEG with the standard Editor; all text fields are optional.

This is an **incomplete, provisional catalog**. Please review and correct images and metadata yourself. The GitHub Pages site is a simplified **read-only static demo**, not the full Python application. Source-code archives do not include the image collection; use the named Release ZIP for the complete catalog.
