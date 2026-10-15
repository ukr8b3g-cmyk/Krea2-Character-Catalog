# Krea2 Character Catalog v0.9.6

English-first UI corrections for Windows, macOS and Linux. Python 3.10+ is required.

- The catalog, Editor, comparison setup and comparison review initially open in English. Use the language menu to switch to Japanese.
- Comparison review now localizes decisions, counts, captions, AI suggestion labels, export controls and draft messages. Review language and choices survive reload.
- Editor has its own language selector; changing language keeps image and typed inputs.
- Close screen, Cancel changes and Stop server are separate actions. Closing keeps the current inputs or review drafts; cancel restores saved setup settings. Server shutdown has a separate colored control and localized hover text.
- When the browser does not allow a tab to close programmatically, Close screen shows a closed-screen notice and Return button. You may close the tab yourself. It does not silently stop the background server.
- Export confirmed selections saves JSON; applying verdicts to the catalog remains a separate explicit action.
- Improved narrow layouts and finished-ZIP setup/review regression tests.

All accepted images and catalog metadata remain unchanged: **3,809 characters + 110 styles**. Rejected regeneration workflows are a separate ZIP. Previous releases and downloads are retained.

## Downloads and startup

Download **Krea2-Character-Catalog-v0.9.6.zip**, extract the whole archive and open the OS-labelled **START_HERE** file. The optional comparison tool remains separate in **AnimaDex-Comparison**, with its own **START_COMPARISON** entry.

- [Read-only live demo](https://ukr8b3g-cmyk.github.io/Krea2-Character-Catalog/) — a simplified static preview; no local Python editing or comparison services.
- [README and setup](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog#readme)
- [Previous releases](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/releases)

## Verification limits

Publication is gated on the exact completed ZIP passing Windows Server 2022, macOS 15 Intel and Ubuntu 24.04 jobs. Native OS launchers and disposable Chromium are exercised; comparison tests use a fictitious SQLite DB and synthetic images. Physical Mac/Linux desktop double-click behavior, OS security dialogs, default-browser/file-manager integration, real AnimaDex installations and comparison artifact migration across OSes are not manually verified. These tests do not establish character or style accuracy. The exact successful release-validation run and per-OS reports are linked below by the publishing workflow.
