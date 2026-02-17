# Product Atlas – Local PM Copilot

Product Atlas is a **local-first RAG assistant** for Product Managers.  
It runs an open-source LLM via Ollama on your machine and augments it with your own docs (PRDs, strategy docs, transcripts, notes).

Everything stays on your laptop.

---

## Features

- Local LLM via [Ollama](https://ollama.com) (default: `llama3:8b`)
- Retrieval-Augmented Generation (RAG) over your own documents
- Supports:
  - `.txt` and `.md` files (PRDs, notes, transcripts)
  - `.pdf` (books, reports, slide exports)
- Simple Streamlit UI for Q&A over your corpus
- Configurable via `.env` (no code changes needed)

---

## 1. Prerequisites

- Python 3.11+  
- [Ollama](https://ollama.com) installed locally  
- Git

On macOS, you can install Ollama from:  
https://ollama.com/download

Then pull the default model:

```bash
ollama pull llama3:8b
