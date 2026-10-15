---
name: krea2-animadex-review
description: Compare locally installed Krea2 character catalog images with AnimaDex references, review AI suggestions with a human, and apply only confirmed selected verdicts while preserving unrelated catalog state. Use for optional comparison workflows, not ordinary image registration or generation.
---

# Krea2 / AnimaDex character review

Use the catalog's standard Editor for adding images and editing metadata. This optional skill pairs existing character images with a local AnimaDex installation and applies explicit selected decisions. It does not install AnimaDex, generate images, restart services, or publish files.

## Human-facing entrypoint

For a request to open a past comparison, find and reopen the existing material first; do not regenerate pairs or overwrite decisions. Do not make the user find a nested HTML file, edit JSON, copy a URL, or run server commands for routine use.

For new distributions, the normal catalog opens from the clearly OS-labelled START_HERE file at the extracted folder's top level. Accept that top-level folder as catalog_root; the helper resolves its internal app folder. Keep implementation files out of the user's startup choices.

Keep the comparison separate from the catalog. After initial setup, prepare leaves START_COMPARISON files labelled by OS at the comparison folder's top level, with internal files under app. The user opens that file to start or reopen the same comparison and uses Stop comparison in the comparison screen to end its background server. Do not add a comparison button or extra startup steps to the main catalog. Verify the actual entrypoint, image pair display, service reuse and stop behavior before calling setup complete. For an older existing comparison, reopen its current screen rather than rebuilding it.

Environment discovery and the commands below are for the assistant or advanced troubleshooting, not mandatory manual steps for the end user. Ask only for a missing folder location, complete the setup, and leave a reusable human-facing entrypoint.

## Two supported setup methods

The complete ZIP includes `AnimaDex-Comparison/START_COMPARISON` for each OS. Without a skill, it opens a folder-selection setup screen, checks connections, and prepares the same bundled HTML comparison. No command or JSON editing is required.

With this skill, discover the selected catalog and AnimaDex folders and use the existing inspect/prepare helpers below. Do not build a different HTML page or require interactive folder picking when the user has already supplied paths. Both methods use the same collect/prepare code and selected-human-verdict apply contract. Leave the prepared workspace's START_COMPARISON files as the everyday entrypoint. For screen-based setup, use the complete ZIP's comparison launcher; root catalog startup remains independent.

## Find the environment

Use the user's specified folders first. Otherwise check the current catalog folder and its launcher/settings. If AnimaDex's data folder is unknown, request that location only; do not assume a drive, user name, port, or install path. Put environment values in a private copy of [config.example.json](config.example.json), resolving relative paths against that config file. Never include the filled config or generated review folders in a release.

Run `scripts/review.py inspect --config <config>` using the catalog's working Python. The helper reuses the running catalog URL from `outputs/review_service.json` when no URL is configured, verifies `/api/info` against the chosen root, checks the original-tag CSV, and opens AnimaDex SQLite read-only. If the catalog is not running, use its existing launcher; do not stop or replace another user's service.

The bundled adapter supports AnimaDex's `characters` table with `character`, `name`, `trigger`, and `thumbname`. AnimaDex installations with a different schema must be inspected and adapted before pairing. This character adapter does not establish style-image correspondences.

## Prepare and compare

Run `prepare --config <config> --output <new folder outside both catalogs>`, optionally with `--copyright <work>`. The helper checks the first two CSV identity tags and requires one exact AnimaDex trigger after case/whitespace normalization. Ambiguous or missing matches are reported in `unresolved.csv`, not guessed. It records both image SHAs and does not copy images.

The assistant can inspect `pairs.json` to verify matched paths; do not send the user there to open the comparison. Visually compare both images using the available local image/browser tools. A successful tag match is identity evidence, not proof of visual similarity. Report the actual compared count and elapsed time, including time per compared image when requested. Do not claim AI judging happened merely because the pairing script ran.

For routine use, open the generated START_COMPARISON entrypoint. The following foreground server command is an advanced diagnostic fallback: use `serve --review-dir <folder> --port 0` for a local HTTP comparison screen. The review folder records its chosen port in `review-server.json`; restarting the same folder with `--port 0` reuses that address so browser drafts, filters and page position survive. If that port is occupied, inspect its owner rather than stopping it or silently changing the address. Record the printed URL/PID and stop only a service you started when done. The comparison screen stores choices in the browser and exports confirmed selected decisions; it does not automatically change the catalog. The user may also explicitly confirm selected AI suggestions in the conversation.

Prepared pairs, settings and assets live under the comparison folder's `app` directory; the helper accepts the outer comparison folder for serve/apply. AI suggestions can be saved in `app/ai_candidates.json`: an array of `key`, `catalog_image_sha256`, `reference_image_sha256`, `decision` (`match`, `mismatch`, `hold`), and `reason`. They must come from actual two-image comparison. The page accepts only suggestions for the current pair SHAs, labels them as AI suggestions, and leaves final confirmation to the user.

## Apply confirmed choices

Read [references/contracts.md](references/contracts.md) when applying decisions. Require direct user authorization for the selected batch unless already present in the conversation. Run `apply --config <config> --review-dir <folder> --decisions <json> --dry-run` first. Unselected, unconfirmed, and held rows are skipped. A changed or missing image rejects the batch before mutations.

When authorized, rerun without `--dry-run`. The dry run reports the current visibility plan and counts of changes and unchanged items. The helper snapshots state outside the catalog and sends only necessary restores/hides through the catalog's API: an already visible match or already hidden mismatch needs no visibility write, but its confirmed judgment is still recorded. It rechecks image identities before each write and at completion. After an interruption, inspect `apply-checkpoint.json`, run the dry run again, and retry the same confirmed export; the helper recomputes remaining changes from the live catalog rather than blindly replaying prior operations. Metadata, favorites, ratings, generation manifests, and image files are not rewritten. Empty decisions mean no changes, never an empty replacement catalog.

Keep generated review artifacts, snapshots, logs, and local path settings outside the distribution folder. Do not resume or interrupt generation queues for comparison work. Preserve the user's task order and publication restrictions.
