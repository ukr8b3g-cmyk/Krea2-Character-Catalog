# Audit fixes on main — October 13, 2026

These changes are in the development branch. They do not replace the existing v0.9.1 Release ZIP, its tag/checksums, or the deployed Pages demo. Downloaded v0.9.1 assets retain the audited implementation until a separate release is published.

| Issue | Change |
|---|---|
| AnimaDex verdict application fails for already visible matches/already hidden mismatches | Plan only necessary visibility operations; still record confirmed unchanged judgments. Revalidate image identities during apply, record partial progress, and recompute live state on retry. |
| Previous image's automatic fields remain after replacement | Refresh untouched fields from the current image, including clearing unavailable metadata. Keep manual values and intentional blank fields. |
| PNG imports negative/unrelated text or ignores resolved catalog metadata | Read PNG/EXIF catalog snapshots and trace save/sampler/positive connections for supported nodes. Ambiguous/unsupported text stays unset; reusable and generation text remain separate. |
| Explicit Remove JSON is undone by embedded workflow fallback | Persist auto/explicit/removed workflow selection. Removed stays unavailable; original image bytes and legacy records remain intact. |
| Skill/node-only changes do not start CI | Include `skills/**` and `comfyui/**` in workflow paths. |
| VERSION.json differs from VERSION | Correct source metadata and fail packaging when version or tag disagrees. |

Regression tests use temporary SQLite databases and fictitious images, never a user's DB or collection. `tests/check_audit_contracts.py` runs against code from the complete candidate ZIP on each OS. It covers the four visibility/verdict combinations, dry run, repeat apply, interrupted apply/retry, ignored choices, changed-image rejection, workflow selection, and headless Chromium image replacement/registration/reopening.

The test report distinguishes synthetic AnimaDex contracts from a real AnimaDex installation. Actual installation compatibility, comparison-page desktop use, cross-OS migration of prepared absolute paths, physical desktop behavior, and GPU generation remain outside this added coverage. Regenerate private comparison files when changing environments.

[Main workflow runs and downloadable reports](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/actions/workflows/release.yml)

## Prompt-parser follow-up

An independent audit identified two additional conditions in the initial fix. `ConditioningConcat` now follows Core's `conditioning_to`/`conditioning_from` inputs, while `ConditioningCombine` keeps `conditioning_1`/`conditioning_2`. Identical text resolves; differing text remains unset instead of being guessed or merged.

Optional node metadata is type-checked before use. A valid image with a save node whose `inputs` is null, a list, or another non-dictionary value can still be inspected and registered with prompt text unset. Invalid node type values are treated as unsupported metadata. No broad exception handler suppresses real image corruption or I/O failures. Regression tests include real PNG metadata and actual HTTP inspection/registration, preserving original bytes.

## Catalog consistency follow-up — October 14, 2026

CSV export limits image-file fields to the declared columns and replaces the existing CSV only after a complete temporary write. Workflow attachments no longer introduce unknown CSV columns. Failure leaves the previous CSV intact.

Hidden cards can be selected and restored together using ordinary page controls. Hide and restore act on the selected visible/hidden subsets respectively. Appearance facets inspect tags independently of their position, excluding exact name/copyright identities; text search includes original tags. Static demo records retain the `user_edited` marker so original artist metadata cannot overwrite manual style corrections.

Regression tests cover workflow-bearing exports and failed replacement, unprefixed appearance tags, browser bulk restore and tag search, and matching edited style names/tags in real local and generated static pages. These changes do not redeploy the public demo or replace Release assets.

## 日本語

4件の修正と回帰試験はmain向けです。公開済みv0.9.1のZIP・タグ・チェックサム・ライブデモは上書きしません。修正版の配布は別のRelease作業になります。

比較スキルは現在の表示状態から必要な変更だけを反映します。途中失敗後はチェックポイントを確認し、dry-runから再実行します。Editorは手入力を保持しつつ画像由来の自動入力を更新し、PNGの取得文とJSON除外を修正します。元画像は再圧縮・変更しません。

AnimaDexの実DB・個人画像は試験へ持ち込みません。架空DB・画像による契約試験と、実インストールや別OSへの移行の検証は区別します。
