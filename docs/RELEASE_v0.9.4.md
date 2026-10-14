# Krea2 Character Catalog v0.9.4

Bug-fix release for Windows, macOS, and Linux. Python 3.10+ is required. Open `open_review.cmd` on Windows, `open_review.command` on macOS, or `sh ./open_review.sh` on Linux after extracting the full catalog ZIP.

## Downloads

- `Krea2-Character-Catalog-v0.9.4.zip`: complete catalog, Editor, images, tags, and workflow examples.
- `Krea2-Character-Catalog-Rejected-Workflows-v0.9.4.zip`: rejected regeneration recipes without rejected images.
- `SHA256SUMS.txt`: checksums for both ZIPs. Older releases are preserved.

## Fixes

- Adds **Stop server** (Japanese: **サーバー停止**) at the top right. Hover text explains that it stops only this catalog background process and leaves the browser tab open. Saved images and catalog data remain intact. Reopen the OS startup file to restart. The read-only static demo hides this control. v0.9.3 downloads remain available.

- The catalog heading now uses the packaged VERSION instead of a hard-coded old version, including after language switching. v0.9.2 downloads are preserved.

- Comparison verdict application is idempotent and retains unrelated state.
- Replacing an Editor image updates automatic fields while retaining manual input; Remove JSON stays removed.
- Prompt extraction follows positive conditioning, supports ConditioningConcat, and ignores malformed optional metadata.
- Workflow-bearing entries export to CSV safely via atomic replacement.
- Hidden cards can be selected and restored together; raw tags are included in search and filtering.
- Edited style names and tags survive rebuilding the read-only demo from the exact tested ZIP.

## Collection and review

3,809 character samples and 110 styles are unchanged. Of 17,416 reviewed image candidates, 3,919 were retained and 13,497 rejected. [Accepted characters](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/blob/v0.9.4/lists/character-pass.csv), [rejected characters](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/blob/v0.9.4/lists/character-fail.csv), [accepted styles](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/blob/v0.9.4/lists/style-pass.csv), [rejected styles](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/blob/v0.9.4/lists/style-fail.csv).

All final selections were made by the author after manual review, including the small AI-assisted subset. These judgments are provisional. Resemblance and manual review do not establish accuracy or training-data inclusion. Please report mistakes with the name and catalog version.

## Validation scope

The same complete ZIP must pass native-startup, core API, headless Chromium, and audit regression tests on Windows Server 2022, macOS 15 Intel, and Ubuntu 24.04 before publication. The audit tests use synthetic SQLite databases and fictitious images. Real AnimaDex installations and cross-OS migration of prepared comparison data remain unverified; AnimaDex is optional. Physical macOS/Linux desktop interaction, security dialogs, default-browser opening, and real file-manager integration remain unverified. No GPU generation or real ComfyUI Queue validation is claimed.

[Read-only live demo](https://ukr8b3g-cmyk.github.io/Krea2-Character-Catalog/) is a simplified static preview; use the ZIP for registration, editing, and local persistence.
