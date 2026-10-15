# v0.9.5 platform setup and verification

The complete ZIP includes Windows, macOS, and Linux launchers. Python **3.10 or later** and a web browser are required. Python itself and generation models are not bundled. The catalog does not install or upgrade your existing Python environment.

## Open the catalog

Extract the complete ZIP into a writable folder named `Krea2-Character-Catalog`.

| OS | Catalog | Direct Editor |
|---|---|---|
| Windows | Double-click `START_HERE - Windows.cmd` | Use Add image in the catalog |
| macOS | `START_HERE - macOS.command`, or Terminal: `sh './START_HERE - macOS.command'` | Use Add image in the catalog |
| Linux | Terminal: `sh './START_HERE - Linux.sh'` | Use Add image in the catalog |

macOS double-click is intended but not physically verified. Extraction tools may remove executable permission; using `sh` does not require that permission. Linux file-manager double-click behavior depends on the desktop; use the documented terminal command. General desktop OS warnings, permission dialogs, default browser opening, and actual Finder/Explorer/xdg-open integration are distinct from headless CI tests.

The preferred address is `http://127.0.0.1:8790/`. A busy port results in a different free local port. The actual address is printed, and a matching service for this catalog folder is reused. Other applications are never terminated. Closing the browser tab leaves this catalog service available. Pass `--stop` to the OS startup file to stop this catalog only.

## Install Python first

