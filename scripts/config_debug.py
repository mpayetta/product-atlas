import os

import os
import sys

# Ensure project root is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Now imports from app will work
import app  # noqa: E402
from app.vector_store import PERSIST_DIR_ABS  # noqa: E402

def get_env(name, default=None):
    value = os.getenv(name, default)
    return value, (value is not None)

def main():
    print("=== Product Atlas Configuration ===\n")

    sections = [
        ("LLM / Ollama", [
            "OLLAMA_URL",
            "LLM_MODEL_NAME",
            "LLM_TEMPERATURE",
            "LLM_MAX_TOKENS",
        ]),
        ("Embeddings / Chroma", [
            "EMBEDDING_MODEL_NAME",
            "CHROMA_PERSIST_DIR",
        ]),
        ("RAG", [
            "RAG_TOP_K",
            "RAG_MAX_CONTEXT_CHARS",
        ]),
        ("Ingestion / Chunking", [
            "INGEST_DATA_DIR",
            "INGEST_COLLECTION_NAME",
            "CHUNK_SIZE",
            "CHUNK_OVERLAP",
        ]),
    ]

    for title, keys in sections:
        print(f"[{title}]")
        for key in keys:
            value, present = get_env(key)
            status = "set" if present else "defaulted"
            print(f"  {key} = {value} ({status})")
        print()

    print("[Derived paths]")
    print(f"  Chroma absolute persist dir = {PERSIST_DIR_ABS}")

if __name__ == "__main__":
    main()
