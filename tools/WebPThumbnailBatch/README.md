# WebP Thumbnail Batch

An optional tool for making smaller WebP previews in a separate folder while keeping the original images. It is not automatically integrated into the catalog.

## Graphical interface

Run `Start-WebPThumbnailBatch.ps1`, select an input and a separate output folder, choose width and quality, and start conversion. Python 3.12+, Pillow with WebP support, and Tk are required. This mini-tool does not install dependencies automatically.

## Command line

From this tool folder, replace the relative input and output examples with your chosen folders:

```powershell
python -B ./webp_thumbnail_batch.py --input ./images --output ./thumbnails --width 240 --quality 80 --workers 2 --dry-run
```

Remove `--dry-run` to convert. Results are returned as JSON. Exit codes: 0 success, 1 some images failed, 2 invalid configuration. `--no-recursive` processes only the input folder itself; `--force` rebuilds managed outputs.

Outputs preserve transparency and applicable ICC profiles, apply EXIF orientation, and omit generation EXIF/XMP. Source images remain untouched. Identical input/output folders or unsafe parent output paths are rejected. Only files managed by the tool are eligible for replacement. Output records are stored in `.webp-thumbnail-index.json`, allowing unchanged files to be skipped and preventing simultaneous runs for the same output folder. Change detection uses file size and modification time.

The launcher checks `WEBP_THUMBNAIL_PYTHON`, an available user Miniconda installation, and ordinary Python installations. Set that environment variable to your own compatible interpreter if needed. This mini-tool requires a newer Python than the core catalog.
