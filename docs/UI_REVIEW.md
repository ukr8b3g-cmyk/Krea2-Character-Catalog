# UI review after v0.9.5

This source change does not replace the published v0.9.5 ZIP.

## Screens and behavior

- Catalog: existing English default, English/Japanese selector, image details, Editor entry, reversible hide and explicit Stop server retained.
- Editor: added an English/Japanese selector; language changes keep image and inputs. Existing Close (keep draft), Cancel (discard inputs), and Save remain separate.
- Comparison setup: English default; English/Japanese selector; file picker explicitly asks for a database file when appropriate. Cancel changes restores the last saved settings. Close screen keeps current in-page inputs without saving settings.
- Comparison review: English default; all controls, counts, captions, draft messages, AI labels and decisions switch languages. Language choice and decision drafts survive reload. Export confirmed selections saves JSON and does not apply decisions.
- Close screen returns to a closed-screen notice with a Return button. It does not stop a background server. The user may close the browser tab; arbitrary browser tabs cannot reliably be closed by JavaScript.
- Stop server is a separate colored action with an explanation on hover. In review it is placed in the footer, away from decisions/export.
- Both setup and comparison retain keyboard focus indicators and adapt to narrow screens.

## Local validation

- Windows Python unittest suite: 30 passed.
- Isolated Chromium with synthetic SQLite/images: folder selection, pairing, two decoded images, settings persistence, English defaults, Japanese/English switching, decision persistence after reload/close, confirmed JSON export.
- Additional isolated checks: catalog English default, Editor translation preserving typed inputs, Cancel restoring saved settings, storage-failure close warning with cancel preserving the page, no JavaScript errors, 390px layouts for catalog/Editor/setup/comparison.
- These are software browser tests, not human Mac/Linux desktop checks. The added distributed-ZIP setup CI exercises English defaults, switching, close/reopen, decision persistence and narrow layouts on each OS. CI success must be checked separately.

Original catalog, Legacy, user DB/images, accepted/rejected verdicts, favorites, and ratings are outside this patch.
