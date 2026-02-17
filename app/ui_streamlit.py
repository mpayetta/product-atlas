import os
import sys

# Ensure project root is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import app  # triggers env load
from app.rag import rag_answer

APP_TITLE = os.getenv("APP_TITLE", "Product Atlas (Local PM Copilot)")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))

st.set_page_config(page_title=APP_TITLE, layout="wide")

st.title(APP_TITLE)
st.write("Ask questions grounded in your local docs (PRDs, transcripts, notes).")

st.sidebar.header("Settings")
st.sidebar.write(f"Top-k documents: {RAG_TOP_K}")
st.sidebar.write(f"Collection: {os.getenv('INGEST_COLLECTION_NAME', 'pm_docs')}")
st.sidebar.write(f"Data dir: {os.getenv('INGEST_DATA_DIR', 'data/raw')}")

question = st.text_area(
    "Your question about your product / docs:",
    height=120,
    placeholder='e.g. "Summarize the main user problems mentioned in my discovery interviews."',
)

top_k = st.sidebar.slider("Top-k (RAG)", min_value=3, max_value=20, value=RAG_TOP_K, step=1)

if st.button("Ask", type="primary") and question.strip():
    with st.spinner("Thinking..."):
        answer = rag_answer(question, k=top_k)

    st.subheader("Answer")
    st.write(answer)