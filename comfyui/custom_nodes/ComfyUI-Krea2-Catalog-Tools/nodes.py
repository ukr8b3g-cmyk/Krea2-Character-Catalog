import csv
import hashlib
import io
import json
import re
from pathlib import Path


COMMON_SUFFIX = "standing alone on a plain gray background, looking at the camera"
DEFAULT_FILE = ""
RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL"} | {
    f"{prefix}{number}" for prefix in ("COM", "LPT") for number in range(1, 10)
}


def read_records(file_path):
    path = Path(file_path.strip())
    source = path.read_bytes()
    text = source.decode("utf-8-sig")
    extension = path.suffix.lower()
    if extension == ".csv":
        reader = csv.DictReader(io.StringIO(text, newline=""))
        columns = reader.fieldnames or []
        prompt_column = next((name for name in ("prompt", "tag", "text") if name in columns), None)
        if prompt_column is None:
            raise ValueError("CSV needs a prompt, tag, or text column.")
        rows = []
        for row in reader:
            if None in row:
                raise ValueError("CSV has extra fields. Put prompts containing commas inside quotes.")
            if any(row.values()):
                rows.append((row.get("id", ""), row.get(prompt_column, "")))
    elif extension == ".json":
        data = json.loads(text)
        records = data["krea"] if isinstance(data, dict) else data
        rows = [(row.get("id", ""), row.get("prompt") or row.get("basic", "")) for row in records]
    elif extension == ".txt":
        rows = []
        for line in text.splitlines():
            if line.strip():
                rows.append(tuple(line.split("\t", 1)) if "\t" in line else ("", line))
    else:
        raise ValueError("Choose a UTF-8 .txt, .csv, or .json file.")

    result = []
    ids = set()
    for number, (record_id, prompt) in enumerate(rows, 1):
        record_id = (record_id or f"line_{number:06d}").strip()
        prompt = (prompt or "").strip()
        if not prompt:
            raise ValueError(f"Record {number} has no prompt.")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", record_id) or record_id.upper() in RESERVED_NAMES:
            raise ValueError(f"Record {number} has an unsafe filename ID: {record_id!r}")
        if record_id in ids:
            raise ValueError(f"Duplicate record ID: {record_id}")
        ids.add(record_id)
        result.append((record_id, prompt))
    if not result:
        raise ValueError("The file contains no prompts.")
    return result, hashlib.sha256(source).hexdigest()


def make_prefix(output_folder, record_id):
    folder = output_folder.strip().replace("\\", "/")
    if folder:
        parts = folder.split("/")
        if any(part in {"", ".", ".."} or part.rstrip(" .") != part
               or not re.fullmatch(r"[A-Za-z0-9 _.-]+", part)
               or part.split(".")[0].upper() in RESERVED_NAMES for part in parts):
            raise ValueError("Output folder must be a relative folder inside ComfyUI/output.")
        return f"{folder}/{record_id}"
    return record_id


class Krea2CatalogPromptFile:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING", {"default": DEFAULT_FILE, "tooltip": "UTF-8 TXT, CSV, or catalog JSON"}),
                "index": ("INT", {"default": 0, "min": 0, "max": 1000000, "control_after_generate": True,
                                  "tooltip": "0 = first record. Use increment to advance for each queued image."}),
                "common_suffix": ("STRING", {"default": COMMON_SUFFIX, "multiline": True}),
                "output_folder": ("STRING", {"default": "krea2_catalog"}),
            },
            "optional": {"manual_prompt": ("STRING", {"default": "", "multiline": True}), "manual_id": ("STRING", {"default": "manual"})},
            "hidden": {"extra_pnginfo": "EXTRA_PNGINFO", "unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT")
    RETURN_NAMES = ("prompt", "filename_prefix", "record_id", "total")
    FUNCTION = "load_record"
    CATEGORY = "Krea2/Catalog"
    DESCRIPTION = "Read one record, append a shared prompt, and keep its ID for WebP filenames and metadata."

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Each execution must attach the selected prompt to that image's metadata.
        return float("nan")

    def load_record(self, file_path, index, common_suffix=COMMON_SUFFIX, output_folder="krea2_catalog",
                    extra_pnginfo=None, unique_id=None, manual_prompt="", manual_id="manual"):
        if manual_prompt.strip():
            record_id, text = (manual_id.strip() or "manual"), manual_prompt.strip()
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", record_id) or record_id.upper() in RESERVED_NAMES:
                raise ValueError("Manual record ID must be a safe filename.")
            records=[(record_id,text)];index=0;source_hash=hashlib.sha256(text.encode("utf-8")).hexdigest()
        else:
            records, source_hash = read_records(file_path)
            if index < 0 or index >= len(records):
                raise ValueError(f"Index {index} is outside this file. Valid range: 0–{len(records) - 1}.")
            record_id, text = records[index]
        suffix = common_suffix.strip()
        prompt = f"{text}, {suffix}" if suffix else text
        prefix = make_prefix(output_folder, record_id)
        if isinstance(extra_pnginfo, dict) and unique_id is not None:
            snapshots = extra_pnginfo.setdefault("krea2_catalog_prompts", {})
            snapshots[str(unique_id)] = {
                "record_id": record_id, "index": index, "total": len(records), "prompt": prompt,
                "filename_prefix": prefix, "file_path": "" if manual_prompt.strip() else str(Path(file_path.strip()).resolve()),
                "source_sha256": source_hash,
            }
        return {
            "ui": {"text": [f"{index + 1} / {len(records)}\n{record_id}\n{prompt}"]},
            "result": (prompt, prefix, record_id, len(records)),
        }
