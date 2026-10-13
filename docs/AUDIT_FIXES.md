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

## 日本語

4件の修正と回帰試験はmain向けです。公開済みv0.9.1のZIP・タグ・チェックサム・ライブデモは上書きしません。修正版の配布は別のRelease作業になります。

比較スキルは現在の表示状態から必要な変更だけを反映します。途中失敗後はチェックポイントを確認し、dry-runから再実行します。Editorは手入力を保持しつつ画像由来の自動入力を更新し、PNGの取得文とJSON除外を修正します。元画像は再圧縮・変更しません。

AnimaDexの実DB・個人画像は試験へ持ち込みません。架空DB・画像による契約試験と、実インストールや別OSへの移行の検証は区別します。
