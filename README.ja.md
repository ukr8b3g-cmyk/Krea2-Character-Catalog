[English](./README.md)

**v0.9.7 — Windows・macOS・Linux対応。カタログ本体のZIPは1つです。** Python 3.10以上とブラウザーが必要です。初期言語は英語です。

**v0.9.7の修正：** CP932 CSVの日本語読込、保存JSONの非同期登録競合、再起動時のURLとブラウザー保存領域の維持、追加画像の日時順を修正しました。[修正・復旧方法・検証範囲](docs/RELEASE_v0.9.7.md)。英語／日本語切替と以前のUI改善も保持しています。

**起動方法と以前の改善も保持：** OS名入りのSTART_HEREから起動します。比較は別ツールです。初回設定後は比較専用フォルダーのSTART_COMPARISONから開きます。**以前の修正も保持：** [比較・Editor・プロンプト取得・CSV出力・非表示からの復元・タグ検索・デモ一致の修正](docs/AUDIT_FIXES.md)を完成ZIPに含めます。旧Releaseも残します。ライブデモは同じ検証済みZIPから再作成します。

| OS | 展開した `Krea2-Character-Catalog` フォルダーで開くもの |
|---|---|
| Windows | `START_HERE - Windows.cmd` をダブルクリック |
| macOS | `START_HERE - macOS.command` をダブルクリック。実行権限が保持されない場合は下記のターミナル手順を使用 |
| Linux | このフォルダー内で `sh './START_HERE - Linux.sh'` を実行 |

画像の追加は起動後の「画像を追加」、編集は画像を開いて「編集」から操作できます。Editor用の別ファイルを探す必要はありません。