- Windows: [official Python downloads](https://www.python.org/downloads/windows/). Install a supported Python and enable its PATH option. A registered Python launcher installation is also detected. Windows App Execution Alias stubs are skipped.
- macOS: [official Python downloads](https://www.python.org/downloads/macos/). Install a supported Python and reopen Terminal if necessary.
- Linux: [official Unix installation guidance](https://docs.python.org/3/using/unix.html). Use your distribution package manager to install Python 3.10+ and its matching venv/ensurepip package; on Ubuntu/Debian this is typically `python3-venv`.

**After installation, open the same startup file again.** Before loading any Python catalog code, the native startup checks executable versions. It searches multiple PATH candidates and, on Windows, the registered installed interpreter list; it skips old candidates in a mixed environment. It does not download or install Python itself. If you installed Python in a custom location not on PATH, set `KREA2_CATALOG_PYTHON` to its complete executable path.

An explicit `KREA2_CATALOG_PYTHON` or `--python` path is validated and not silently replaced. Interactive startup errors wait for Enter before closing. CI (`CI` set), redirected input/output, and `KREA2_CATALOG_NO_PAUSE` do not wait for input.

## Private dependencies

An existing Python with Pillow 10–12 and WebP support can be reused. Otherwise the launcher creates a **new** `.catalog-venv` (or `.catalog-venv-1`, etc.) and installs Pillow there. Internet access is needed for that installation. It never runs pip in a pre-existing environment, never deletes an old `.venv`, and never installs packages globally. An incomplete environment from a failed setup is retained; another new private folder is used on retry. After a successful retry, unused failed private environments may be removed manually while the catalog is stopped.

Useful startup arguments are `--editor`, `--no-open`, `--port 8790`, `--force-venv`, `--resolve-only`, `--stop`, and `--json`. Paths derive from the extracted files, independent of the working directory or a specific drive.

## Startup errors

| Message / exit code | Cause and action |
|---|---|
| `PYTHON_MISSING` / 10 | No runnable Python found. Use the OS-specific official link, then reopen this startup file. |
| `PYTHON_OLD` / 11 | Only an older Python found, or explicitly selected Python is below 3.10. Install/select a compatible Python, then reopen. |
| `PYTHON_PATH` / 12 | An explicit path is missing or cannot execute. Correct or unset `KREA2_CATALOG_PYTHON` / `--python`. |
| `VENV_MISSING` / 13 | Python lacks venv/ensurepip or cannot build a private environment. Install the matching venv package or select a complete Python installation. |
| `WRITE_PERMISSION` / 14 | Runtime folder is not writable. Extract into a writable user folder. Editor saves can also fail because another program locks the destination; close that program and retry. Existing saved data is preserved. |
| `PILLOW_WEBP` / 15 | Installed private dependency cannot provide Pillow 10–12 and WebP. Choose a compatible existing interpreter. |
| `NETWORK` / 16 | Dependency download failed due to a detected connection/proxy/certificate problem. Check connectivity, then reopen. |
| `DEPENDENCY_INSTALL` / 17 | Other dependency installation failure. Read the diagnostic and select a supported interpreter. |

## Validation scope

For a published v0.9.5 ZIP, see the [exact GitHub Actions run and downloadable per-OS reports linked in Release validation](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/releases/tag/v0.9.5#release-validation). Publication requires the following tests to pass on **Windows Server 2022, macOS 15 Intel, and Ubuntu 24.04**, using Python 3.12 and a real Python 3.9 negative-test interpreter. The same built ZIP is extracted and invoked through `.cmd`, `.command`, or `.sh` respectively; the server is not the only launch entry under test.

| Check | Method / scope |
|---|---|
| Startup, catalog and style listing, Editor startup, double startup, port conflicts, stop/restart | Distributed OS entry files; HTTP assertions and real socket conflicts. |
| Search, image registration, editing, saving, reload | Disposable headless Chromium, on the catalog started by its OS entry file. |
| Persisted entries/edits, hidden/favorite state after backend restart | HTTP assertions after stopping/reopening the same extracted catalog. |
| Python unavailable, 3.9 only, mixed 3.9/3.12, invalid env and CLI paths | Controlled PATH using actual installed interpreters, and native startup files; CI has no interactive pause. |
| Missing venv/ensurepip, download failure, WebP capability failure | External test-only `sitecustomize` fault fixtures in child interpreters; no source patch or modification of installed Python. |
| Old 3.9 venv / incomplete existing venv | Actual old venv plus sentinel files remain unchanged; a fresh private environment is built. |
| Japanese/spaced paths and mixed-case image extensions | Actual extraction paths and registration filenames; PNG/JPEG/WebP bytes are unchanged. |
| Save failure protects data | Real POSIX directory permission denial or a Windows file handle preventing destination replacement. Saved file bytes and catalog values remain unchanged. |
| Folder-command routing / no reverse DNS / file locks | Separate unit tests; native GUI commands are mocked. |

**Not physically verified on macOS/Linux:** general desktop double-clicking, OS security and permission dialogs, opening the default browser, and interaction with a real Finder or Linux file manager. Headless Chromium success does not establish those behaviors. Only the listed runner OS versions/architecture and functions are automatically verified. Windows physical browser checks are separate from CI. GPU generation, every extraction utility, every distribution, and every Python 3.10+ version are not certified.

## AnimaDex is separate

The v0.9.5 release includes [audit regression tests](AUDIT_FIXES.md) using a temporary SQLite DB, fictitious image pairs, the real catalog HTTP API, and headless Editor operations. These run against the candidate ZIP on each CI OS. This limited contract coverage does not certify a real AnimaDex installation, the comparison page's desktop behavior, or relocation of prepared absolute paths between OSes. The release includes these checks in addition to the core startup and Editor tests.

**AnimaDex integration is optional and unverified on Linux/macOS.** It is excluded from the core catalog three-OS support claims and release tests. SQLite DB reading, image-reference matching, comparison pages, applying confirmed verdicts, case/separator differences, absolute paths, and comparison migration/rebuilding across OSes have not been exercised in this CI. Use local configuration and regenerate comparisons after changing environments. No real user DB or personal reference images are included in CI.

## 日本語

v0.9.5の1つのZIPに3OSの起動ファイルを同梱します。Python 3.10以上は別途必要です。未導入・旧版・無効な指定・venv不足・書込権限・Pillow/WebP不足・通信失敗を区別して案内します。導入後は同じ起動ファイルを再度開いてください。旧Python・既存venvを変更せず、依存は新規専用環境にのみ導入します。

上の表は公開ZIPに対する自動試験の範囲です。Mac/Linuxの通常のデスクトップ操作とOSの警告画面・標準ブラウザー・ファイルマネージャー連携は実機未確認です。AnimaDex連携は別の任意機能で、Linux/macOSでは未検証です。

The v0.9.5 release CI also tests the separate comparison setup launcher and HTML folder chooser against a fictitious SQLite DB and synthetic image pair on each OS. Passing these tests establishes the listed synthetic workflow only; real AnimaDex installations and physical desktop integration remain outside that scope.
