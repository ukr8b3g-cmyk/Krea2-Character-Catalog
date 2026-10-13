# 任意のAnimaDex比較連携

**Scope: optional AnimaDex integration; Linux/macOS are unverified.** Core catalog CI does not exercise SQLite DB loading, reference image matching, comparison pages, confirmed-verdict application, or cross-OS relocation/rebuilding of comparison artifacts. Configure paths locally and regenerate comparison material after moving environments. No personal DB or images are used in release CI.

通常の画像追加・情報編集はカタログとEditorでできます。AnimaDexを使った比較が必要な場合だけ、同梱の [krea2-animadex-review](../skills/krea2-animadex-review/SKILL.md) をCodex等へ導入します。キャラクター比較用のスキルで、スタイルは別の参照形式を確認してから扱います。

## 導入と環境設定

`skills/krea2-animadex-review/` を、使っているCodexのskillsフォルダーへコピーしてください。このカタログに同梱しただけでは、Codex全体に自動インストールしたことにはなりません。導入後は新しいCodexタスクで「$krea2-animadex-review を使い、指定したカタログとAnimaDexを比較する」のように依頼できます。既存タスクでは同梱のSKILL.mdを直接指定できます。

スキルの `config.example.json` を作業用フォルダーへコピーし、`catalog_root` と `animadex_root` を各自の場所に設定します。設定ファイルからの相対パスでも指定できます。Python・ドライブ・ユーザー名・ポートを固定していません。AnimaDexは既存のインストールを利用し、スキルが勝手に導入・置換しません。

カタログを通常のランチャーで開いてから、スキルのフォルダーをカレントディレクトリにして実行します。

```powershell
python scripts/review.py inspect --config "../private/review-config.json"
python scripts/review.py prepare --config "../private/review-config.json" --output "../private/review-001"
python scripts/review.py serve --review-dir "../private/review-001" --port 0
```

作業フォルダーは両方のカタログの外に置きます。表示されたローカルURLをブラウザーで開きます。比較画面の終了はCtrl+Cです。同じ作業フォルダーを `--port 0` で再開すると、`review-server.json` に記録した前回のポートを再利用します。検索・判定フィルター・ページ位置・判定下書きは同じブラウザーの同じアドレスで復元します。前回のポートが他のサービスに使われていたら、先に所有者を確認してください。勝手に停止しません。明示的に別ポートを指定した場合は保存先のブラウザー領域が変わるため、先に確定JSONを保存してください。スクリプト自体はPython標準ライブラリだけを使います。

## 比較と確定

CSVの名前・作品の識別タグとAnimaDexのtriggerが一意に一致し、両画像があるものを並べます。照合処理自体はAI判定ではありません。Codexに実際の両画像を比較してもらう場合は、スキルに沿って候補を作り、最後は人間が確認します。対応が曖昧なものは推測で合格にしません。参照が見つからない、候補が複数ある、画像がない項目は、画面上部の「参照未対応の一覧（CSV）」から確認できます。未対応は不合格という意味ではありません。CSVの reason は `csv_identity_missing`（元CSVに識別タグなし）、`reference_missing`（参照なし）、`reference_ambiguous`（参照候補が複数）、`image_missing`（画像なし）です。

比較画面で合格・不合格・保留を選び、反映対象にチェックを付けます。「選択した判定を確定してJSON出力」は確定データを書き出す操作で、カタログへの反映は別です。未選択・保留は反映されません。

```powershell
python scripts/review.py apply --config "../private/review-config.json" --review-dir "../private/review-001" --decisions "../private/confirmed-comparison-decisions.json" --dry-run
python scripts/review.py apply --config "../private/review-config.json" --review-dir "../private/review-001" --decisions "../private/confirmed-comparison-decisions.json"
```

まずdry-runの件数を確認します。反映時は両画像のSHAを再確認し、変更された画像や別カタログへの反映を拒否します。現在の選別状態を作業フォルダーへ退避し、合格は表示、不合格は非表示にします。画像を物理削除しません。既存のお気に入り・星評価・元タグ・画像・生成記録は保持します。空の判定ファイルでカタログ全体を初期化しません。

確定履歴は `outputs/user_comparison_decisions.json` に保存し、次の比較準備では同じ画像の判定済み分を除外します。反映途中で問題が起きた場合は作業フォルダーの `apply-checkpoint.json` とスナップショットを確認し、現在の状態を読んでから再実行します。生成ジョブを止める必要はありません。

AnimaDexのDB形式が違う場合は、実際の形式を確認して対応を調整します。満たされた照合数と実際にAIが比較した数は別々に報告してください。比較資料・バックアップ・設定ファイルにはそのPCのパスが入るため、配布ZIPやライブデモに混ぜません。

## 確認済みの範囲

相対パスと空白を含む別フォルダーで、確定分だけの合格／不合格反映を確認しています。現在の実カタログではキャラクター3,809件中3,696組を照合し、113件を未対応として出力できました。実カタログの判定は変更せず、空データの反映が何も消さないことを確認しました。実ブラウザーで両画像、検索リンク、F5とサーバー再起動後の条件・下書き復元を確認済みです。Windowsでの二重起動も拒否します。別PCでの通し検証、実際のAI画像再判定、スタイル画像の対応はこの確認には含みません。
