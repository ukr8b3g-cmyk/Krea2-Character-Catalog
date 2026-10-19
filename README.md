[日本語 / Japanese](README.ja.md)

**v0.9.6 — Windows, macOS, and Linux startup files in one catalog ZIP.** Requires Python 3.10+ and a web browser. English is the default interface language.

**New in v0.9.6:** English is the initial language in the catalog, Editor, comparison setup and comparison review. Use the English/Japanese selector to switch. **Close screen** keeps the current screen inputs or review drafts; **Cancel changes** restores saved setup settings; **Stop server** separately ends the background process. Comparison exports save confirmed JSON and do not apply verdicts to the catalog. [UI behavior and validation](docs/UI_REVIEW.md).

**Startup and earlier improvements retained:** Clear OS-labelled startup files, a clean download folder, and a separate comparison tool with its own clear startup files. **Earlier fixes retained:** The complete ZIP includes [comparison, Editor, prompt extraction, CSV export, hidden restoration, tag search, and demo consistency fixes](docs/AUDIT_FIXES.md). Previous releases remain available. The live demo is rebuilt from the same tested ZIP.

| Your OS | Open this file in the extracted `Krea2-Character-Catalog` folder |
|---|---|
| Windows | Double-click `START_HERE - Windows.cmd`. |
| macOS | Double-click `START_HERE - macOS.command`. If executable permissions were not preserved, use the Terminal command below. |
| Linux | Open a terminal in this folder and run `sh './START_HERE - Linux.sh'`. |

After startup, click **Add image** to register an image; click a saved image and choose **Edit** to change it. You do not need to find a separate Editor startup file. All three platforms open the same local browser interface. See [platform setup and test coverage](docs/PLATFORMS.md).