v0.9.7の公開ZIPはWindows Server 2022・macOS 15 Intel・Ubuntu 24.04のCI合格を公開条件にします。[実際の検証runとOS別レポート](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/releases/tag/v0.9.7#release-validation)／[検証範囲](docs/PLATFORMS.md#validation-scope)。macOS・Linuxのデスクトップでのダブルクリック、OSの警告・権限画面、標準ブラウザーの自動起動、実ファイルマネージャー連携は**実機未確認**です。AnimaDex連携は本体とは別の任意機能です。

<img width="1269" height="743" alt="{604FEE72-032C-4BC9-8AA0-8E2AAB612015}" src="https://github.com/user-attachments/assets/f4878143-6a91-4529-917e-c9bdce45d322" />



**最初に開くものは、OS名が書かれたSTART_HEREです。** `app` は内部ファイル・画像・保存データ用です。普段の利用で中を探す必要はありません。展開したフォルダー全体を一緒に保管してください。

```text
Krea2-Character-Catalog/
  START_HERE - Windows.cmd
  START_HERE - macOS.command
  START_HERE - Linux.sh
  README.md
  README.ja.md
  AnimaDex-Comparison/  # optional comparison setup and startup
  app/
```

終了は画面の「サーバー停止」です。保存データを保持し、ブラウザーのタブは残ります。再開するときも同じSTART_HEREを開きます。

# Krea2 Character Catalog v0.9.7

Krea2で生成したキャラクターとスタイルの見本を、検索・比較しながらプロンプトや元タグと一緒に使うためのローカルカタログです。Windows・macOS・Linux向けの画像追加・編集ツールも含みます。

**このカタログは Incomplete / 不完全です。** 約17,000候補すべてを私自身が目視で確認し、最終的な採否を決めました。一部でAI補助を試しましたが、その結果も自分で確認しており、AI判定だけで採用した画像はありません。ただし、すべてのキャラクターを知っているわけではなく、資料を調べても判断が難しいものは色・形・全体の類似性から暫定的に残しました。人間が確認済みでも、正確な再現やモデルの学習データへの収録を保証しません。名前・タグ・人物や作風の誤認、選別ミスはあり得ます。確認に1週間以上かかり、全件をもう一度確認することは私一人では現実的ではありません。利用する画像を再確認し、誤りがあればキャラクター／スタイル名とカタログのバージョンを添えてお知らせください。修正や改善の報告を歓迎します。

## ダウンロードとライブデモ

- **[v0.9.7のZIPと不合格再生成用JSON](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/releases/tag/v0.9.7)**
- **[最新版のRelease](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/releases/latest)**
- **[閲覧用ライブデモ](https://ukr8b3g-cmyk.github.io/Krea2-Character-Catalog/)**

通常はReleaseの `Krea2-Character-Catalog-v0.9.7.zip` をダウンロードしてください。合格として残した画像・元タグCSV・ワークフロー見本・Editorをまとめて含みます。展開すると `Krea2-Character-Catalog` フォルダーができます。Python本体と生成モデルは同梱していません。

GitHubの **Code → Download ZIP / Source code** は開発用ソースです。画像を含む完成したカタログはReleaseの上記ZIPにあります。各バージョンのReleaseから、その版のZIPを引き続きダウンロードできます。

## すぐに使う

1. ZIPをすべて展開します。ZIPの中から直接実行しないでください。
2. 上の表から、自分のOS用の起動ファイルを開きます。
3. ブラウザーでカタログが開きます。キャラクター／スタイルを切り替え、名前・作品・外見タグで絞り込めます。
4. 画像をクリックすると詳細が開き、Krea2用プロンプトや元タグをコピーできます。

初期アドレスは `http://127.0.0.1:8790/` です。使用中なら空いているポートを選び、実際のアドレスをブラウザーで開きます。別のアプリを停止・置換しません。同じカタログが起動済みならそのサービスを再利用します。公開インターネットに待ち受けを作らず、ローカルPCで使います。

Python **3.10以上**とPillow **10以上13未満・WebP対応**を確認します。利用できる既存Pythonを優先し、必要なら検出したPythonで新しい専用 `.catalog-venv` を作ります。既存Python・古いvenvは変更せず、システム全体へPillowを追加しません。初回の依存導入にはインターネット接続が必要です。Pythonが未導入または3.10未満の場合は、[Windows公式導入先](https://www.python.org/downloads/windows/)・[macOS公式導入先](https://www.python.org/downloads/macos/)・[Linux公式案内](https://docs.python.org/3/using/unix.html)を参照してください。**インストール後、この起動ファイルを再度開きます。** 起動ファイルがPython本体のバージョンを確認してからランチャーを呼びます。旧版と適合版が混在する場合は適合版を選び、無効な指定パスは明示します。エラー時は対話画面を保持し、CIや非対話の入力待ちはしません。

[原因別のエラー案内と検証範囲](docs/PLATFORMS.md)も参照してください。

特定のPythonを使う場合は `KREA2_CATALOG_PYTHON` 環境変数を設定するか、フォルダー内で次を実行します。

```sh
python app/tools/launch_catalog.py --python "<利用するPythonの実行ファイル>"
```

macOS・Linuxでは、必要に応じて `python` を `python3` に置き換えてください。Macでダブルクリック起動できない場合は、このフォルダー内で `sh './START_HERE - macOS.command'` を実行できます。ZIPには実行権限を設定しますが、展開ツールによって保持されない場合があります。

このカタログのバックグラウンド処理だけを停止するには、右上の「サーバー停止」（マウスオーバーで説明表示）を押すか、 `python app/tools/launch_catalog.py --stop` を実行します。ブラウザーのタブを閉じても、再度開けるようにローカルサービスは残ります。

検索条件・表示設定・ページ位置はブラウザーへ、非表示・お気に入り・星評価はローカルファイルへ保存します。同じカタログを再び開くと保存済み状態を使います。ZIPに個人のお気に入り・星評価・入力途中の下書きは含めていません。

## カタログの操作

画像を選択してまとめて非表示にできます。**非表示は画像ファイルの削除ではありません。** 「非表示一覧」「再表示」やUndoで戻せます。Undoは直前の非表示操作をまとめて戻します。非表示を除く一覧はCSV、非表示の一覧はTXTに保存できます。作品順は現在の条件に該当する件数の多い順です。

詳しい操作は [カタログとEditorの使い方](review/README.md)を参照してください。

## 自分の画像を追加・編集する

**Krea2 Catalog Editor** は、自分で生成した画像を登録し、名前・作品・再利用プロンプト・タグを整えるための標準ツールです。画像の生成やAIによる自動合否判定は行いません。

1. カタログ上部の「画像を追加」、またはOSに対応したEditorの起動ファイルを開きます。
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
|`app/outputs/staging/<run>/images/`|同梱した合格画像、コピー用プロンプト、元タグ。|
|`app/outputs/staging/<run>/generation_manifest.json`|同梱画像と情報の対応。|
|`app/outputs/user_items/<uuid>/`|Editorで追加した画像と任意JSON。|
|`app/outputs/user_catalog.json`|追加した項目。|
|`app/outputs/user_catalog_edits.json`|既存項目の編集内容。|
|`app/outputs/review_state.json`|自分の非表示・お気に入り・星評価。|
|`app/original_tags/anima_characters.csv`|既存のキャラクター元タグCSV。|
|`app/original_tags/styles/selected_all_styles.csv`|スタイル候補のCSV。|
|`comfyui/workflows/`|ComfyUI用の共通ワークフロー見本。|
|`lists/`|今回の合格・不合格一覧と件数。|

元タグCSVの列は `tag,category,count,insert_mode` です。`tag` の先頭にキャラクター名・作品名、続いて外見などのタグがあります。生成用サンプル `comfyui/inputs/thumbnail_prompts.csv` は `id,prompt` で、元タグCSVとは別の形式です。コピー用プロンプト、元タグ、実際の生成文は区別しています。

バックアップ・PC移行ではカタログフォルダーごとコピーしてください。更新版は別フォルダーに展開し、旧版を保持してから、追加項目・編集内容・選別状態を移してください。詳細は [更新とバックアップ](docs/UPGRADING.md)を参照してください。

## 生成・再生成

キャラクターとスタイルの画像はComfyUIで生成しました。同梱画像3,919枚のうち、**保存APIメタデータのある3,913枚**には、下記と同じモデル・テキストエンコーダー・VAEが記録されています。同梱のキャラクター／スタイル用ワークフローJSON全6本も同じ組み合わせです。残り6枚の旧画像にはAPIメタデータがないため、元の読み込み設定は画像から確認できませんでした。

|構成|記録されているファイル名・設定|
|---|---|
|Krea2 Turboモデル|`krea2_turbo_int8_convrot.safetensors`（ワークフローのモデルフォルダー：`krea2`）|
|テキストエンコーダー|`qwen3vl_4b_fp8_scaled.safetensors`、CLIP type：`krea2`|
|VAE|`qwen_image_vae.safetensors`|

これらは今回使用した量子化モデル・エンコーダーを含む、ワークフロー内の実際のファイル名です。モデル本体は同梱していません。[キャラクター用JSON](comfyui/workflows/Krea2%20Catalog%20Thumbnails.json)と[スタイル用JSON](comfyui/workflows/Krea2%20Style%20Catalog%20Dedicated.json)を参照し、自分のComfyUI環境に合わせて読み込み先を設定してください。このメタデータ確認は保存された生成設定の確認であり、キャラクターがモデルの学習データに含まれることを示すものではありません。

[生成・追加の説明](README_GENERATION.md)と [ComfyUIのワークフロー](comfyui/README.md)を用意しています。使用モデル・解像度・ステップ等も記載しています。自分の環境で必要なモデル・ノードを用意し、出力した画像をEditorで登録してください。

詳細パネルの「元画像を開く」「画像の場所を開く」から、生成情報を持つWebPを取り出せます。対応するComfyUIへドラッグ＆ドロップするとワークフローを読み込めます。

配布コピーのメタデータから元PCのCSVパスを外しました。キャラクター画像のCSVノードは、保存済みの生成文を `manual_prompt` として直接使います。同梱の `ComfyUI-Krea2-Catalog-Tools` を利用者のComfyUIの `custom_nodes` に置き、ComfyUIを再起動してください。モデル名や不足ノードは各自の環境に合わせます。元の画像の圧縮画素データは変更していません。古い画像など生成情報のない例もあり、すべての画像で条件が完全復元できるわけではありません。

不合格画像はカタログ・ZIPに含めていません。再生成用JSONは別の `Krea2-Character-Catalog-Rejected-Workflows-v0.9.7.zip` です。13,486件は保存された生成情報に基づき、旧版11件は元情報がない編集用テンプレートです。不合格のJSONを実行しても合格を保証するものではありません。画像やブランクのカードを本体へ復活させずに、必要なレシピだけを使えます。

## 簡易ライブデモ

GitHub Pagesのデモは**閲覧用の簡易版であり、フル機能版ではありません。** カタログのPythonバックエンドを使わず、生成済みの静的データを表示します。ZIP版とは機能・保存動作が異なります。

検索・絞り込み・並べ替え・キャラクター／スタイル切替・拡大・コピーを試せます。公開データの削除・非表示・登録・編集はできず、その操作ボタンや保存APIもありません。自分の画像の追加・情報修正にはローカルZIP版を使います。オンラインのデモは、前回スタイルを見ていても開くたびにキャラクター一覧から始まります。その他の表示条件は利用者自身のブラウザー内だけに保存します。ローカル版は前回のタブを保持できます。

[静的デモの作成方法](docs/LIVE_DEMO.md)も同梱しています。

## 任意のAnimaDex比較

[スキル・Codexを使わずに手動設定する手順](docs/COMPARISON_MANUAL.md)。

**AnimaDex連携は任意機能で、Linux・macOSでは未検証です。本体の3OS検証に含みません。** DB読込・画像照合・比較画面・確定判定の反映・別OSへの設定移行はReleaseのCIでは未実施です。

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

Download **Krea2-Character-Catalog-v0.9.7.zip** from [Releases](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/releases/latest), extract it, then double-click `START_HERE - Windows.cmd`. A working Python 3.10+ is reused; a private virtual environment is created when needed. The catalog supports Japanese and English UI. Add your own WebP, PNG or JPEG with the standard Editor; all text fields are optional.

This is an **incomplete, provisional catalog**. Please review and correct images and metadata yourself. The GitHub Pages site is a simplified **read-only static demo**, not the full Python application. Source-code archives do not include the image collection; use the named Release ZIP for the complete catalog.

## AnimaDex比較の初期設定

同梱の `AnimaDex-Comparison` にあるOS名付きSTART_COMPARISONから、画面でフォルダーを選んで設定できます。コマンド・JSON編集・AIアシスタントは不要です。スキルによる自動設定も同じ処理を使います。[設定手順](docs/COMPARISON_MANUAL.md)。

## AnimaDex比較を使う前の準備

AnimaDexは別のアプリです。[公式サイト](https://animadex.net/)・[ローカル版と導入手順](https://github.com/zetaneko/AnimaDex)・[公式データ取り込み手順](https://github.com/zetaneko/AnimaDex/blob/main/docs/import-from-site.md)を参照してください。

1. AnimaDexの手順に従って導入・設定し、一度起動してローカルのカタログが開くことを確認します。
2. キャラクター情報と比較用の参照画像（サムネイル）をPCへ取り込みます。最初のサンプルだけでは全件の比較はできません。AnimaDexのオフラインデータ書き出し・取り込み手順で必要な画像をダウンロードし、ローカルで表示できる状態にしてください。Webサイトを開くだけではローカルへ保存されません。
3. 本カタログの `AnimaDex-Comparison` 内のSTART_COMPARISONを開き、AnimaDexの保存場所を選択します。独自のデータ保存先なら「詳細設定」でDBと画像フォルダーも選べます。

**準備後はAnimaDexを起動しておく必要はありません。** ローカルのSQLite DBを読み取り専用で参照し、画像ファイルを直接表示します。AnimaDexのWebサーバーとは通信しません。DBと画像は移動・削除せず残してください。比較の作成・再作成と判定の反映時にはKrea2カタログを起動します。作成済みの比較を見るだけなら、両アプリ本体のサーバーは停止していても使えます。

AnimaDex自体の設定が難しければ、ChatGPT・Claude・Codex等のLLMへ、公式手順を示して依頼できます。例えば「私のOSでAnimaDexを導入し、キャラクター情報とサムネイルをローカルへ取り込んで、画面で表示できるところまで案内してください」と伝え、OSと保存先を知らせます。書き出し用トークンなどの秘密情報は公開しないでください。本カタログがAnimaDexを自動インストールすることはありません。

[Previous versions and downloads / 旧版のダウンロード](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/releases) — existing releases remain available.

## ライセンス

作者のアプリコード・文書・ツール・タグデータ・プロンプト・カタログ一覧は [MIT License](LICENSE) です。既存カタログの3919枚の画像は別扱いで、この許諾によって一括してMIT素材とはしません。第三者のキャラクター・作品・モデル・元データの権利は変更しません。適用範囲は [NOTICE.md](NOTICE.md) を参照してください。
