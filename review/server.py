"""Local review of generated images, with persistent visibility flags and no file moves."""
import argparse
import csv
import datetime
import io
import json
import os
import re
import secrets
import socketserver
import threading
import time
from catalog_editor import EditorCatalog, decode_bytes, inspect_image
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from runtime_support import CatalogLock, atomic_json, catalog_version, folder_available, read_json


RUN = re.compile(r"(?:run|test)-[0-9]{8}-[0-9]{6}")
ID = re.compile(r"(?:a|cn|ky|jp)[0-9]{5}")
ASSETS = Path(__file__).resolve().parent


class LocalCatalogServer(ThreadingHTTPServer):
    def server_bind(self):
        # A loopback-only catalog needs no reverse DNS; macOS resolvers can stall it.
        socketserver.TCPServer.server_bind(self)
        self.server_name = 'localhost'
        self.server_port = self.server_address[1]


def etag_matches(header, etag):
    return any(value.strip().removeprefix("W/") in {etag, "*"}
               for value in (header or "").split(","))


def tag_facets(record):
    tags = list(dict.fromkeys(part.strip().replace("_", " ").lower() for part in record["copy_tags"].split(",")))
    result = {"character": [record["name"].split(" (", 1)[0]], "copyright": [record["copyright"]],
              "hairColor": [], "hairLength": [], "eyeColor": [], "gender": [], "outfit": []}
    for tag in tags[2:]:
        if re.fullmatch(r"(black|white|blonde|blond|brown|red|blue|purple|pink|green|grey|gray|orange|silver|aqua|multicolored) hair", tag):
            result["hairColor"].append(tag)
        elif tag in {"short hair", "long hair", "very long hair", "medium hair", "bald"}:
            result["hairLength"].append(tag)
        elif re.fullmatch(r"(black|white|brown|red|blue|purple|pink|green|grey|gray|orange|yellow|aqua) eyes", tag) or tag == "heterochromia":
            result["eyeColor"].append(tag)
        elif tag in {"1girl", "female"}:
            result["gender"].append("Female")
        elif tag in {"1boy", "male"}:
            result["gender"].append("Male")
        elif tag in {"robot", "android", "monster", "animal", "no humans"}:
            result["gender"].append("Non-human")
        elif re.search(r"\b(dress|uniform|jacket|armor|suit|coat|shirt|cape|robe|swimsuit|hat|gloves|boots|skirt|kimono|bodysuit|leotard|mask|helmet)\b", tag):
            result["outfit"].append(tag)
    return {key: list(dict.fromkeys(values)) for key, values in result.items()}


