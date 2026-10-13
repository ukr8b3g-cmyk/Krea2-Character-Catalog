# 更新とバックアップ

更新版ZIPは別フォルダーへ展開し、旧版を残してください。旧フォルダーへZIPを直接上書きしない方法を推奨します。

自分の登録・修正・選別を移す場合は、旧カタログのサービスを終了した後に、次を対応する場所へコピーします。

- `outputs/user_items/` と `outputs/user_catalog.json`：追加画像と登録情報。
- `outputs/user_catalog_edits.json`：既存カードの修正。
- `outputs/user_comparison_decisions.json`：任意の比較ツールで確定した判定。
- `outputs/review_state.json`：非表示・お気に入り・星評価。

存在しないファイルを作る必要はありません。画像と登録JSONはセットで移してください。編集と判定は画像SHAで対応を確認するため、新版で画像が変わった項目は旧判定を無条件に流用しません。

ブラウザー内の表示条件・入力途中の下書きは、そのブラウザーとローカルアドレスに属します。別PCや別ポートへ移る前に入力を保存・確定してください。

`.venv`、`outputs/python_runtime.json`、`outputs/review_service.json`、ログは移行しません。新版のOSに対応した `open_review.cmd`・`open_review.command`・`open_review.sh` が、新しい場所でPythonとサービスを確認します。空の追加JSONで初期カタログ全体を置き換える処理はありません。
