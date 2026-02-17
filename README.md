```markdown
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

Install Ollama from:  
https://ollama.com/download

Then pull the default model:

```bash
ollama pull llama3:8b
```

Test it:

```bash
ollama run llama3:8b
```

Ask a simple question, then exit with `Ctrl+C`.

---

## 2. Clone and set up

```bash
git clone <YOUR_REPO_URL> product-atlas
cd product-atlas
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Configure environment

Copy the example env file:

```bash
cp config/settings.example.env config/settings.env
```

Edit `config/settings.env` as needed:

- `LLM_MODEL_NAME` – which Ollama model to use (default: `llama3:8b`)
- `LLM_TEMPERATURE` – 0.0–0.3 for factual, higher for creative
- `EMBEDDING_MODEL_NAME` – default `BAAI/bge-m3`
- `INGEST_DATA_DIR` – folder with your raw docs (default: `data/raw`)
- `CHUNK_SIZE` / `CHUNK_OVERLAP` – RAG chunking behavior
- `RAG_TOP_K` – how many chunks to retrieve per question
- `APP_TITLE` – optional custom title for the UI

---

## 4. Add your documents

Create the data folder:

```bash
mkdir -p data/raw
```

Drop your files under `data/raw/` (this folder is ignored by Git), for example:

- `data/raw/prds/...`
- `data/raw/strategy/...`
- `data/raw/transcripts/...`

Supported extensions:

- `.txt`, `.md`
- `.pdf`

---

## 5. Ingest documents

From the project root:

```bash
source .venv/bin/activate        # if not already active
python -c "from app.ingest import ingest_folder; ingest_folder()"
```

You should see output like:

```text
Chroma persist dir: /path/to/product-atlas/data/chroma
Ingesting from data/raw into collection 'pm_docs'
Ingested XXX chunks from ...
Done. Files ingested: N, total chunks: M
Collection count from inside ingest: M
```

You can sanity-check configuration:

```bash
python scripts/config_debug.py
```

---

## 6. Run the UI

From the project root:

```bash
source .venv/bin/activate
streamlit run app/ui_streamlit.py
```

Streamlit will open a browser window (usually at `http://localhost:8501`).

- Type a question in the text area (e.g. `Summarize the main themes in my discovery interviews.`).
- Adjust “Top-k (RAG)” in the sidebar if needed.
- Click **Ask**.

---

## 7. Command-line usage (optional)

You can call the RAG function directly from Python:

```bash
source .venv/bin/activate
python
```

```python
from app.rag import rag_answer
print(rag_answer("What are the success metrics mentioned in my docs?"))
```

---

## 8. Project structure

```text
product-atlas/
  app/
    __init__.py           # loads config/settings.env
    llm_client.py         # talks to Ollama
    embeddings.py         # embedding model (bge-m3)
    vector_store.py       # Chroma (PersistentClient)
    ingest.py             # load + chunk + ingest docs
    rag.py                # RAG orchestration
    ui_streamlit.py       # Streamlit UI
  config/
    settings.example.env  # template for config
    settings.env          # local config (ignored by Git)
  data/
    raw/                  # your docs (ignored by Git)
    chroma/               # Chroma DB files (ignored by Git)
  scripts/
    config_debug.py       # prints current config
  requirements.txt
  .gitignore
  README.md
```

---

## 9. Git and privacy best practices

Recommended `.gitignore` entries:

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd

# Virtual env
.venv/

# Local data
data/chroma/
data/raw/

# Config with personal settings
config/settings.env

# OS/editor
.DS_Store
.idea/
.vscode/
*.swp
```

Guidelines:

- Do **not** commit:
  - `data/raw/` (your actual documents)
  - `data/chroma/` (vector DB)
  - `.venv/`
  - `config/settings.env` (personal config)
- Each person:
  - Clones the repo.
  - Creates their own `config/settings.env` from `settings.example.env`.
  - Adds their own docs under `data/raw/`.
  - Runs ingestion + UI locally.

---

## 10. Quick start checklist

1. Install Python 3.11+ and Ollama.  
2. `ollama pull llama3:8b`.  
3. Clone repo and create venv.  
4. `pip install -r requirements.txt`.  
5. Copy `settings.example.env` → `settings.env`.  
6. Add docs under `data/raw/`.  
7. Run ingestion.  
8. `streamlit run app/ui_streamlit.py`.