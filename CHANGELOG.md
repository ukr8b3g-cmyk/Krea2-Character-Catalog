# Changelog

## v0.9.3 — 2026-10-14

- Catalog headings follow the packaged VERSION in both languages; the live demo retains its static-mode notice.
- Native ZIP browser tests now verify the visible heading matches VERSION before and after a language change.
- Includes all v0.9.2 fixes; v0.9.2 and earlier downloads are preserved.

## v0.9.2 — 2026-10-14

- Includes all comparison and Editor audit fixes: idempotent confirmed verdicts, image replacement metadata, positive prompt tracing, and persistent Remove JSON.
- Handles ConditioningConcat and malformed optional PNG prompt metadata conservatively.
- Atomic CSV export accepts workflow-bearing entries without damaging previous exports.
- Hidden cards support bulk selection and restoration; original tags are searchable and facets no longer require identity tags at the beginning.
- Static demos retain manually edited style metadata and identify their release version.
- VERSION drives package filenames, OS tests, Release creation, and demo deployment. Existing releases are never overwritten.
- The unchanged image collection still contains 3,809 characters and 110 styles.

## v0.9.1 — 2026-10-13

- Formal semantic version; v0.9 and v0.91 published downloads are retained.
- Native startup verifies Python 3.10+ before importing catalog code, selects compatible mixed installations, and provides OS-specific installation guidance without CI input waits.
- Explicit path, venv, permission, Pillow/WebP, and download errors are distinguished. Existing interpreters and virtual environments are never modified by dependency setup.
- Release CI expands real ZIP/startup coverage to Python 3.9/mixed installations, dependency faults, Unicode/case-sensitive filenames, PNG/JPEG/WebP preservation, headless browser search/edit/save, and data protection on write failure.
- AnimaDex Linux/macOS support remains unverified and separate from core catalog support. Physical Mac/Linux desktop integration remains unverified.

## v0.91 — 2026-10-13

- One catalog ZIP for Windows, macOS, and Linux, with OS-specific Catalog and Editor startup files.
- Shared Python launcher reuses a compatible existing interpreter or prepares a private venv; no system-wide Pillow installation.
- Persistent service reuse, cross-platform instance locks, occupied-port fallback, explicit shutdown, and portable paths.
- Explorer/Finder integration and Linux image-folder opening when a desktop file manager is available.
- Native-OS automated ZIP/runtime checks; macOS Finder double-click and Linux file-manager GUI behavior remain unverified manually.
- English and Japanese startup instructions. Included images, tags, judgments, and workflows are unchanged from v0.9.


## v0.9 — 2026-10-13

Initial public release. Includes 3,809 provisional character images and 110 style images, a Windows local catalog, the standard image-registration Editor, inline metadata editing, portable ComfyUI workflow examples, four decision lists and an optional AnimaDex comparison skill.

The image pixels are retained while PC-specific generation-metadata paths are removed. Character workflow metadata uses its saved resolved prompt instead of the original PC's CSV. Rejected regeneration workflows are provided in a separate ZIP. The GitHub Pages catalog is a simplified read-only demo.

- English is the initial UI language; the online demo always opens on Characters.
- Completed distribution manifests display the saved-image status.