Publication of the v0.9.6 ZIP requires Windows Server 2022, macOS 15 Intel, and Ubuntu 24.04 CI tests. See the [exact release validation run and downloadable OS reports](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/releases/tag/v0.9.6#release-validation) and [coverage details](docs/PLATFORMS.md#validation-scope). macOS/Linux desktop double-clicking, security/permission dialogs, default-browser opening, and native file-manager integration remain **unverified on physical desktops**. AnimaDex is an optional, separate workflow.

<img width="1269" height="743" alt="{604FEE72-032C-4BC9-8AA0-8E2AAB612015}" src="https://github.com/user-attachments/assets/e1904ff8-181d-4792-bb61-95b17fddf90a" />


# Krea2 Character Catalog v0.9.6

A local catalog of Krea2-generated character and style samples, with searchable tags, reusable prompts, and an image registration and editing tool for Windows, macOS, and Linux. **English is the default interface language.** Japanese is also available; your language choice is remembered.

**This catalog is incomplete and provisional.** I personally reviewed all roughly 17,000 candidates and made every final selection decision. AI assistance was tried on a small subset, but those results were checked by me too; no entry was accepted solely on an AI judgment. I am not familiar with every character, and some were provisionally retained based on color, shape, and overall resemblance after checking references. Manual review does not guarantee accuracy or prove that a character appeared in the model's training data. Names, tags, likenesses, and styles may be wrong. The review took over a week, and another complete pass is not practical for me alone. Please recheck your local collection and report mistakes with the character/style name and catalog version. Corrections and suggestions are welcome.

## Downloads and live demo

- **[Download v0.9.6: complete catalog ZIP and rejected-workflow ZIP](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/releases/tag/v0.9.6)**
- **[Latest release](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/releases/latest)**
- **[Read-only live demo](https://ukr8b3g-cmyk.github.io/Krea2-Character-Catalog/)**

Download `Krea2-Character-Catalog-v0.9.6.zip` for the complete application. It includes the accepted images, original tag CSVs, workflow examples, and Catalog Editor. Extract it to obtain a folder named `Krea2-Character-Catalog`. Python and generation models are not bundled.

GitHub's **Code → Download ZIP** and automatic **Source code** archives contain the development source, without the image collection or full tag dataset. Use the named ZIP attached to a Release for the complete catalog. Each release keeps its own versioned downloads. `SHA256SUMS.txt` provides checksums for the two ZIPs.

## Quick start

1. Extract the entire ZIP. Do not run it from inside the archive.
2. Use the startup file for your OS in the table above.
3. Switch between **Characters** and **Styles**, and search or filter by name, copyright, or appearance tags.
4. Click an image to enlarge it and copy its reusable Krea2 prompt or original tags.

**Start here:** Open the file with your OS in its name. The `app` folder contains internal files and saved images; you do not need to open it to use the catalog. Keep the whole extracted folder together.

```text
Krea2-Character-Catalog/
  START_HERE - Windows.cmd
  START_HERE - macOS.command
  START_HERE - Linux.sh
  README.md
  README.ja.md
  AnimaDex-Comparison/  # optional comparison setup and startup
  app/
```

**To stop:** Click **Stop server** in the catalog. The browser tab stays open; saved images and decisions remain intact. Reopen the same START_HERE file to use it again.

The preferred local address is `http://127.0.0.1:8790/`. If the port is occupied, the launcher chooses an available port and opens the actual address. It reuses an already-running service for this same catalog and does not replace other applications. The server listens only on the local PC.

The launcher checks for **Python 3.10+**, **Pillow 10 to below 13**, and WebP support. It prefers an existing compatible Python. When necessary, it creates a new private `.catalog-venv` using a detected Python and installs dependencies there, without installing Pillow globally or changing any existing venv. Old or incomplete environments are left intact. The first dependency installation needs internet access. If Python is missing or older than 3.10, use the official [Windows installer](https://www.python.org/downloads/windows/), [macOS installer](https://www.python.org/downloads/macos/), or [Linux installation guide](https://docs.python.org/3/using/unix.html). **After installation, open the same startup file again.** Each startup file checks runnable interpreter versions before loading the Python launcher, and can select a compatible version when an older Python is also installed. Invalid explicit interpreter paths are reported rather than silently ignored. Interactive error windows wait for Enter; redirected input and CI do not wait.

See [distinct startup error messages and remedies](docs/PLATFORMS.md#startup-errors).

To choose a specific Python, set `KREA2_CATALOG_PYTHON`, or run this from the extracted folder with your interpreter path:

```sh
python app/tools/launch_catalog.py --python '<your-python-executable>'
```

On macOS/Linux, use `python3` if `python` is unavailable. If macOS does not allow double-clicking, run `sh './START_HERE - macOS.command'` from this folder. The ZIP includes executable permissions, but some extraction tools do not preserve them.

To stop only this catalog's background server, click **Stop server** in the top-right corner (hover for the explanation), or run `python app/tools/launch_catalog.py --stop` (or `python3` on macOS/Linux). Closing the browser tab leaves the local service available for reopening.

Search filters, language, display settings, and page position are saved in your browser. Hidden entries, favorites, and star ratings are saved locally. The download starts without personal favorites, ratings, or editor drafts.

## Using the catalog

Select images to hide them together. **Hide does not delete the image file.** Use **Hidden list**, **Show again**, or **Undo** to restore visibility. Undo restores the entire previous hide operation. Export the visible catalog as CSV or the hidden list as TXT. Copyright sorting orders groups by the number of matches under the current filters.

See [Catalog and Editor usage](review/README.md) for the controls and saved-state behavior.

## Add and edit your own images

**Krea2 Catalog Editor** registers your generated images and lets you organize their name, copyright/category, reusable prompt, and tags. It does not generate images or automatically judge them.

1. Click **Add image** at the top of the catalog, or use the Editor startup file for your OS.
2. Choose or drop an image. **WebP is recommended**; PNG and JPEG are supported. Maximum size: 64 MB per image.
3. Enter only the information you need, then click **Register**.

An image alone is enough. Every text field is optional. A blank name uses the filename, and a blank copyright uses **Unclassified**. The original file is copied without recompression.

Expand **CSV / workflow JSON (optional)** to search the supplied CSVs or your own CSV. For unfamiliar CSVs, choose the column mapping. Selecting a CSV does not register anything automatically. Workflow JSON is optional and can be removed. If the image already exists, choose the existing entry or explicitly add a separate entry.

Click a registered card to open its information panel, then click **Edit** to change its information inside that panel.

| Control | Result |
|---|---|
| **Register** / green **Save changes** | Saves the inputs to the catalog. |
| Blue **Close (keep draft)** / Esc | Closes while keeping a draft. Unsaved changes are not applied. |
| Orange **Cancel (discard changes/inputs)** | Discards unsaved inputs and the draft; saved information remains. |
| **Clear text fields** | Clears only the text fields and continues editing. |

Edits are saved separately and affect only changed fields. An empty registration file does not clear the existing catalog. Original images, generation records, visibility, favorites, and ratings are preserved.

## Files and storage

| Location inside the extracted folder | Contents |
|---|---|
| `app/outputs/staging/<run>/images/` | Included accepted images, reusable prompts, and original tags. |
| `app/outputs/staging/<run>/generation_manifest.json` | Links between included images and their records. |
| `app/outputs/user_items/<uuid>/` | Images and optional JSON added through the Editor. |
| `app/outputs/user_catalog.json` | Added entries. |
| `app/outputs/user_catalog_edits.json` | Changes to existing entries. |
| `app/outputs/review_state.json` | Your hidden entries, favorites, and star ratings. |
| `app/original_tags/anima_characters.csv` | Existing original character-tag CSV, included in the complete Release ZIP. |
| `app/original_tags/styles/selected_all_styles.csv` | Optional style suggestions, included in the complete Release ZIP. |
| `comfyui/workflows/` | Shared ComfyUI workflow examples. |
| `lists/` | Accepted/rejected name and copyright lists, and review counts. |

The existing original-tag CSV uses **`tag,category,count,insert_mode`**. The `tag` field begins with character and copyright identities, followed by appearance tags. The generation input example, `comfyui/inputs/thumbnail_prompts.csv`, instead uses **`id,prompt`**. Reusable prompts, original tags, and the actual generation prompt serve different purposes.

For backup or moving to another PC, copy the entire catalog folder. Extract upgrades into a separate folder, keep the old version, and transfer your added images, edits, and review state. See [Updating and backup](docs/UPGRADING.md).

## Generate and regenerate

The character and style samples were generated in ComfyUI. The saved API metadata in **3,913 of the 3,919 included images** records the same model, text encoder, and VAE below. All six included character/style workflow JSONs use this combination. The remaining six older images lack API metadata, so their original loader settings could not be confirmed from the images.

| Component | Recorded filename / setting |
|---|---|
| Krea2 Turbo model | `krea2_turbo_int8_convrot.safetensors` (workflow model folder: `krea2`) |
| Text encoder | `qwen3vl_4b_fp8_scaled.safetensors`, CLIP type `krea2` |
| VAE | `qwen_image_vae.safetensors` |

These are the filenames recorded in the workflows, including the quantized model/encoder variants used for this collection. Model weights are not bundled. Inspect the [character workflow](comfyui/workflows/Krea2%20Catalog%20Thumbnails.json) and [style workflow](comfyui/workflows/Krea2%20Style%20Catalog%20Dedicated.json), and adjust loader filenames for your own ComfyUI installation. These metadata checks establish the recorded generation setup; they do not establish that a character was present in the model's training data.

See [Generation and registration](README_GENERATION.md) and [ComfyUI workflows](comfyui/README.md) for the models, settings, examples, and required nodes. Set up your own generation environment, render an image, then register it through the Editor.

The detail panel offers **Open original image** and **Open image folder**. Where a WebP contains generation metadata, drag it into a compatible ComfyUI installation to load the workflow.

The distribution copy removes the original PC's CSV paths from image metadata. Character workflows use the saved, resolved generation text through `manual_prompt`. Install or update the bundled `ComfyUI-Krea2-Catalog-Tools` under your ComfyUI `custom_nodes` folder and restart ComfyUI. Adjust model names and missing nodes for your environment. The compressed pixel data has not been changed. Some older images have no generation metadata, so not every image can reproduce its complete original settings.

Rejected images and blank rejected cards are excluded from the catalog ZIP. Their regeneration JSONs are available separately as **`Krea2-Character-Catalog-Rejected-Workflows-v0.9.6.zip`**. Of these, 13,486 are based on saved generation metadata, and 11 older entries are editable templates without original metadata. Running a rejected recipe does not guarantee an accepted result. You can use the recipes without adding rejected images back to the catalog.

## Simplified live demo

The GitHub Pages site is a **simplified read-only demo, not the full application**. It displays prebuilt static data and **does not run the catalog's Python backend**. Its features and saving behavior differ from the local ZIP application.

Try searching, filtering, sorting, character/style switching, enlarging images, and copying prompts. Public data cannot be deleted, hidden, registered, or edited. Mutation controls and save APIs are absent. Use the local ZIP application to add your own images or change information. The online demo opens on **Characters** each time, even after a previous Styles session. Other demo display preferences are stored only in your own browser. The local application can remember its last tab.

See [Building the static demo](docs/LIVE_DEMO.md).

## Optional AnimaDex comparison

[Set up comparison without Codex or an installed skill](docs/COMPARISON_MANUAL.md).

The layout and organization of this catalog were inspired by [AnimaDex](https://animadex.net/). Normal registration and editing do not require AnimaDex or Codex.

**AnimaDex integration is optional and unverified on Linux/macOS. It is excluded from the core catalog's three-OS verification.** Database reading, reference-image matching, comparison pages, confirmed verdict application, and moving comparison paths/settings between OSes are not covered by the release CI.

For optional comparisons, install both catalogs locally and use the supplied [krea2-animadex-review skill](skills/krea2-animadex-review/SKILL.md). Configure paths and ports for your own environment, reusing an existing AnimaDex installation. See [Comparison setup and applying decisions](docs/COMPARISON_SKILL.md).

AI suggests candidates; a human makes the final decision. Only selected, confirmed pass/fail decisions are applied. Unselected, held, or empty data does not alter existing catalog state. References are matched using CSV identity tags and both images, rather than a name alone. Identity matching by the skill is not itself AI visual judgment. The current comparison adapter supports characters; style references need separate handling.

## Review lists and counts

| Type | Accepted | Rejected | Candidates checked |
|---|---:|---:|---:|
| Characters | 3,809 | 13,122 | 16,931 |
| Styles | 110 | 375 | 485 |
| **Total** | **3,919** | **13,497** | **17,416** |

- [Accepted characters](lists/character-pass.csv)
- [Rejected characters](lists/character-fail.csv)
- [Accepted styles](lists/style-pass.csv)
- [Rejected styles](lists/style-fail.csv)
- [Counts as JSON](lists/summary.json)

Counts refer to image candidates in the current reviewed set. Alternate outfits can be separate candidates. Retired or duplicate older style samples are excluded. There are no held or undecided candidates in this release scope. **Accepted means provisionally selected, not guaranteed accurate reproduction.** CSV lists contain names and copyrights/categories; internal record IDs and image hashes are omitted from these human-readable lists.

In these style checks, many artist styles associated with Pixiv or Danbooru were difficult to reproduce, while some well-known manga artists and illustrators had similar results. This is an observation from this catalog, not evidence establishing which artists were present in the model's training data.

Rights to characters, works, models, and third-party tag data remain with their respective owners. Check the applicable terms with each provider. To report a wrong name, tag, or generated result, include the entry name and catalog version in an Issue.

## Optional AnimaDex comparison

Open `AnimaDex-Comparison/START_COMPARISON` for your OS to select folders on screen. No AI assistant or JSON editing is needed. The optional skill automates the same setup. [Setup guide](docs/COMPARISON_MANUAL.md).

## Before using optional AnimaDex comparison

AnimaDex is a separate application: [website](https://animadex.net/), [local application and installation instructions](https://github.com/zetaneko/AnimaDex), [official dataset import guide](https://github.com/zetaneko/AnimaDex/blob/main/docs/import-from-site.md).

1. Install/configure AnimaDex using its own instructions. Start it once and confirm its local catalog opens correctly.
2. Import/download the character metadata and reference thumbnails to your PC. The starter samples are not the full reference collection. Follow AnimaDex's current offline dataset export/import procedure; download the images needed for your comparisons, and confirm they display locally. Merely opening the website does not download a local reference library.
3. Open this catalog's `AnimaDex-Comparison/START_COMPARISON` file and select that AnimaDex installation. If its DB/images use a custom data directory, select them under Advanced settings.

**AnimaDex does not need to remain running.** This tool reads its local SQLite database read-only and serves local reference images directly; it does not call AnimaDex's web server. Keep the downloaded DB and image files in place. Creating/rebuilding pairs and applying decisions require the selected Krea2 catalog to be running. Viewing an already prepared comparison does not require either application's main server.

If installation is confusing, you can ask an LLM assistant such as ChatGPT, Claude, or Codex to help set up AnimaDex using its official instructions. For example: “Help me install AnimaDex on my OS, import its character metadata and thumbnails locally, and confirm the local gallery works before configuring Krea2 comparison.” Tell it your OS and chosen folders; keep export tokens and other credentials private. This catalog does not install AnimaDex automatically.

[Previous versions and downloads / 旧版のダウンロード](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/releases) — existing releases remain available.

## License

The maintainer-authored application code, documentation, tools, tag data, prompts, and catalog lists are licensed under the [MIT License](LICENSE). The existing 3,919 catalog images are a separate collection and are not granted a blanket MIT license here. Third-party character, work, model, and source-data rights remain unchanged. See [NOTICE.md](NOTICE.md) for scope.
