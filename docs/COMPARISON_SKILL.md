# 任意のAnimaDex比較連携

**Scope: optional AnimaDex integration.** Release CI uses a fictitious SQLite DB and synthetic images to test pairing, comparison display, setup controls and confirmed-verdict application contracts on Windows, macOS and Linux. Real AnimaDex installations, real reference collections and cross-OS relocation/rebuilding remain unverified. Configure paths locally and regenerate comparison material after moving environments. No personal DB or images are used in release CI.

通常の画像追加・情報編集はカタログとEditorでできます。AnimaDexを使った比較が必要な場合だけ、同梱の [krea2-animadex-review](../skills/krea2-animadex-review/SKILL.md) をCodex等へ導入します。キャラクター比較用のスキルで、スタイルは別の参照形式を確認してから扱います。

スキルを使わない場合は [手動設定マニュアル](COMPARISON_MANUAL.md) を参照してください。

## 普段の開き方

初回設定は、同梱のAnimaDex-Comparison内のSTART_COMPARISONから画面でフォルダーを選ぶ方法と、Codex等のスキルへ保存場所を伝えて自動設定する方法の二通りです。利用者が設定JSONや深い場所のHTMLを探す必要はありません。

比較はカタログ本体とは別ツールです。設定後は比較専用フォルダーにある、OS名付きの **START_COMPARISON** を開きます。内部のHTMLやJSONを探したり、サーバー用コマンドを入力したりする必要はありません。終了は比較画面の **Stop server / サーバー停止** です。判定の下書きはブラウザーに保存し、カタログへの反映には従来どおり選択・確定が必要です。

初回設定やPC移行後の再設定は、設定画面またはアシスタントで行えます。既存の比較を開く依頼なら、その比較を先に探して再利用します。新しい比較を勝手に作り直して判定を消すことはしません。

## アシスタント・上級者向けの設定手順

以下は初回設定・診断用です。普段の起動でこれらのコマンドを入力する必要はありません。

## 導入と環境設定

`skills/krea2-animadex-review/` を、使っているCodexのskillsフォルダーへコピーしてください。このカタログに同梱しただけでは、Codex全体に自動インストールしたことにはなりません。導入後は新しいCodexタスクで「$krea2-animadex-review を使い、指定したカタログとAnimaDexを比較する」のように依頼できます。既存タスクでは同梱のSKILL.mdを直接指定できます。

スキルの `config.example.json` を作業用フォルダーへコピーし、`catalog_root` と `animadex_root` を各自の場所に設定します。設定ファイルからの相対パスでも指定できます。Python・ドライブ・ユーザー名・ポートを固定していません。AnimaDexは既存のインストールを利用し、スキルが勝手に導入・置換しません。

カタログを通常のランチャーで開いてから、スキルのフォルダーをカレントディレクトリにして実行します。

```powershell
python scripts/review.py inspect --config "../private/review-config.json"
python scripts/review.py prepare --config "../private/review-config.json" --output "../private/review-001"
python scripts/review.py serve --review-dir "../private/review-001" --port 0
```

作業フォルダーは両方のカタログの外に置きます。v0.9.5ではprepareが比較専用のSTART_COMPARISONを用意します。serveコマンドは診断向けの前面サーバーで、通常は不要です。診断用のserveコマンドを前面で動かした場合はCtrl+Cで停止します。通常のSTART_COMPARISONでは画面の「サーバー停止」を使います。同じ作業フォルダーを `--port 0` で再開すると、`review-server.json` に記録した前回のポートを再利用します。検索・判定フィルター・ページ位置・判定下書きは同じブラウザーの同じアドレスで復元します。前回のポートが他のサービスに使われていたら、先に所有者を確認してください。勝手に停止しません。明示的に別ポートを指定した場合は保存先のブラウザー領域が変わるため、先に確定JSONを保存してください。スクリプト自体はPython標準ライブラリだけを使います。

## 比較と確定

