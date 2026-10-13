---
name: krea2-animadex-review
description: Compare locally installed Krea2 character catalog images with AnimaDex references, review AI suggestions with a human, and apply only confirmed selected verdicts while preserving unrelated catalog state. Use for optional comparison workflows, not ordinary image registration or generation.
---

# Krea2 / AnimaDex character review

Use the catalog's standard Editor for adding images and editing metadata. This optional skill pairs existing character images with a local AnimaDex installation and applies explicit selected decisions. It does not install AnimaDex, generate images, restart services, or publish files.

## Find the environment

Use the user's specified folders first. Otherwise check the current catalog folder and its launcher/settings. If AnimaDex's data folder is unknown, request that location only; do not assume a drive, user name, port, or install path. Put environment values in a private copy of [config.example.json](config.example.json), resolving relative paths against that config file. Never include the filled config or generated review folders in a release.

Run `scripts/review.py inspect --config <config>` using the catalog's working Python. The helper reuses the running catalog URL from `outputs/review_service.json` when no URL is configured, verifies `/api/info` against the chosen root, checks the original-tag CSV, and opens AnimaDex SQLite read-only. If the catalog is not running, use its existing launcher; do not stop or replace another user's service.

The bundled adapter supports AnimaDex's `characters` table with `character`, `name`, `trigger`, and `thumbname`. AnimaDex installations with a different schema must be inspected and adapted before pairing. This character adapter does not establish style-image correspondences.

## Prepare and compare

Run `prepare --config <config> --output <new folder outside both catalogs>`, optionally with `--copyright <work>`. The helper checks the first two CSV identity tags and requires one exact AnimaDex trigger after case/whitespace normalization. Ambiguous or missing matches are reported in `unresolved.csv`, not guessed. It records both image SHAs and does not copy images.

Open `pairs.json` to inspect the matched paths. Visually compare both images using the available local image/browser tools. A successful tag match is identity evidence, not proof of visual similarity. Report the actual compared count and elapsed time, including time per compared image when requested. Do not claim AI judging happened merely because the pairing script ran.

Use `serve --review-dir <folder> --port 0` for a local HTTP comparison screen. The review folder records its chosen port in `review-server.json`; restarting the same folder with `--port 0` reuses that address so browser drafts, filters and page position survive. If that port is occupied, inspect its owner rather than stopping it or silently changing the address. Record the printed URL/PID and stop only a service you started when done. The comparison screen stores choices in the browser and exports confirmed selected decisions; it does not automatically change the catalog. The user may also explicitly confirm selected AI suggestions in the conversation.

AI suggestions can be saved in `ai_candidates.json` inside the review folder: an array of `key`, `catalog_image_sha256`, `reference_image_sha256`, `decision` (`match`, `mismatch`, `hold`), and `reason`. They must come from actual two-image comparison. The page accepts only suggestions for the current pair SHAs, labels them as AI suggestions, and leaves final confirmation to the user.

## Apply confirmed choices

Read [references/contracts.md](references/contracts.md) when applying decisions. Require direct user authorization for the selected batch unless already present in the conversation. Run `apply --config <config> --review-dir <folder> --decisions <json> --dry-run` first. Unselected, unconfirmed, and held rows are skipped. A changed or missing image rejects the batch before mutations.

When authorized, rerun without `--dry-run`. The helper snapshots the review-state file outside the catalog, applies only selected matches/restores and mismatches/hides through the catalog's own API, and checks visibility afterward. Metadata, favorites, ratings, generation manifests, and image files are not rewritten. Empty decisions mean no changes, never an empty replacement catalog.

Keep generated review artifacts, snapshots, logs, and local path settings outside the distribution folder. Do not resume or interrupt generation queues for comparison work. Preserve the user's task order and publication restrictions.
