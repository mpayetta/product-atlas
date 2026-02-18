import os
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "data/chroma")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3")

# Absolute path to ensure consistency across processes
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERSIST_DIR_ABS = os.path.join(BASE_DIR, CHROMA_PERSIST_DIR)
os.makedirs(PERSIST_DIR_ABS, exist_ok=True)

print("Chroma persist dir:", PERSIST_DIR_ABS)

# ✅ Use PersistentClient so data survives across runs
client = chromadb.PersistentClient(path=PERSIST_DIR_ABS)

_chroma_embedding_fn = SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL_NAME
)

def get_collection(name="pm_docs"):
    return client.get_collection(name=name, embedding_function=_chroma_embedding_fn) \
        if name in [c.name for c in client.list_collections()] \
        else client.create_collection(name=name, embedding_function=_chroma_embedding_fn)

def add_docs(collection, ids, texts, metadatas=None):
    if metadatas is None:
        metadatas = [{}] * len(texts)
    collection.add(ids=ids, documents=texts, metadatas=metadatas)

def query(collection, query_text, k=5):
    results = collection.query(
        query_texts=[query_text],
        n_results=k,
    )
    return results