def save_human_decisions(store, rows):
    """Persist verdicts only. This never changes catalog visibility."""
    if not isinstance(rows, list) or len(rows) > 200:
        raise ValueError("Expected up to 200 human decisions")
    validated = []
    for row in rows:
        if not isinstance(row, dict) or row.get("decision") not in {"match", "mismatch", "hold"}:
            raise ValueError("Invalid human decision")
        entry = store.lookup(row.get("key", ""))
        if entry.get("kind", "character") != "character" or entry["image_sha256"] != row.get("catalog_image_sha256"):
            raise ValueError("Human decision image no longer matches")
        slug = row.get("reference_slug")
        if not isinstance(slug, str) or not 0 < len(slug) <= 500:
            raise ValueError("Invalid reference identity")
        decided_at = row.get("decided_at", "")
        when = datetime.datetime.fromisoformat(decided_at.replace("Z", "+00:00"))
        if when.tzinfo is None:
            raise ValueError("Decision timestamp needs timezone")
        validated.append({"key": entry["key"], "name": entry["name"], "copyright": entry["copyright"],
                          "decision": row["decision"], "decided_at": when.isoformat(),
                          "catalog_image_sha256": entry["image_sha256"], "reference_slug": slug})
    with store.lock:
        path = store.outputs / "human_decisions.json"
        payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"schema": "krea2-human-paired-review-v1", "decisions": []}
        # One latest verdict per card: no growing event log or image cache.
        saved = {row["key"]: row for row in payload["decisions"]}
        for row in validated:
            old = saved.get(row["key"])
            if old is None or datetime.datetime.fromisoformat(old["decided_at"].replace("Z", "+00:00")) <= datetime.datetime.fromisoformat(row["decided_at"]):
                saved[row["key"]] = row
        payload["decisions"] = list(saved.values())
        payload["saved_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        os.replace(temporary, path)
    return len(validated)


class ReviewStore:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.outputs = self.root / "outputs"
        self.outputs.mkdir(parents=True, exist_ok=True)
        self.outputs = self.outputs.resolve()
        self.state_path = self.outputs / "review_state.json"
        self.state = json.loads(self.state_path.read_text(encoding="utf-8")) if self.state_path.exists() else {"deleted": {}, "undo": []}
        self.state.setdefault("deleted", {})  # Legacy locations, retained without moving the files.
        self.state.setdefault("undo", [])
        self.state.setdefault("hidden", list(self.state["deleted"]))
        self.state.setdefault("favorites", [])
        self.state.setdefault("similarity", {})
        self.lock = threading.RLock()
        # Build catalog metadata independently of image and review-state operations.
        self.refresh_lock = threading.Lock()
        self.cache = {}
        self.index = {}
        self.present = {}
        self.runs = []
        self.styles = []
        self.style_stamp = None
        self.audit_at = 0
        self.catalog_revision = 0
        self.state_revision = 0
        self.view_stamp = None
        self.view = None
        self.revision = 0
        self.restored_keys = set()
        self.next_record_revision = 0
        self.editor = EditorCatalog(self.root)
        self.editor_stamp = None

    def path(self, relative):
        path = (self.outputs / relative).resolve()
        if not path.is_relative_to(self.outputs):
            raise ValueError("Output path escapes the review folder")
        return path

    def save(self):
        temporary = self.state_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(self.state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.state_path)
        self.state_revision += 1

    @staticmethod
    def file_stamp(path):
        stat = path.stat()
        return stat.st_mtime_ns, stat.st_size

    def prepare_record(self, record, run, kind, directory):
        if not ID.fullmatch(record["id"]):
            raise ValueError("Invalid image ID in generation record")
        files, paths = {}, {}
        for field, suffix in (("image", ".webp"), ("copy_prompt_file", ".copy.txt"), ("copy_tags_file", ".tags.txt")):
            path = self.path("staging/" + run + "/" + record[field].replace("\\", "/"))
            if path.name != record["id"] + suffix or not path.is_relative_to(directory):
                raise ValueError("Invalid image bundle path")
            legacy = self.state["deleted"].get(run + "/" + record["id"], {}).get("files", {}).get(field)
            if not path.is_file() and legacy:
                trash = self.path(legacy["trash"])
                if (legacy["source"] != path.relative_to(self.outputs).as_posix()
                        or not trash.is_relative_to(self.outputs / "review_trash")
                        or trash.name != record["id"] + suffix):
                    raise ValueError("Invalid legacy image location")
                path = trash
            files[field] = path.relative_to(self.outputs).as_posix()
            paths[field] = path
        self.next_record_revision += 1
        entry = {**record, "record_revision": self.next_record_revision, "kind": kind, "key": run + "/" + record["id"], "run_id": run,
                 "files": files, "facets": tag_facets(record)}
        return {"raw": record, "entry": entry, "image_path": paths["image"],
                "present": paths["image"].is_file()}

    def refresh(self):
        with self.refresh_lock:
            audit = time.monotonic() >= self.audit_at
            cache, changed = {}, False
            for report_path in sorted((self.outputs / "staging").glob("*/generation_manifest.json")):
                run = report_path.parent.name
                if not RUN.fullmatch(run):
                    continue
                previous = self.cache.get(run)
                try:
                    stamp = self.file_stamp(report_path)
                except OSError:
                    continue
                item = previous
                if previous is None or stamp != previous["stamp"]:
                    report = None
                    for attempt in range(4):
                        try:
                            report = json.loads(report_path.read_text(encoding="utf-8"))
                            break
                        except (json.JSONDecodeError, OSError):
                            time.sleep(0.03)
                    # A writer may temporarily leave partial JSON; keep the last good view
                    # and its old stamp so the next poll retries the new manifest.
                    if report is not None:
                        kind = report.get("kind", "character")
                        old_records = previous["records"] if previous else {}
                        directory = report_path.parent.resolve()
                        records = {}
                        for record in report["records"]:
                            old = old_records.get(record["id"])
                            if old and old["raw"] == record and old["entry"]["kind"] == kind:
                                records[record["id"]] = old
                            else:
                                records[record["id"]] = self.prepare_record(record, run, kind, directory)
                        item = {"stamp": stamp, "records": records,
                                "run": {"id": run, "kind": kind, "status": report.get("status", ""),
                                        "count": len(report["records"])}}
                        changed = True
                if item is not None:
                    if audit or any(not value["present"] for value in item["records"].values()):
                        records = {}
                        for record_id, prepared in item["records"].items():
                            exists = prepared["image_path"].is_file() if audit or not prepared["present"] else True
                            records[record_id] = {**prepared, "present": exists}
                            changed |= exists != prepared["present"]
                        item = {**item, "records": records}
                    cache[run] = item
            changed |= cache.keys() != self.cache.keys()
            style_path = self.root / "original_tags/styles/styles_manifest.json"
            styles, accepted_style_stamp = self.styles, self.style_stamp
            try:
                style_stamp = self.file_stamp(style_path) if style_path.exists() else None
                if style_stamp != self.style_stamp:
                    styles = json.loads(style_path.read_text(encoding="utf-8"))["entries"] if style_stamp else []
                    accepted_style_stamp = style_stamp
                    changed = True
            except (json.JSONDecodeError, OSError):
                pass
            editor_stamp, user_items, user_edits = self.editor.snapshot()
            changed |= editor_stamp != self.editor_stamp
            self.cache = cache
            if audit:
                self.audit_at = time.monotonic() + 30
            if changed:
                index, present, runs = {}, {}, []
                for item in cache.values():
                    runs.append(item["run"])
                    for prepared in item["records"].values():
                        entry = prepared["entry"]
                        index[entry["key"]] = entry
                        present[entry["key"]] = prepared["present"]
                runs.sort(key=lambda item: item["id"].split("-", 1)[1], reverse=True)
                with self.lock:
                    # Restore may finish while metadata is being built. Reconcile
                    # those bundles before publishing the independently built index.
                    for item in cache.values():
                        for prepared in item["records"].values():
                            key = prepared["entry"]["key"]
                            if key in self.restored_keys:
                                prepared["present"] = prepared["image_path"].is_file()
                                present[key] = prepared["present"]
                    self.restored_keys.clear()
                    self.editor.merge(index, present, user_items, user_edits, tag_facets)
                    self.index, self.present, self.runs = index, present, runs
                    self.editor_stamp = editor_stamp
                    self.styles, self.style_stamp = styles, accepted_style_stamp
                    self.catalog_revision += 1

    def listing(self):
        # Caller holds the review-state lock; metadata objects are never mutated.
        stamp = self.catalog_revision, self.state_revision
        if stamp != self.view_stamp:
            favorites = set(self.state["favorites"])
            hidden = set(self.state["hidden"])
            # Keep the old boolean for generation-progress readers; it now means hidden.
            entries = [{**entry, "hidden": key in hidden, "deleted": key in hidden, "favorite": key in favorites, "similarity": self.state["similarity"].get(key, 0)}
                       for key, entry in self.index.items()
                       if self.present.get(key)]
            self.view = {"entries": entries, "runs": self.runs, "style_candidates": self.styles,
                         "undo_count": len(self.state["undo"]), "visibility_mode": "flags", "hidden_export": True}
            self.view_stamp = stamp
            self.revision += 1
        return self.view

    def entries(self):
        listing = self.list()
        return listing["entries"], listing["runs"]

    def list(self):
        self.refresh()
        with self.lock:
            return self.listing()

    def snapshot(self):
        self.refresh()
        with self.lock:
            return self.listing(), self.revision

    def lookup(self, key):
        if key not in self.index:
            self.refresh()
        with self.lock:
            return self.lookup_cached(key)

    def lookup_cached(self, key):
        found = self.index.get(key)
        if found is None or not self.present.get(key):
            raise ValueError("Image record was not found")
        hidden = key in self.state["hidden"]
        return {**found, "hidden": hidden, "deleted": hidden, "favorite": key in self.state["favorites"], "similarity": self.state["similarity"].get(key, 0)}

    def favorite(self, key, enabled):
        self.lookup(key)
        with self.lock:
            if type(enabled) is not bool:
                raise ValueError("Expected a favorite setting")
            self.lookup_cached(key)
            previous = list(self.state["favorites"])
            values = set(previous)
            values.add(key) if enabled else values.discard(key)
            self.state["favorites"] = sorted(values)
            try:
                self.save()
            except Exception:
                self.state["favorites"] = previous
                raise
            return {"key": key, "favorite": enabled}

    def similarity(self, key, rating):
        self.lookup(key)
        with self.lock:
            if type(rating) is not int or not 0 <= rating <= 3:
                raise ValueError("Expected a similarity rating from 0 to 3")
            self.lookup_cached(key)
            previous = dict(self.state["similarity"])
            if rating:
                self.state["similarity"][key] = rating
            else:
                self.state["similarity"].pop(key, None)
            try:
                self.save()
            except Exception:
                self.state["similarity"] = previous
                raise
            return {"key": key, "similarity": rating}

    def image(self, key, if_none_match=None, version=None):
        self.lookup(key)
        with self.lock:
            entry = self.lookup_cached(key)
            digest = entry["image_sha256"]
            if version is not None and version != digest:
                raise ValueError("Image version no longer matches the record")
            if etag_matches(if_none_match, '"' + digest + '"'):
                return None, digest
            return self.path(entry["files"]["image"]).read_bytes(), entry["image_sha256"]

    def hide(self, keys):
        keys = list(dict.fromkeys(keys))
        for key in keys:
            self.lookup(key)
        with self.lock:
            if not keys:
                raise ValueError("Select an image first")
            records = [self.lookup_cached(key) for key in keys]
            if any(entry["hidden"] for entry in records):
                raise ValueError("An image is already hidden")
            previous = json.loads(json.dumps(self.state))
            self.state["hidden"] = sorted(set(self.state["hidden"]) | set(keys))
            self.state["undo"].append(keys)
            try:
                self.save()
            except Exception:
                self.state = previous
                raise
            return len(keys)

    def restore(self, keys):
        with self.lock:
            keys = list(dict.fromkeys(keys))
            if not keys or any(key not in self.state["hidden"] for key in keys):
                raise ValueError("Hidden image was not found")
            previous = json.loads(json.dumps(self.state))
            self.state["hidden"] = [key for key in self.state["hidden"] if key not in keys]
            self.state["undo"] = [remaining for batch in self.state["undo"]
                                  if (remaining := [key for key in batch if key not in keys])]
            try:
                self.save()
            except Exception:
                self.state = previous
                raise
            return len(keys)

    def undo(self):
        with self.lock:
            if not self.state["undo"]:
                raise ValueError("Nothing to undo")
            return self.restore(self.state["undo"][-1])

    def export(self, kind=None):
        self.refresh()
        with self.lock:
            if kind not in {None, "character", "style"}:
                raise ValueError("Unknown catalog tab")
            entries = self.listing()["entries"]
            entries = [entry for entry in entries if not entry["hidden"] and (kind is None or entry["kind"] == kind)]
            fields = ["run_id", "id", "name", "copyright", "image", "copy_prompt_file", "copy_tags_file", "copy_prompt", "copy_tags", "favorite"]
            if kind == "style":
                fields += ["source_style_id", "category", "name_jp"]
            path = self.outputs / ("review_styles_selection.csv" if kind == "style" else "review_selection.csv")
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                for entry in entries:
                    row = {field: entry.get(field, "") for field in fields}
                    row.update(entry["files"])
                    writer.writerow(row)
            return {"count": len(entries), "file": str(path)}


    def export_hidden(self, kind="character"):
        self.refresh()
        with self.lock:
            if kind not in {"character", "style"}:
                raise ValueError("Unknown catalog tab")
            entries = sorted((entry for entry in self.listing()["entries"]
                              if entry["hidden"] and entry["kind"] == kind),
                             key=lambda entry: (entry["copyright"], entry["name"], entry["key"]))
            lines = ["非表示にした画像の一覧", "対象: " + ("スタイル" if kind == "style" else "キャラクター"),
                     f"件数: {len(entries)}", "範囲: このタブ全体（検索条件・表示ページに関係なく出力）",
                     "画像ファイルは移動・削除していません。", ""]
            for number, entry in enumerate(entries, 1):
                lines.extend([f"[{number}]", "名前: " + entry["name"], "作品名: " + entry["copyright"],
                              "ID: " + entry["id"], "生成回: " + entry["run_id"],
                              "画像: " + str(self.path(entry["files"]["image"])), ""])
            path = self.outputs / ("review_hidden_styles.txt" if kind == "style" else "review_hidden_images.txt")
            temporary = path.with_suffix(".txt.tmp")
            temporary.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
            temporary.replace(path)
            return {"count": len(entries), "file": str(path)}


def make_server(root, port=8767):
    print('Loading catalog records...',flush=True)
    store = ReviewStore(root)
    token = secrets.token_urlsafe(24)
    instance = secrets.token_hex(8)
    response_lock = threading.Lock()
    response_cache = {"revision": None, "content": None}

    def sync_version():
        return {"instance": instance, "catalog": store.catalog_revision, "state": store.state_revision}

    def version_etag(value):
        return f'"{value["instance"]}-{value["catalog"]}-{value["state"]}"'

    def operation_delta(route, data):
        # Resolve bundles outside the state lock; catalog parsing must not hold it.
        if route != "undo":
            keys = [data["key"]] if route in {"favorite", "similarity"} else list(dict.fromkeys(data["keys"]))
            for key in keys:
                store.lookup(key)
        with store.lock:
            before = sync_version()
            if route == "undo":
                keys = list(store.state["undo"][-1]) if store.state["undo"] else []
                result = {"count": store.undo()}
            elif route == "similarity":
                result = store.similarity(data["key"], data["rating"])
            elif route == "favorite":
                result = store.favorite(data["key"], data["enabled"])
            else:
                count = store.restore(keys) if route == "restore" else store.hide(keys)
                result = {"count": count}
            changes = []
            hidden, favorites = set(store.state["hidden"]), set(store.state["favorites"])
            for key in keys:
                changes.append({"key": key, "hidden": key in hidden, "deleted": key in hidden,
                                "favorite": key in favorites, "similarity": store.state["similarity"].get(key, 0)})
            current = sync_version()
            return {**result, "before": before, "version": current, "changes": changes,
                    "undo_count": len(store.state["undo"]), "etag": version_etag(current)}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, content, content_type, code=200, headers=None):
            try:
                self.send_response(code)
                self.send_header("Content-Type", content_type)
                if code != 304:
                    self.send_header("Content-Length", str(len(content)))
                self.send_header("X-Content-Type-Options", "nosniff")
                for key, value in {"Cache-Control": "no-store", **(headers or {})}.items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(content)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                return

        def json(self, value, code=200):
            self.send(json.dumps(value, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", code)

        def host_ok(self):
            return self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"

        def do_GET(self):
            if not self.host_ok():
                self.json({"error": "Invalid host"}, 403)
                return
            url = urlsplit(self.path)
            try:
                if url.path == "/api/info":
                    self.json({"app": "Krea2CatalogReview", "root": str(store.root), "pid": os.getpid(), "visibility_mode": "flags", "hidden_export": True, "editor_version": 1, "catalog_version": catalog_version(store.root), "folder_available": folder_available()})
                elif url.path == "/api/editor/bootstrap":
                    sources = [name for name, relative in [("characters", "original_tags/anima_characters.csv"), ("styles", "original_tags/styles/selected_all_styles.csv"), ("sample", "comfyui/inputs/thumbnail_prompts.csv")] if (store.root / relative).is_file()]
                    self.json({"token": token, "sources": sources, "editor_version": 1, "folder_available": folder_available()})
                elif url.path == "/api/editor/record":
                    key = parse_qs(url.query).get("key", [""])[0]
                    store.refresh()
                    record = store.lookup(key)
                    workflow = store.editor.workflow(record)
                    self.json({"record": record, "workflow_available": workflow is not None})
                elif url.path == "/api/editor/operation":
                    value = parse_qs(url.query).get("id", [""])[0]
                    self.json(store.editor.operation(value))
                elif url.path == "/api/editor/csv":
                    query = parse_qs(url.query)
                    self.json(store.editor.builtin_csv(query.get("source", ["characters"])[0], query.get("query", [""])[0]))
                elif url.path == "/api/editor/workflow":
                    key = parse_qs(url.query).get("key", [""])[0]
                    store.refresh(); record = store.lookup(key)
                    workflow = store.editor.workflow(record)
                    if workflow is None:
                        raise ValueError("この画像には保存JSONがありません。")
                    content = json.dumps(workflow, ensure_ascii=False, indent=2).encode("utf-8")
                    filename = "workflow-" + record["id"] + ".json"
                    self.send(content, "application/json; charset=utf-8", headers={"Content-Disposition": 'attachment; filename="' + filename + '"'})
                elif url.path == "/api/human-decisions":
                    headers = {"Access-Control-Allow-Origin": "null", "Vary": "Origin"}
                    capability = json.loads((store.outputs / "human_review_capability.json").read_text(encoding="utf-8"))["token"]
                    if self.headers.get("Origin") != "null" or not secrets.compare_digest(self.headers.get("X-Human-Review-Token", ""), capability):
                        self.send(b'{"error":"Unauthorized human review"}', "application/json", 403, headers)
                        return
                    with store.lock:
                        path = store.outputs / "human_decisions.json"
                        content = path.read_bytes() if path.exists() else b'{"schema":"krea2-human-paired-review-v1","decisions":[]}'
                    self.send(content, "application/json; charset=utf-8", 200, headers)
                elif url.path == "/api/paired-catalog":
                    # Read-only metadata for the local file-based paired review.
                    # Never expose the mutation token or filesystem paths here.
                    store.refresh()
                    with store.lock:
                        etag = version_etag(sync_version())
                        headers = {"ETag": etag, "Cache-Control": "private, no-cache"}
                        if self.headers.get("Origin") == "null":
                            headers["Access-Control-Allow-Origin"] = "null"
                            headers["Vary"] = "Origin"
                        if etag_matches(self.headers.get("If-None-Match"), etag):
                            content, code = b"", 304
                        else:
                            rows = [{"key": e["key"], "id": e["id"],
                                     "identity": ", ".join(e.get("copy_tags", "").split(",")[:2]).strip(),
                                     "image_sha256": e["image_sha256"], "hidden": e["hidden"],
                                     "present": e.get("present", True)}
                                    for e in store.listing()["entries"] if e.get("kind", "character") == "character"]
                            content, code = json.dumps({"entries": rows}, ensure_ascii=False).encode("utf-8"), 200
                    self.send(content, "application/json; charset=utf-8", code, headers)
                elif url.path == "/api/list":
                    store.refresh()
                    with store.lock:
                        current = sync_version()
                        etag = version_etag(current)
                        headers = {"ETag": etag, "Cache-Control": "private, no-cache"}
                        if etag_matches(self.headers.get("If-None-Match"), etag):
                            content, code = b"", 304
                        else:
                            stamp = tuple(current.values())
                            with response_lock:
                                if response_cache["revision"] != stamp:
                                    listing = store.listing()
                                    response_cache["content"] = json.dumps({**listing, "token": token, "version": current,
                                                                          "optimizer_version": 1, "folder_available": folder_available()}, ensure_ascii=False).encode("utf-8")
                                    response_cache["revision"] = stamp
                                content = response_cache["content"]
                            code = 200
                    self.send(content, "application/json; charset=utf-8", code, headers)
                elif url.path == "/image":
                    query = parse_qs(url.query)
                    version = query.get("v", [None])[0]
                    data, digest = store.image(query.get("key", [""])[0], self.headers.get("If-None-Match"), version)
                    headers = {"ETag": '"' + digest + '"',
                               "Cache-Control": "private, max-age=3600, must-revalidate" if version else "private, no-cache"}
                    mime = store.lookup(query.get("key", [""])[0]).get("image_mime", "image/webp")
                    self.send(data or b"", mime, 304 if data is None else 200, headers)
                elif url.path == "/api/hidden.txt":
                    kind = parse_qs(url.query).get("kind", ["character"])[0]
                    if kind not in {"character", "style"}:
                        raise ValueError("Unknown catalog tab")
                    name = "review_hidden_styles.txt" if kind == "style" else "review_hidden_images.txt"
                    self.send((store.outputs / name).read_bytes(), "text/plain; charset=utf-8",
                              headers={"Content-Disposition": f'attachment; filename="{name}"'})
                elif url.path == "/api/selection.csv":
                    kind = parse_qs(url.query).get("kind", ["character"])[0]
                    if kind not in {"character", "style"}:
                        raise ValueError("Unknown catalog tab")
                    name = "review_styles_selection.csv" if kind == "style" else "review_selection.csv"
                    self.send((store.outputs / name).read_bytes(), "text/csv; charset=utf-8")
                else:
                    assets = {"/": ("index.html", "text/html; charset=utf-8"),
                              "/review.js": ("review.js", "text/javascript; charset=utf-8"),
                              "/review.css": ("review.css", "text/css; charset=utf-8"),
                              "/editor": ("editor.html", "text/html; charset=utf-8"),
                              "/editor.js": ("editor.js", "text/javascript; charset=utf-8"),
                              "/editor.css": ("editor.css", "text/css; charset=utf-8")}
                    if url.path not in assets:
                        self.json({"error": "Not found"}, 404)
                        return
                    name, content_type = assets[url.path]
                    self.send((ASSETS / name).read_bytes(), content_type)
            except (ValueError, OSError) as error:
                self.json({"error": str(error)}, 400)

        def do_OPTIONS(self):
            if self.host_ok() and urlsplit(self.path).path == "/api/human-decisions" and self.headers.get("Origin") == "null":
                self.send(b"", "text/plain", 204, {"Access-Control-Allow-Origin": "null",
                    "Access-Control-Allow-Methods": "GET, POST", "Access-Control-Allow-Headers": "Content-Type, X-Human-Review-Token", "Vary": "Origin"})
            else:
                self.json({"error": "Invalid origin"}, 403)

        def receive_human_decisions(self):
            headers = {"Access-Control-Allow-Origin": "null", "Vary": "Origin"}
            try:
                capability_path = store.outputs / "human_review_capability.json"
                capability = json.loads(capability_path.read_text(encoding="utf-8"))["token"]
                if not self.host_ok() or self.headers.get("Origin") != "null" or not secrets.compare_digest(self.headers.get("X-Human-Review-Token", ""), capability):
                    self.send(b'{"error":"Unauthorized human review"}', "application/json", 403, headers)
                    return
                length = int(self.headers.get("Content-Length", "0"))
                if self.headers.get("Content-Type", "").split(";")[0] != "application/json" or not 0 < length <= 250000:
                    raise ValueError("Invalid decision request")
                payload = json.loads(self.rfile.read(length))
                if payload.get("schema") != "krea2-human-paired-review-v1":
                    raise ValueError("Invalid decision schema")
                count = save_human_decisions(store, payload.get("decisions"))
                self.send(json.dumps({"saved": count}).encode(), "application/json", 200, headers)
            except (ValueError, OSError, KeyError, TypeError) as error:
                self.send(json.dumps({"error": str(error)}).encode(), "application/json", 400, headers)

        def do_POST(self):
            if urlsplit(self.path).path == "/api/human-decisions":
                self.receive_human_decisions()
                return
            origin = f"http://127.0.0.1:{self.server.server_port}"
            if not self.host_ok() or self.headers.get("Origin", origin) != origin or self.headers.get("X-Review-Token") != token:
                self.json({"error": "This action must come from the review screen"}, 403)
                return
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                self.json({"error": "Expected JSON"}, 400)
                return
            length = int(self.headers.get("Content-Length", "0"))
            request_limit = 100 * 1024 * 1024 if urlsplit(self.path).path.startswith("/api/editor/") else 1000000
            if not 0 < length <= request_limit:
                self.json({"error": "Invalid request size"}, 400)
                return
            try:
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("Expected a JSON object")
                action = urlsplit(self.path).path
                if action == "/api/editor/inspect":
                    self.json(inspect_image(decode_bytes(data.get("image_base64"))))
                elif action == "/api/editor/csv":
                    raw = decode_bytes(data.get("csv_base64"), 16 * 1024 * 1024)
                    self.json(store.editor.csv_rows(raw, data.get("query", ""), data.get("mapping")))
                elif action == "/api/editor/add":
                    listing = store.list()
                    result = store.editor.add(data, listing["entries"])
                    store.refresh()
                    self.json(result, 409 if result.get("status") == "duplicate" else 200)
                elif action == "/api/editor/edit":
                    store.refresh(); record = store.lookup(data.get("key", ""))
                    result = store.editor.edit(data, record)
                    store.refresh(); self.json(result)
                elif action == "/api/editor/reveal":
                    store.refresh(); record = store.lookup(data.get("key", ""))
                    if record["image_sha256"] != data.get("image_sha256"):
                        raise ValueError("画像が変更されています。開き直してください。")
                    self.json(store.editor.reveal(record))
                elif action in {"/api/hide", "/api/delete", "/api/restore"}:
                    keys = data["keys"]
                    if not isinstance(keys, list) or any(not isinstance(key, str) for key in keys):
                        raise ValueError("Expected selected image IDs")
                    self.json(operation_delta("restore" if action == "/api/restore" else "hide", data))
                elif action == "/api/undo":
                    self.json(operation_delta("undo", data))
                elif action == "/api/similarity":
                    self.json(operation_delta("similarity", data))
                elif action == "/api/favorite":
                    self.json(operation_delta("favorite", data))
                elif action == "/api/export-hidden":
                    self.json(store.export_hidden(data.get("kind", "character")))
                elif action == "/api/export":
                    self.json(store.export(data.get("kind")))
                elif action == "/api/shutdown":
                    self.json({"status": "stopped"})
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                else:
                    self.json({"error": "Not found"}, 404)
            except PermissionError:
                self.json({"error": "[WRITE_PERMISSION] Could not save. Existing data is preserved. Move the catalog to a writable folder, or close applications locking the saved file, then try again."}, 400)
            except (ValueError, OSError, KeyError, TypeError) as error:
                self.json({"error": str(error)}, 400)

    print('Binding local HTTP socket...',flush=True)
    server = LocalCatalogServer(("127.0.0.1", port), Handler)
    server.store = store
    server.token = token
    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Review generated images locally with reversible hiding and no file moves.")
    parser.add_argument("--root", type=Path, default=ASSETS.parent)
    parser.add_argument("--port", type=int, default=8790)
    parser.add_argument("--fallback-port", action="store_true")
    args = parser.parse_args()
    args.root = args.root.resolve()
    with CatalogLock(args.root / 'outputs/review_server.lock', timeout=0):
        try:
            server = make_server(args.root, args.port)
        except OSError as error:
            import errno
            occupied = error.errno in (errno.EADDRINUSE, 10048) or (os.name == 'nt' and getattr(error, 'winerror', None) == 10013)
            if not args.fallback_port or not args.port or not occupied:
                raise
            server = make_server(args.root, 0)
        service_path = args.root / "outputs/review_service.json"
        atomic_json(service_path, {"pid":os.getpid(), "url":f"http://127.0.0.1:{server.server_port}/",
                    "root":str(args.root), "python":__import__('sys').executable,
                    "version":catalog_version(args.root), "method":"Portable Python launcher"})
        print(f"Review screen: http://127.0.0.1:{server.server_port}/", flush=True)
        try:
            server.serve_forever()
        finally:
            server.server_close()
            if read_json(service_path).get('pid') == os.getpid():
                service_path.unlink(missing_ok=True)
