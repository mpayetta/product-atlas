import os
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3")

_embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

def embed_texts(texts):
    return _embedding_model.encode(texts, show_progress_bar=False).tolist()

def embed_text(text):
    return embed_texts([text])[0]
