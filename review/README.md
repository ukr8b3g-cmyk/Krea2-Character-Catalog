[日本語 / Japanese](README.ja.md)

# Catalog and Editor usage

Use `open_review.cmd` on Windows, `open_review.command` on macOS, or `sh ./open_review.sh` on Linux from the extracted folder. See [OS setup](../docs/PLATFORMS.md). English is the initial language; Japanese is available from the catalog language menu. The preferred port is 8790. Switch between Characters and Styles, search names and original tags, or filter by copyright and appearance. Copyright sorting places the largest matching groups first.

Filters, language, display settings, and page position are stored in your browser. Visibility, favorites, and star ratings are stored in `outputs/review_state.json` and survive reloads and restarts.

Click an image to enlarge it and copy the reusable prompt or original tags. **Hide does not delete files.** Undo restores the previous hide operation. Hidden list and Show again also restore visibility. Physically removed rejected images are not part of the distribution.

Select several cards to hide them together. Save visible catalog (CSV) exports non-hidden entries in the current tab; Save hidden list (TXT) exports hidden entries. The old Exit review control is not included.

## Register images

1. Click Add image or run `open_editor.cmd`.
2. Choose or drop a WebP, PNG, or JPEG, up to 64 MB.
3. Fill only the fields you want and click Register. All text fields may be blank.

Blank names use the image filename; blank copyrights use Unclassified. Images are copied without recompression. Readable metadata can suggest values only for blank fields. Explicitly cleared fields remain blank when saved.

CSV / workflow JSON (optional) can fill a chosen row from original character tags, styles, the generation example, or your own CSV. Choose column mappings for unfamiliar formats. Choosing a CSV does not register anything. JSON is optional; Remove JSON removes an unwanted attachment.

If an image is already registered, the Editor asks whether to use it or add a separate entry. A duplicate is saved only after Add a separate entry. View in catalog opens the saved card.

## Edit and exit

Click a card, then Edit, to change its name, copyright, reusable prompt, and tags in the information panel. The green Save changes button at the bottom right applies the changes. The orange Cancel (discard changes) at the bottom left discards unsaved changes and returns to saved information. The blue Close (keep draft) at the top right, or Esc, closes while keeping a draft; opening the same image resumes it. Change entry type through the separate Editor.

In the separate Editor, Close (keep draft) preserves the chosen image, text, and attached JSON as a browser draft. If the browser cannot close the tab, the Editor returns to the catalog. Drafts belong to the same browser and catalog URL and are not registered entries. Cancel (discard inputs) removes unsaved inputs and the draft before leaving. Clear text fields clears text while continuing the edit. Saved cards are preserved.

Language and theme are inherited from the catalog. The Editor does not add separate switches. Its image-and-information layout follows the catalog detail panel. Browser-tab close or F5 may require selecting the image again; use the Editor's Close control to keep the image draft.

Edits affect only changed fields. Images, generation records, favorites, visibility, and ratings are retained. Open original image, Open image folder, and Open workflow JSON (when available) provide access to saved files. Open image folder selects the file in Explorer on Windows, reveals it in Finder on macOS, and opens its parent directory on Linux when a desktop file manager is available.

## Python and storage

The catalog and Editor share one launcher. It checks Python 3.10+, Pillow >=10,<13, and WebP support, reuses a compatible existing Python, or creates a private `.venv` as needed. Initial dependency installation needs internet access. Python itself is not bundled. Set `KREA2_CATALOG_PYTHON` or use the `-Python` argument to `tools/open_review.ps1` to select an interpreter.

An already-running service for this same folder is reused. An occupied preferred port results in a free port, without stopping another service. For startup failures, inspect `outputs/review_server.err.log`. To run in a terminal, use `python -B review/server.py --root . --port 8790` and stop with Ctrl+C. A background launcher service remains running when its browser tab is closed.

Back up `outputs/user_catalog.json`, `outputs/user_items/`, `outputs/user_catalog_edits.json`, and `outputs/review_state.json`, preferably by copying the entire catalog folder. See the [main README](../README.md) and [upgrade guide](../docs/UPGRADING.md).
