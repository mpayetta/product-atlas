import os
import uuid
from typing import List

from pypdf import PdfReader
from app.vector_store import get_collection, add_docs

# Basic chunking params (you can tune later)
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
INGEST_DATA_DIR = os.getenv("INGEST_DATA_DIR", "data/raw")
INGEST_COLLECTION_NAME = os.getenv("INGEST_COLLECTION_NAME", "pm_docs")

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
            chunk_count += len(chunks)
            print(f"Ingested {len(chunks)} chunks from {path}")

    print(f"Done. Files ingested: {file_count}, total chunks: {chunk_count}")
    print("Collection count from inside ingest:", coll.count())



    # With persistent Chroma, no explicit persist() call is needed.
