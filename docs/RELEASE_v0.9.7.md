# Krea2 Character Catalog v0.9.7

[日本語](#日本語) · [English README](../README.md) · [日本語 README](../README.ja.md)

Four fixes for the local catalog and Editor. The image collection, catalog records, original CSVs, and rejected-workflow recipes are preserved from v0.9.6. Older releases remain available.

- Japanese CP932 CSV suggestions retain their names, copyright and tags. UTF-16 is selected only for files with a UTF-16 BOM; UTF-8 and UTF-8 BOM remain supported.
- Register is disabled while workflow JSON is being read. Selecting another JSON or removing JSON invalidates older reads. Invalid JSON blocks registration until removed or replaced. Close waits for the selected JSON and retains the image draft; Cancel discards that pending selection.
- The catalog remembers its last port separately from process information. Restarting with the same port option first tries the remembered port, preserving the browser origin and its drafts/settings. Other services are never stopped. If that port is also occupied, the launcher records/displays the previous URL and reports that browser data remains there. Stop this catalog, free the previous port, and reopen the normal startup file with `--port PREVIOUS_PORT` to return to that browser origin. Browser data is not automatically transferred between origins; do not clear it.
- Newest/generation sorting uses user-added timestamps and generation-run timestamps, with stable tie breakers rather than numeric UUIDs. Existing within-run source order is retained.

## Downloads and existing data

Download `Krea2-Character-Catalog-v0.9.7.zip` for the complete application, or the separate rejected-workflow ZIP for recipes. Automatic Source code archives omit the image collection. Checksums are in `SHA256SUMS.txt`.

Extract to a new folder first. Keep the previous folder and its browser data. For an existing customized catalog, retain its images, `app/outputs`, original tag CSVs, settings and local changes; do not replace those with a clean distribution. The six runtime fix files are `app/review/catalog_editor.py`, `editor.js`, `review.js`, `runtime_support.py`, `server.py`, and `app/tools/launch_catalog.py`.

The distribution is made by copying the verified v0.9.6 ZIP and replacing/adding only changed source and documentation entries using **7-Zip**. Every other archive entry, including all image and catalog data, is compared byte-for-byte by SHA-256. Rejected-workflow ZIP bytes are unchanged. Publication is gated on the exact candidate ZIP passing Windows Server 2022, macOS 15 Intel, and Ubuntu 24.04 tests; the run link and reports are appended below by the release workflow.

## Validation scope

Local Windows checks: Python 34 tests, 11 synthetic API contract groups, real Chrome workflow-race regressions, and actual launcher restart with image/JSON draft and search/favorite-filter restoration. Both occupied-port notification and explicit return to the previous origin were tested. Regression checks are also run against the distributed ZIP in CI. The public demo is rebuilt from that same tested ZIP; it remains a simplified read-only preview without registration or Editor backend operations.

Physical macOS/Linux desktop launch, native security/file-manager dialogs, real AnimaDex datasets, exhaustive visual review of the collection, and GPU/ComfyUI generation are not covered by these checks.

## 日本語

CP932 CSVの日本語誤読、JSON読込中の誤登録・選び直し・削除の競合、再起動でURLが変わって下書きや表示設定へ戻れなくなる問題、追加画像の「新しい順」を修正しました。画像・カタログデータ・元CSV・再生成レシピはv0.9.6から保持し、旧Releaseも残します。

同じポート指定で再起動した場合、前回の使用ポートを先に試します。そのポートまで他サービスに使われている場合は元URLと復旧方法を通知します。元の下書き・設定は以前のURLに残り、自動移行はしません。このカタログを停止し、元ポートの競合を解消した後、普段の起動ファイルへ `--port 元ポート番号` を付けて戻せます。ブラウザーの保存データを削除しないでください。他サービスを自動停止する処理はありません。

まず別フォルダーへ展開し、旧フォルダーを保管してください。カスタマイズ済み本体の画像、`app/outputs`、元CSV、設定、既存変更を配布用の初期データで上書きしないでください。ZIP内のファイル更新には7-Zipを使用し、更新対象外の全エントリと全画像のSHA-256一致を確認します。公開デモは同じ検証済みZIPから更新しますが、編集・登録のない読み取り専用版です。

Windowsのローカル検証、隔離コピーの実Chrome・実ランチャー検証に加え、同一ZIPの3OS自動テストを公開条件とします。GPU生成、実AnimaDexデータ、全画像の目視校正、macOS/Linux実デスクトップでの操作は検証していません。
