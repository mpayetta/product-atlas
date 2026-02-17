import os
import sys

# Ensure project root is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import app  # loads env
from app.rag import conversational_rag_answer

APP_TITLE = os.getenv("APP_TITLE", "Product Atlas (Local PM Copilot)")
DEFAULT_TOP_K = int(os.getenv("RAG_TOP_K", "5"))

st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
st.write("Chat with your product docs (PRDs, strategy, transcripts, notes).")

# Sidebar
st.sidebar.header("Chat settings")
top_k = st.sidebar.slider(
    "Top-k documents per question",
    min_value=3,
    max_value=20,
    value=DEFAULT_TOP_K,
    step=1,
)
st.sidebar.write(f"Collection: {os.getenv('INGEST_COLLECTION_NAME', 'pm_docs')}")
st.sidebar.write(f"Data dir: {os.getenv('INGEST_DATA_DIR', 'data/raw')}")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of {"role": "user"|"assistant", "content": str}

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Ask a question about your product or docs...")
if user_input:
    # Add user message to history and display
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Call conversational RAG with history so far (excluding the new assistant to come)
    history_for_llm = st.session_state.messages.copy()

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer = conversational_rag_answer(
                user_message=user_input,
                history=history_for_llm,
                k=top_k,
            )
            st.markdown(answer)

    # Save assistant message
    st.session_state.messages.append({"role": "assistant", "content": answer})
