import json
from pathlib import Path
from app.core.vector_store import get_collection
from app.ingestion.ingest import (
    INGEST_COLLECTION_NAME,
    INGEST_INDEX_PATH,
    _compute_doc_id,
    _compute_doc_version,
)


def main():
    coll = get_collection(INGEST_COLLECTION_NAME)
    print(f"Loading all metadata from collection '{INGEST_COLLECTION_NAME}'...")

    limit = 1000  # tune if needed
    offset = 0
    index = {}
    total = 0

    while True:
        results = coll.get(
            include=["metadatas"],
            limit=limit,
            offset=offset,
        )

        metadatas_batch = results.get("metadatas", [])
        if not metadatas_batch:
            break

        for md in metadatas_batch:
            source = md.get("source")
            if not source:
                continue

            doc_id = _compute_doc_id(source)
            if doc_id in index:
                continue  # already recorded from another chunk

            version = _compute_doc_version(source)
            index[doc_id] = {
                "version": version,
                "path": source,
            }

        batch_size = len(metadatas_batch)
        total += batch_size
        offset += limit
        print(f"Processed batch of {batch_size}, total metadata rows: {total}")

    INGEST_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INGEST_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    print(f"Wrote {len(index)} unique documents into {INGEST_INDEX_PATH}")


if __name__ == "__main__":
    main()
