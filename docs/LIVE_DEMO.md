# 閲覧専用ライブデモ

このページは閲覧用の簡易ライブデモで、フル機能版ではありません。カタログのPythonバックエンドを動かさず、生成済みの静的データを表示しています。ZIP版とは利用できる機能と保存動作が異なります。 ダウンロード版のすべての機能を試せる画面ではありません。

現在のカタログからGitHub Pages用の静的版を作れます。Pythonバックエンドは含めません。検索、キャラクター／スタイル切替、作品・タグでの絞り込み、拡大、コピーを使えます。削除・非表示・登録・編集の操作は表示せず、保存・削除APIもありません。

## 作成

カタログを起動できるPythonで、カタログのフォルダーから実行します。

```powershell
python tools/build_static_demo.py --dest "../Krea2-Character-Catalog-Demo"
```

出力先はカタログの外にある、新しいフォルダーにします。既存フォルダーの上書き・削除は行いません。現在非表示の項目は含めず、画像の実体とSHAが一致することを確認してコピーします。同じ画像の実体は1つにまとめ、対応するカードは保持します。個人のお気に入り・星評価、バックエンドのトークン、ファイルの絶対パスは公開用JSONに含めません。

Release公開後は、実際のダウンロードURLを追加します。公開前は「ZIP版は公開準備中です」と表示します。

```powershell
python tools/build_static_demo.py --dest "../Krea2-Character-Catalog-Demo-v0.9" --download-url "https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/releases/latest"
```

作成だけではGitHubにアップロードしません。最終選別・画像メタデータ・配布条件を確認してから公開します。現在の検証用デモも暫定の選別結果です。

## ローカル確認とPages

出力フォルダーをHTTPで開いて確認します。file:// で開く方法は使いません。

```powershell
python -m http.server 8000 --bind 127.0.0.1 --directory "../Krea2-Character-Catalog-Demo"
```

ブラウザーで `http://127.0.0.1:8000/` を開きます。終了はCtrl+Cです。PagesのプロジェクトURLでも画像・JSONは相対位置から読み込みます。Pagesの公開時はこの静的出力だけを用い、ローカルカタログ全体やvenv・ログを配置しません。サイト上限1GB以内であること、実際の公開URLで検索・拡大・コピーが動くことを公開時に確認します。
