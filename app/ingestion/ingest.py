import os
import uuid
import json
import hashlib
from typing import List, Dict, Any
from pathlib import Path

from pypdf import PdfReader
from app.core.vector_store import get_collection, add_docs

# Basic chunking params (you can tune later)
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

# Resolve project root (one level above app/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Ingest from project-root/data by default
INGEST_DATA_DIR = os.getenv(
    "INGEST_DATA_DIR",
    str(PROJECT_ROOT / "data"),
)
INGEST_COLLECTION_NAME = os.getenv("INGEST_COLLECTION_NAME", "pm_docs")

# Where we track what has been ingested
INGEST_INDEX_PATH = Path(str(PROJECT_ROOT / "data" / ".product_atlas_ingested.json"))


# ---------- Ingestion index helpers ----------

def _load_index() -> Dict[str, Any]:
    if not INGEST_INDEX_PATH.exists():
        return {}
    try:
        with open(INGEST_INDEX_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        # If the file is corrupted, start fresh
        return {}


def _save_index(index: Dict[str, Any]) -> None:
    INGEST_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INGEST_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)


def _compute_doc_id(path: str) -> str:
    # Absolute path as stable id
    return str(Path(path).resolve())


def _compute_doc_version(path: str) -> str:
    # Content hash; if file is missing or unreadable, return empty string
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
    except OSError:
        return ""
    return h.hexdigest()


def should_ingest(path: str) -> bool:
    index = _load_index()
    doc_id = _compute_doc_id(path)
    new_version = _compute_doc_version(path)
    if not new_version:
        # If we couldn't compute a version, better to try ingesting (and fail loudly)
        return True

    record = index.get(doc_id)
    if record and record.get("version") == new_version:
        # Already ingested and unchanged
        return False

    # Either new file or changed content
    return True


def mark_ingested(path: str) -> None:
    index = _load_index()
    doc_id = _compute_doc_id(path)
    version = _compute_doc_version(path)
    index[doc_id] = {
        "version": version,
        "path": path,
    }
    _save_index(index)


# ---------- File readers & chunking ----------

def read_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def read_pdf(path: str) -> str:
    reader = PdfReader(path)
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def read_md(path: str) -> str:
    # For now treat markdown as plain text
    return read_txt(path)


def load_file(path: str) -> str:
    lower = path.lower()
    if lower.endswith(".pdf"):
        return read_pdf(path)
    if lower.endswith(".txt") or lower.endswith(".md"):
        return read_txt(path)
    # Unknown extension -> skip
    return ""


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == length:
            break
        start = end - overlap  # step with overlap
    return chunks


# ---------- Main ingestion ----------

def ingest_folder(
    data_dir: str = INGEST_DATA_DIR,
    collection_name: str = INGEST_COLLECTION_NAME,
):
    coll = get_collection(collection_name)

    print(f"Ingesting from {data_dir} into collection '{collection_name}'")

    file_count = 0
    chunk_count = 0

    for root, _, files in os.walk(data_dir):
        for filename in files:
            path = os.path.join(root, filename)

            # Skip if already ingested with same content
            if not should_ingest(path):
                print(f"Skipping (already ingested, unchanged): {path}")
                continue

            content = load_file(path)
            if not content.strip():
                print(f"Skipping empty or unsupported file: {path}")
                continue

            file_count += 1
            chunks = chunk_text(content)
            ids = [str(uuid.uuid4()) for _ in chunks]
            metadatas = [
                {
                    "source": path,
                    "chunk_index": i,
                    "filename": filename,
                }
                for i in range(len(chunks))
            ]

            add_docs(coll, ids, chunks, metadatas)
            mark_ingested(path)

            chunk_count += len(chunks)
            print(f"Ingested {len(chunks)} chunks from {path}")

    print(f"Done. Files ingested: {file_count}, total chunks: {chunk_count}")
    print("Collection count from inside ingest:", coll.count())
    # With persistent Chroma, no explicit persist() call is needed.

if __name__ == "__main__":
    ingest_folder()