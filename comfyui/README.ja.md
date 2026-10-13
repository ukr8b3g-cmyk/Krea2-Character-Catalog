[English](./README.md)

# ComfyUIのワークフローと入力サンプル

保存した共通ワークフローは `workflows/` にあります。UI用の `.json` はComfyUIへドラッグ＆ドロップし、モデル名とCSV入力・出力先を各環境へ合わせて使ってください。`.api.json` はAPI用の形式です。

## ノードと保存情報

Krea2のモデル・テキストエンコーダー・VAE、`ForgeNeoBridgeScheduler`、`SaveWebPMeta` を使います。カタログ用CSVを読むノードのソースは `custom_nodes/` に残しています。各ユーザーのComfyUIへ必要なノードを導入してください。

生成条件・CSVとプロンプト・保存WebPの扱いは [画像の生成・追加方法](../README_GENERATION.md) を参照してください。入力サンプルは [thumbnail_prompts.csv](inputs/thumbnail_prompts.csv) です。元タグの統合CSVは別スキーマで [anima_characters.csv](../original_tags/anima_characters.csv) に保存しています。

この配布版には以前の生成キュー・再開管理ツールを含めません。JSONを読み込んだだけでは生成されず、ComfyUIでユーザーが実行します。保存済みWebPにワークフローが含まれる場合は、その画像からも読み込めます。

不合格の再生成用JSONはカタログ本体の外へ分離しています。別の再生成用ZIPを展開し、索引CSVから名前・作品を調べて使います。

## 手入力と保存済み生成文

`Krea2CatalogPromptFile` は `manual_prompt` と `manual_id` を扱えます。`manual_prompt` を入れるとCSVの場所に依存せず、その文を使います。CSV連続生成ではこの欄を空に戻します。配布WebPの生成情報には解決済みの生成文を入れているため、付属ノードを自分のComfyUIへ導入・更新してください。ノードだけではモデル本体や他の依存ノードは追加されません。
