# Windows, macOS, and Linux

One complete catalog ZIP supports all three desktop operating systems. This concerns catalog browsing, registration, and editing. Set up ComfyUI and generation models separately for your own hardware.

## Open the catalog

Extract the complete Release ZIP into a writable folder. The top-level folder is `Krea2-Character-Catalog`.

| OS | Catalog | Direct Editor |
|---|---|---|
| Windows | Double-click `open_review.cmd` | Double-click `open_editor.cmd` |
| macOS | Double-click `open_review.command` | Double-click `open_editor.command` |
| Linux | `sh ./open_review.sh` | `sh ./open_editor.sh` |

For macOS Terminal fallback, run `sh ./open_review.command` or `sh ./open_editor.command` from the extracted folder. Shell startup files use LF newlines and include executable permissions in the ZIP; some extraction tools may remove those permissions. Linux file-manager double-click behavior depends on the desktop environment, so the documented entry is the terminal command.

After startup, the launcher opens your browser at `http://127.0.0.1:8790/`, or another available local port. The actual address is printed. If automatic browser opening is unavailable, copy that address into your browser. The service only listens on the local PC. The launcher remembers the actual port and reuses a matching running service for this same folder.

## Python and dependencies

Python 3.10+ must already be installed. The launcher checks Pillow 10–12 and WebP support. It reuses an existing compatible Python where possible. Otherwise it creates a private `.venv` and installs `tools/requirements-editor.txt` there. The first installation needs internet access. It does not install Pillow into your global Python. If a copied venv belongs to a different OS, a separate `.venv-<platform>` is created instead of deleting it.

If Python is missing, install it from https://www.python.org/downloads/ and reopen the catalog. On Debian/Ubuntu, venv creation may require the matching `python3-venv` package. A Python installation cannot be replaced by creating a venv; the venv is created using your existing interpreter.

Set `KREA2_CATALOG_PYTHON` to your preferred executable, or run:

```sh
python tools/launch_catalog.py --python '<your-python-executable>'
```

Use `python3` on macOS/Linux if necessary. Useful options are `--editor`, `--no-open`, `--port 8790`, `--force-venv`, `--resolve-only`, and `--json`. Paths are derived from the extracted files, not a fixed drive or the current working directory.

## Stop and reopen

Closing the browser tab keeps the catalog service available. To stop only this catalog:

```sh
python tools/launch_catalog.py --stop
```

You can also pass `--stop` to your OS startup file. Other applications and generation services are not stopped. Reopening restores saved entries, edits, visibility, favorites, and ratings.

## Open image folders

Windows selects the image in Explorer. macOS reveals it in Finder. Linux opens the image's parent folder using `xdg-open` when a graphical desktop is available. On a headless system the folder button is disabled; **Open original image** remains available in the browser.

## Validation scope

The release workflow extracts the same complete ZIP on Windows, macOS, and Ubuntu Linux, and checks the native startup entry, service reuse, direct Editor route, WebP registration with blank text fields, editing, persistent visibility/favorites after restart, occupied-port fallback, instance-lock rejection, shutdown, and private venv dependency setup. Test reports are available in GitHub Actions. Desktop folder command selection is checked separately with mocked system calls.

Windows browser operation is also checked manually. **Finder double-click/security prompts and Linux file-manager GUI operation have not been verified manually on a user's desktop.** Automated runtime success does not certify every macOS version, Linux distribution, extraction tool, browser, or CPU architecture. Generation-model GPU compatibility is outside these catalog checks.

## 日本語

Windowsは `open_review.cmd`、Macは `open_review.command` をダブルクリックします。Linuxはフォルダー内で `sh ./open_review.sh` を実行します。Macで実行権限が保持されない場合は `sh ./open_review.command` を使えます。Python 3.10以上を事前に用意し、必要な依存だけ専用venvへ導入します。

3つのOSでZIPの展開・起動・登録・編集・保存復元を自動検証します。Windowsのブラウザー操作は手動確認します。MacのFinderからの起動やセキュリティ確認画面、Linuxのファイルマネージャー操作は実機での手動確認が未実施です。この区別を対応説明に残します。
