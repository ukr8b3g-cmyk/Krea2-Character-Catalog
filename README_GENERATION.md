[日本語 / Japanese](README_GENERATION.ja.md)

# Generate and register catalog images

This distribution includes saved ComfyUI workflows and examples, rather than the original generation queue or resume checkpoints. The character settings below were checked against saved WebP metadata, generation records, and workflows on October 8, 2026.

## Character generation settings

| Setting | Value |
|---|---|
| Model | `krea2_turbo_int8_convrot.safetensors` (workflow model folder: `krea2`) |
| Text encoder | `qwen3vl_4b_fp8_scaled.safetensors`, CLIP type `krea2` |
| VAE | `qwen_image_vae.safetensors` |
| Resolution | **896 × 1184 px (width × height)** |
| Steps / CFG | **8 / 1.0** |
| Sampler / scheduler | **Euler / simple**, using `ForgeNeoBridgeScheduler` |
| Denoise / seed | **1.0 / fixed 42** |
| Batch size | **1** |
| Negative conditioning | `ConditioningZeroOut`; no separate negative text |
| Save node | `SaveWebPMeta` / Save WEBP Meta |
| Format | **Lossy WebP, quality 80**, internal method 0 |
| Metadata | Resolved prompt, model/sampler settings, workflow, and record mapping in EXIF |

Use the [UI workflow](comfyui/workflows/Krea2%20Catalog%20Thumbnails.json) or [API workflow](comfyui/workflows/Krea2%20Catalog%20Thumbnails.api.json). Install the required models and nodes yourself; adjust their registered names and input/output locations. See [ComfyUI setup](comfyui/README.md).

The catalog's initial display width is 170 px. Its thumbnail slider changes display size only and does not rewrite the 896 × 1184 source image.

## File size reference

A historical measurement of 344 Blue Archive images, including subsequently rejected images, used these character settings. Mean file size was 69.6 KiB, median 69.2 KiB, and range 46.2–102.8 KiB. Metadata averaged about 17.4 KiB. These are historical full-file measurements, not a target size for v0.9's sanitized metadata. Image complexity and prompt content affect size; use quality 80 as the starting point.

The optional [WebPThumbnailBatch tool](tools/WebPThumbnailBatch/README.md) creates smaller previews in a separate folder while keeping source images. The catalog currently displays source images; automatic replacement with these smaller files is not integrated.

## Background and pose

The original CSV workflow appended:

```text
standing alone on a plain gray background, looking at the camera
```

It did not append `full body` or set an exact background RGB value. Background shade and composition vary between generated results. UI theme colors do not control image backgrounds.

## Original CSV versus generation input

`original_tags/anima_characters.csv` in the complete Release ZIP uses **`tag,category,count,insert_mode`**. It contains character/copyright identity and appearance tags. The sample `comfyui/inputs/thumbnail_prompts.csv` uses **`id,prompt`**. The CSV helper reads a `prompt`, `tag`, or `text` column and can append a common suffix.

Reusable catalog prompts omit generation-specific background/pose instructions. Original tags preserve source tags. The actual resolved generation text is saved separately in metadata; do not confuse these three forms.

## Saved images and regeneration

WebPs with saved workflows can be dragged into ComfyUI. Some older images lack metadata and cannot restore all original settings. In v0.9 distribution images, `Krea2CatalogPromptFile` stores resolved generation text in `manual_prompt` and a safe output identifier in `manual_id`. A nonempty manual prompt bypasses CSV lookup, removing dependence on the original PC's CSV path.

Install or update the bundled custom node from `comfyui/custom_nodes/ComfyUI-Krea2-Catalog-Tools` into your own ComfyUI `custom_nodes` folder, then restart ComfyUI. Other required nodes and models are separate. For sequential CSV generation, clear `manual_prompt`, set `file_path` to your own CSV, and choose its row index. With a resolved saved prompt, keep the common suffix empty to avoid appending the same instructions twice.

Rejected workflows are provided in a separate ZIP. Its index identifies names and copyrights; 13,486 recipes use saved generation metadata, and 11 old recipes are editable templates. These are starting points, not a promise of accurate regeneration.

## Register the result

Open Add image or `open_editor.cmd`, choose the output image, and click Register. Name, copyright, prompt, tags, and attached JSON are optional. The Editor copies the image without changing its source file. Existing bundled entries come from generation manifests, while additions and edits are stored in separate user files. See [Editor usage](review/README.md).