CSVの名前・作品の識別タグとAnimaDexのtriggerが一意に一致し、両画像があるものを並べます。照合処理自体はAI判定ではありません。Codexに実際の両画像を比較してもらう場合は、スキルに沿って候補を作り、最後は人間が確認します。対応が曖昧なものは推測で合格にしません。参照が見つからない、候補が複数ある、画像がない項目は、画面上部の「参照未対応の一覧（CSV）」から確認できます。未対応は不合格という意味ではありません。CSVの reason は `csv_identity_missing`（元CSVに識別タグなし）、`reference_missing`（参照なし）、`reference_ambiguous`（参照候補が複数）、`image_missing`（画像なし）です。

比較画面で合格・不合格・保留を選び、反映対象にチェックを付けます。「選択した判定を確定してJSON出力」は確定データを書き出す操作で、カタログへの反映は別です。未選択・保留は反映されません。

```powershell
python scripts/review.py apply --config "../private/review-config.json" --review-dir "../private/review-001" --decisions "../private/confirmed-comparison-decisions.json" --dry-run
python scripts/review.py apply --config "../private/review-config.json" --review-dir "../private/review-001" --decisions "../private/confirmed-comparison-decisions.json"
```

まずdry-runで、表示変更が必要な件数と変更不要の件数を確認します。表示中の合格・非表示中の不合格は表示APIを呼ばず、確定判定の記録だけ保存します。反映時は両画像のSHAを再確認し、変更された画像や別カタログへの反映を拒否します。現在の選別状態を作業フォルダーへ退避し、合格は表示、不合格は非表示にします。画像を物理削除しません。既存のお気に入り・星評価・元タグ・画像・生成記録は保持します。空の判定ファイルでカタログ全体を初期化しません。

確定履歴は `outputs/user_comparison_decisions.json` に保存し、次の比較準備では同じ画像の判定済み分を除外します。反映途中で問題が起きた場合は作業フォルダーの `apply-checkpoint.json` とスナップショットを確認し、現在の状態を読んでから再実行します。生成ジョブを止める必要はありません。

AnimaDexのDB形式が違う場合は、実際の形式を確認して対応を調整します。満たされた照合数と実際にAIが比較した数は別々に報告してください。比較資料・バックアップ・設定ファイルにはそのPCのパスが入るため、配布ZIPやライブデモに混ぜません。

## 過去の形式での確認と制約

相対パスと空白を含む別フォルダーで、確定分だけの合格／不合格反映を確認しています。現在の実カタログではキャラクター3,809件中3,696組を照合し、113件を未対応として出力できました。実カタログの判定は変更せず、空データの反映が何も消さないことを確認しました。実ブラウザーで両画像、検索リンク、F5とサーバー再起動後の条件・下書き復元を確認済みです。Windowsでの二重起動も拒否します。別PCでの通し検証、実際のAI画像再判定、スタイル画像の対応はこの確認には含みません。

事前に[AnimaDex](https://github.com/zetaneko/AnimaDex)を起動できるように設定し、[公式取り込み手順](https://github.com/zetaneko/AnimaDex/blob/main/docs/import-from-site.md)で参照画像とデータをPCへ保存してください。導入で困った場合はLLMへ公式手順に沿った支援を依頼できます。比較時はAnimaDex本体の起動は不要です。

## v0.9.6: language and closing / 言語と終了

English is the initial language. Select English or 日本語 in setup, review, or Editor. Close screen keeps the current in-page inputs (setup) or browser review drafts (comparison); it does not save setup settings or stop the server. You can return to the screen or close the browser tab. Cancel changes restores the last saved setup settings. Stop server separately stops the relevant background service.

初期言語は英語です。設定・比較判定・Editorの言語メニューから切り替えます。「画面を閉じる」は現在の入力／判定下書きを保持しますが、設定の保存やサーバー停止は行いません。戻るボタンで再開するか、ブラウザーのタブを閉じられます。「キャンセル」は最後に保存した設定へ戻し、「サーバー停止」は対象のバックグラウンド処理を止めます。
