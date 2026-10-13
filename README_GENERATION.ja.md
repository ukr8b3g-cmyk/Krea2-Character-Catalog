[English](./README_GENERATION.md)

# Krea2 キャラクターカタログ — 画像の生成・追加方法

この配布版には生成管理・再開チェックポイントを含めません。保存済みワークフローをComfyUIで利用します。

このファイルは、ローカルカタログに追加するキャラクター画像の生成方法をまとめたものです。2026年10月8日に、保存済みWebPのメタデータ・生成記録・ワークフローから確認しました。

確認画面はプロジェクト直下の `open_review.cmd` から開けます。[画面の使い方](review/README.md)と[生成ツールの詳しい操作](comfyui/README.md)も参照してください。

## 1. 使用モデルと生成設定

現在のキャラクター画像は、次の設定で生成しています。

|項目|設定|
|---|---|
|画像生成モデル|`krea2_turbo_int8_convrot.safetensors`（ワークフロー内のパスは `krea2\krea2_turbo_int8_convrot.safetensors`）|
|テキストエンコーダー|`qwen3vl_4b_fp8_scaled.safetensors` / CLIPのtypeは `krea2`|
|VAE|`qwen_image_vae.safetensors`|
|生成サイズ|**幅896 × 高さ1184 px**|
|ステップ|**8**|
|CFG|**1.0**|
|Sampler|**Euler**（`euler`）|
|Scheduler|**simple** / `ForgeNeoBridgeScheduler`|
|Denoise|**1.0**|
|Seed|**42、固定**|
|Batch size|**1**（一度に1枚。ツールが必要な枚数を順に生成）|
|Negative|`ConditioningZeroOut` で正のconditioningをゼロ化。別のネガティブ文章は入力していません。|
|保存ノード|**Save WEBP Meta**（`SaveWebPMeta`）|
|画像形式|**WebP、非可逆圧縮**（`file_format: webp`）|
|WebP品質|**80**（保存ノード内部の `method: 0`）|
|メタデータ|実際の生成文、モデル・サンプラー設定、ワークフロー、元レコードとの対応をEXIFに保存|

