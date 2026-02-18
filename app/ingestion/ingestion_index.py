# ingestion_index.py
import json
from pathlib import Path
import os
import hashlib
from typing import Dict, Any

INDEX_PATH = Path(".product_atlas_ingested.json")


def _load_index() -> Dict[str, Any]:
    if not INDEX_PATH.exists():
        return {}
    with open(INDEX_PATH, "r") as f:
        return json.load(f)


def _save_index(index: Dict[str, Any]) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_PATH, "w") as f:
        json.dump(index, f, indent=2)


def compute_doc_id(path: Path) -> str:
    # Stable id: absolute path string
    return str(path.resolve())


def compute_doc_version(path: Path) -> str:
    # Simple version: content hash; you can use mtime instead
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def should_ingest(path: Path) -> bool:
    index = _load_index()
    doc_id = compute_doc_id(path)
    new_version = compute_doc_version(path)
    record = index.get(doc_id)

    if record and record.get("version") == new_version:
        # Already ingested and unchanged
        return False

    # Either new file or changed content
    return True


def mark_ingested(path: Path) -> None:
    index = _load_index()
    doc_id = compute_doc_id(path)
    version = compute_doc_version(path)
    index[doc_id] = {
        "version": version,
        "path": str(path),
    }
    _save_index(index)
