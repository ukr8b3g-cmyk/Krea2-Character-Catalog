[日本語 / Japanese](README.ja.md)

# ComfyUI workflows and inputs

Drag a UI workflow from `workflows/` into ComfyUI. Files ending in `.api.json` are API graphs. Adjust model names, CSV input paths, and output locations for your own environment.

## Required nodes and models

The examples use Krea2, its text encoder and VAE, `ForgeNeoBridgeScheduler`, and `SaveWebPMeta`. The bundled `custom_nodes/ComfyUI-Krea2-Catalog-Tools` reads CSV inputs and preserves catalog prompt information. Copy or update it in your ComfyUI `custom_nodes` directory and restart ComfyUI. Models and other custom nodes are not installed by this helper.

See [Generation settings](../README_GENERATION.md) and [sample input CSV](inputs/thumbnail_prompts.csv). The original character-tag CSV has a different schema and is included as `original_tags/anima_characters.csv` in the complete [Release ZIP](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/releases/latest).

This package does not include the former generation queue/resume tools. Loading JSON does not start a render; the user executes it in ComfyUI. WebPs containing saved workflows can also restore the graph. Rejected recipes are in a separate Release ZIP, with an index of names and copyrights.

## Manual prompts and portable saved workflows

`Krea2CatalogPromptFile` accepts `manual_prompt` and `manual_id`. A nonempty manual prompt uses that text without locating a CSV. Distribution WebPs use the saved, resolved generation text through this option. For CSV generation, leave `manual_prompt` empty and set your CSV path and row index. Adjust the required models and other nodes for your environment.