再現には [UI用ワークフロー](comfyui/workflows/Krea2%20Catalog%20Thumbnails.json) または [API用ワークフロー](comfyui/workflows/Krea2%20Catalog%20Thumbnails.api.json) を使います。モデルのファイル名だけでなく、テキストエンコーダー・VAE・ForgeNeo Bridgeのスケジューラーも合わせてください。必要なノードと配置先は [ComfyUI側の説明](comfyui/README.md#ノードと保存情報) にあります。

生成画像の896×1184 pxと、一覧の表示幅は別の値です。確認画面の初期表示幅は170 pxで、スライダーによる拡大・縮小は表示だけを変えます。元のWebPを書き換えません。

## 2. ファイルサイズの目安

Blue Archiveの完了済み生成 `run-20261007-150736` の**344枚**を実測しました。旧方式で退避した画像も含み、全枚がWebP・896×1184 px・上記のモデル・8ステップ・CFG 1・Seed 42・品質80でした。

|項目|実測値|
|---|---|
|平均|**69.6 KiB**（71,236 bytesに丸め）|
|中央値|**69.2 KiB**（70,844 bytes）|
|最小〜最大|**46.2〜102.8 KiB**（47,302〜105,302 bytes）|
|例：`ayane (blue archive)` / `a02728.webp`|**63.2 KiB**（64,734 bytes）|

1 KiBは1,024 bytesです。これらは生成情報を含むファイル全体のサイズで、EXIFは平均約17.4 KiBあります。容量は絵柄・細部・生成文などによって変わるため、70 KiBに固定する必要はありません。品質80を基準にしてください。

一覧専用の小さなWebPを作る場合は、別フォルダに出力する [WebPThumbnailBatch](tools/WebPThumbnailBatch/README.md) を使えます。元画像を残す方式です。現状はこのミニツールの作成までで、確認画面を縮小ファイルへ切り替える処理は未実施です。

## 3. 灰色背景・単独・カメラ目線の指定

生成用の説明文の末尾に、専用ノードが以下を追加します。

```text
standing alone on a plain gray background, looking at the camera
```

- `standing alone`：単独で立っている構図。
- `plain gray background`：無地の灰色背景。
- `looking at the camera`：こちら、カメラを見る視線。

**`full body` は追加していません。** 背景のRGB値も固定していません。灰色の濃さや構図は生成結果によって違います。画面のダーク／ウォームグレーのテーマ色は、生成画像の背景指定とは別です。

保存済みの `ayane (blue archive)` の生成文は、以下でした。

```text
A single female character, ayane (blue archive) from blue archive. Appearance: pointy ears, yellow eyes, hair between eyes, brown eyes, glasses, red-framed eyewear, black hair, short hair, braid, hair flower, medium breasts, school uniform, open jacket, white shirt, collared shirt, halo, red halo, long sleeves, standing alone on a plain gray background, looking at the camera
```

## 4. 元タグCSVと生成用サンプルの違い

元の統合CSVは `original_tags/anima_characters.csv` に保存しています。実際の列は `tag,category,count,insert_mode` です。`tag` の原文にはキャラクター名・作品・髪や衣装などが含まれます。

残した生成用サンプル `comfyui/inputs/thumbnail_prompts.csv` の列は **`id,prompt`** です。統合元CSVとは別の形式です。カタログ用ComfyUIノードは `prompt`、`tag`、`text` のいずれかの列を読み、背景などの共通指定を後ろに追加します。

カタログでコピーできるKrea2用の文章は、生成時の背景・姿勢などを除いた再利用向けの文です。「元タグ」はタグ原文です。画像に使った実際の生成文とは区別します。コピー文・元タグ・画像との対応は、現行の生成記録と同名のTXTを保持しています。

## 5. 保存画像・生成用サンプル

保存WebPにワークフロー情報が含まれている場合は、元画像をComfyUIへドラッグ＆ドロップして読み込めます。メタデータのない旧版画像もあるため、すべての画像で元条件を復元できるわけではありません。

共通のUI用・API用JSONは `comfyui/workflows/` に、入力CSVのサンプルは `comfyui/inputs/thumbnail_prompts.csv` に残しています。モデルの名前・CSV入力の場所・出力先を各自の環境へ合わせてから使います。Krea2はWebP保存を推奨しています。

画像を保存したら、カタログの「画像を追加」または `open_editor.cmd` を開き、出力された画像を選んで「登録」を押してください。名前・作品・プロンプト・タグは任意で、CSVの候補入力も使えます。保存画像は元ファイルを変更せずコピーされます。ワークフローJSONは必要な場合だけ添付してください。

既存の生成画像は `outputs/staging/<run>/generation_manifest.json` から読み込み、追加分は `outputs/user_catalog.json` と `outputs/user_items/` に分けて保存します。元の生成記録を手作業で書き換える必要はありません。

不合格再生成用JSONは本体の外の `Krea2-Character-Catalog-Rejected-Workflows` と同名ZIPへ分離しています。別ZIPを展開して対応JSONをComfyUIで読み込みます。13,486件は保存画像から条件を復元したもの、旧版11件は元情報がない編集用テンプレートです。

## v0.9の保存画像からの再生成

配布画像のワークフローでは `Krea2CatalogPromptFile` の `manual_prompt` に、その画像で使った生成文を保存しています。`manual_id` は保存用のIDです。手入力の文がある場合はCSVを読みません。CSVを使って連続生成したい場合は `manual_prompt` を空欄にし、`file_path` とindexを自分のファイルへ合わせてください。付属ノードをComfyUIへコピー・更新し、再起動してから使います。モデル・依存ノードの登録名は各環境へ合わせる必要があります。
