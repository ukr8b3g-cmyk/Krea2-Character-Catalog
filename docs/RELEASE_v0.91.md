[日本語 README](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/blob/v0.91/README.ja.md) · [English README](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/blob/v0.91/README.md)

**Windows, macOS, and Linux — one complete catalog ZIP.** v0.91 adds portable startup, Python/venv handling, service reuse, duplicate-instance protection, and desktop image-folder integration. The catalog UI and included image collection are preserved.

| OS | Start from the extracted catalog folder |
|---|---|
| Windows | Double-click `open_review.cmd` |
| macOS | Double-click `open_review.command`, or run `sh ./open_review.command` in Terminal |
| Linux | Run `sh ./open_review.sh` |

Python 3.10+ is required. A compatible existing Python is reused; dependencies are installed only into a private venv when needed. Use **Add image** for registration or the matching `open_editor` file to open Editor directly. See [platform setup and validation](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/blob/v0.91/docs/PLATFORMS.md).

### Downloads

- **Krea2-Character-Catalog-v0.91.zip**: complete catalog, accepted images, original tag CSVs, all three OS startup files, Editor, and workflow examples.
- **Krea2-Character-Catalog-Rejected-Workflows-v0.91.zip**: separate regeneration JSONs/index; no rejected images. Recipe data is unchanged from v0.9.
- **SHA256SUMS.txt**: checksums for both ZIPs.

Automatic Source code archives contain development code, without the full image collection. Download the named catalog ZIP above. The previous v0.9 release remains available.

### Provisional collection

The selection is incomplete and provisional. Names, character likenesses, tags, and style results may be inaccurate. Please recheck and correct your local copy. Accepted means retained during selection, not guaranteed accurate reproduction.

| Type | Accepted | Rejected | Candidates checked |
|---|---:|---:|---:|
| Characters | 3,809 | 13,122 | 16,931 |
| Styles | 110 | 375 | 485 |
| Total | 3,919 | 13,497 | 17,416 |

[Accepted characters](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/blob/v0.91/lists/character-pass.csv) · [Rejected characters](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/blob/v0.91/lists/character-fail.csv) · [Accepted styles](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/blob/v0.91/lists/style-pass.csv) · [Rejected styles](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/blob/v0.91/lists/style-fail.csv)

### Validation

Publication is gated on automated tests of the same complete ZIP on Windows, macOS, and Ubuntu Linux, including startup, WebP registration, edits, saved state after restart, port conflicts, duplicate startup, shutdown, and private venv setup. Windows browser operation is also checked manually. Finder double-click/security prompts and Linux desktop file-manager GUI behavior are not manually verified. Folder command routing is tested with mocks. These checks do not test GPU image generation.

### Live demo

[Open the read-only live demo](https://ukr8b3g-cmyk.github.io/Krea2-Character-Catalog/). It is a simplified static preview with no Python backend, registration, editing, or deletion. Use the ZIP for the full local application.
