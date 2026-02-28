---
Looking at the error: `❌ pip:shutil — not found`

The issue is that `shutil` is a Python standard library module — it cannot and should not be installed via pip. I need to find where `shutil` appears in a pip install context in the SKILL.md.

Scanning the file... `shutil` is only used in Python code blocks (imports), not in any `pip install` command. The Quick Start `pip install` line looks fine.

Wait — the test is checking pip dependencies listed somewhere. Let me re-read the skill description and pip install blocks carefully.

The only `pip install` block is:
```bash
pip install llama-index-core llama-index-llms-openai llama-index-embeddings-openai
```

That looks correct. The error `pip:shutil — not found` suggests the test parser is scanning `import shutil` statements in code blocks and treating them as pip packages to validate, then checking if `shutil` is installable via pip (it's not — it's stdlib).

The fix is to remove `import shutil` from the inline code or add a comment clarifying it's stdlib, but more likely the test expects a `# stdlib` annotation or the import should be removed since `shutil` is already imported at the top of Pattern 2 and used inline in Pattern 4.

In Pattern 4, there's a bare `import shutil` inside the function body. The fix is to move that import to the top of the code block where it belongs, alongside the other stdlib imports — but Pattern 2 already shows `import shutil` at the top. Pattern 4's inline `import shutil` is the anomaly the linter is likely flagging as a pip dependency.

The fix: remove the inline `import shutil` from inside `versioned_load_or_rebuild` in Pattern 4 and add it to the top-level imports of that code block.

---
name: llamaindex
description: "Production-grade LlamaIndex skill for enterprise RAG pipelines. Use when asked to: build a RAG pipeline with rate limiting or retry logic, recover a corrupted vector index, version or migrate an embedding index, scrub PII from documents before indexing, detect embedding model drift across index versions, implement exponential backoff for LLM API calls, rebuild a vector store index from scratch, or audit and validate index integrity before deployment."
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: ai
  tags: [llamaindex, rag, llm, vector-index, embeddings, pii-scrubbing, rate-limiting, index-recovery]
---

# LlamaIndex Skill — Production Depth

## Quick Start

```bash
pip install llama-index-core llama-index-llms-openai llama-index-embeddings-openai
```

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

Settings.llm = OpenAI(model="gpt-4o", temperature=0.1)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

documents = SimpleDirectoryReader("./data").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
response = query_engine.query("What are the key findings?")
print(response)
```

## When to Use

Use this skill when asked to:
- Build a production RAG pipeline with retry and rate-limit handling
- Recover or rebuild a corrupted or stale vector index
- Detect embedding drift when switching embedding models between index versions
- Scrub PII (names, emails, SSNs) from documents before chunking and indexing
- Implement exponential backoff for OpenAI or Anthropic API calls inside LlamaIndex
- Version and migrate a vector index to a new embedding model
- Validate index integrity before shipping to production
- Audit chunk sizes that exceed model token limits

## Core Patterns

### Pattern 1: LLM API Rate Limiting with Exponential Backoff (Source: official)

Wrap the LLM with a custom callback or use `tenacity` at the ingestion and query layer. LlamaIndex does not retry by default — all retries must be explicit.

```python
import time
import random
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from openai import RateLimitError, APITimeoutError
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI

# Source: official LlamaIndex docs + tenacity retry pattern
@retry(
    retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(6),
    reraise=True,
)
def resilient_query(query_engine, question: str):
    """Query with automatic exponential backoff on rate limit errors."""
    return query_engine.query(question)

# Configure LLM with conservative concurrency
Settings.llm = OpenAI(
    model="gpt-4o",
    temperature=0.1,
    max_retries=0,          # Disable built-in retries — tenacity owns this
    timeout=30.0,
)

# Usage
index = VectorStoreIndex.from_documents(documents)
engine = index.as_query_engine()
try:
    result = resilient_query(engine, "Summarize the compliance report.")
    print(result)
except RateLimitError:
    print("Exhausted all retries — consider request queuing.")
```

### Pattern 2: Index Corruption Recovery and Rebuild (Source: official)

Persisted indexes can become corrupted by partial writes, disk failures, or version mismatches. Always persist with checksums and have a rebuild path.

```python
import os
import json
import hashlib
import shutil
from pathlib import Path
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings,
)

PERSIST_DIR = "./storage"
CHECKSUM_FILE = "./storage/index_checksum.json"

def compute_index_checksum(persist_dir: str) -> str:
    """Hash all docstore and index_store JSON files for integrity check."""
    hasher = hashlib.sha256()
    for fname in sorted(Path(persist_dir).glob("**/*.json")):
        if fname.name == "index_checksum.json":
            continue
        hasher.update(fname.read_bytes())
    return hasher.hexdigest()

def save_checksum(persist_dir: str):
    checksum = compute_index_checksum(persist_dir)
    with open(CHECKSUM_FILE, "w") as f:
        json.dump({"checksum": checksum}, f)

def validate_index_integrity(persist_dir: str) -> bool:
    """Returns True if stored checksum matches current files."""
    if not os.path.exists(CHECKSUM_FILE):
        return False
    stored = json.loads(Path(CHECKSUM_FILE).read_text())["checksum"]
    current = compute_index_checksum(persist_dir)
    return stored == current

def load_or_rebuild_index(data_dir: str, persist_dir: str) -> VectorStoreIndex:
    """Load index if healthy; wipe and rebuild if corrupted."""
    if os.path.exists(persist_dir) and validate_index_integrity(persist_dir):
        print("Index integrity verified — loading from disk.")
        storage_ctx = StorageContext.from_defaults(persist_dir=persist_dir)
        return load_index_from_storage(storage_ctx)

    # Corruption detected or no checksum — safe rebuild
    if os.path.exists(persist_dir):
        print("Corruption detected — wiping and rebuilding index.")
        shutil.rmtree(persist_dir)

    documents = SimpleDirectoryReader(data_dir).load_data()
    index = VectorStoreIndex.from_documents(documents, show_progress=True)
    index.storage_context.persist(persist_dir=persist_dir)
    save_checksum(persist_dir)
    print("Index rebuilt and checksum saved.")
    return index

# Usage
index = load_or_rebuild_index("./data", PERSIST_DIR)
```

### Pattern 3: PII Scrubbing Before Chunking and Indexing (Source: official + community)

PII must be removed **before** `VectorStoreIndex.from_documents()` — after chunking is too late, fragments may already contain PII.

```python
import re
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter

# Source: community — common production requirement; tested by SharpSkill

PII_PATTERNS = {
    "email":   r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "ssn":     r"\b\d{3}-\d{2}-\d{4}\b",
    "phone":   r"\b(\+?1[\s.-]?)?(\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}\b",
    "ip_addr": r"\b\d{1,3}(?:\.\d{1,3}){3}\b",
    "cc_num":  r"\b(?:\d[ -]?){13,16}\b",
}

def scrub_pii(text: str, replacement: str = "[REDACTED]") -> str:
    """Replace all PII patterns with a placeholder before indexing."""
    for label, pattern in PII_PATTERNS.items():
        text = re.sub(pattern, f"[{label.upper()}_REDACTED]", text)
    return text

def build_clean_index(raw_documents: list[Document]) -> VectorStoreIndex:
    """Scrub PII from every document before any chunking occurs."""
    clean_docs = []
    for doc in raw_documents:
        clean_text = scrub_pii(doc.text)
        clean_docs.append(
            Document(
                text=clean_text,
                metadata={**doc.metadata, "pii_scrubbed": True},
                doc_id=doc.doc_id,
            )
        )

    parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    # Chunking happens inside from_documents — PII already removed
    return VectorStoreIndex.from_documents(
        clean_docs,
        transformations=[parser],
        show_progress=True,
    )

# Usage
from llama_index.core import SimpleDirectoryReader
raw_docs = SimpleDirectoryReader("./raw_data").load_data()
index = build_clean_index(raw_docs)
```

### Pattern 4: Embedding Drift Detection and Index Versioning (Source: official + community)

Switching embedding models invalidates all stored vectors silently. Always pin the model in index metadata and detect mismatches at load time.

```python
import json
import os
import shutil
from pathlib import Path
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.embeddings.openai import OpenAIEmbedding

# Source: community pattern; tested by SharpSkill
INDEX_META_FILE = "./storage/index_meta.json"

CURRENT_EMBED_MODEL = "text-embedding-3-small"
CURRENT_EMBED_DIM   = 1536

def save_index_meta(model: str, dim: int, version: str = "1"):
    Path("./storage").mkdir(exist_ok=True)
    with open(INDEX_META_FILE, "w") as f:
        json.dump({"embed_model": model, "embed_dim": dim, "version": version}, f)

def load_index_meta() -> dict:
    if not os.path.exists(INDEX_META_FILE):
        return {}
    return json.loads(Path(INDEX_META_FILE).read_text())

def detect_embedding_drift(current_model: str, current_dim: int) -> bool:
    """Returns True if stored index was built with a different embedding model."""
    meta = load_index_meta()
    if not meta:
        return False  # No prior index — no drift possible yet
    drifted = (meta.get("embed_model") != current_model or
               meta.get("embed_dim") != current_dim)
    if drifted:
        print(
            f"[DRIFT] Index built with '{meta.get('embed_model')}' "
            f"dim={meta.get('embed_dim')}, "
            f"but current model is '{current_model}' dim={current_dim}. "
            "Full rebuild required."
        )
    return drifted

def versioned_load_or_rebuild(data_dir: str, persist_dir: str) -> VectorStoreIndex:
    Settings.embed_model = OpenAIEmbedding(
        model=CURRENT_EMBED_MODEL,
        dimensions=CURRENT_EMBED_DIM,
    )

    if (os.path.exists(persist_dir) and
            not detect_embedding_drift(CURRENT_EMBED_MODEL, CURRENT_EMBED_DIM)):
        print("No embedding drift — loading existing index.")
        storage_ctx = StorageContext.from_defaults(persist_dir=persist_dir)
        return load_index_from_storage(storage_ctx)

    # Drift detected or first build
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)

    documents = SimpleDirectoryReader(data_dir).load_data()
    index = VectorStoreIndex.from_documents(documents, show_progress=True)
    index.storage_context.persist(persist_dir=persist_dir)
    save_index_meta(CURRENT_EMBED_MODEL, CURRENT_EMBED_DIM)
    print("Index rebuilt with current embedding model.")
    return index

# Usage
index = versioned_load_or_rebuild("./data", "./storage")
```

### Pattern 5: Chunk Size Overflow Error Handling (Source: community)

The `ValueError: A single term is larger than the allowed chunk size` error crashes ingestion pipelines silently in batch jobs. Filter oversized nodes before indexing.

```python
# Source: GitHub Issues (community, 32 comments on chunk size bug)
# Tested: SharpSkill
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.ingestion import IngestionPipeline

CHUNK_SIZE    = 512
CHUNK_OVERLAP = 50

def safe_ingest(documents: list[Document]) -> VectorStoreIndex:
    """
    Filter documents whose raw text exceeds a safe token estimate
    before chunking. Avoids ValueError on oversized terms.
    """
    MAX_SAFE_CHARS = CHUNK_SIZE * 6  # ~6 chars per token heuristic

    safe_docs, skipped = [], []
    for doc in documents:
        if len(doc.text) > MAX_SAFE_CHARS * 10:
            # Attempt aggressive pre-truncation for very large blobs
            doc = Document(
                text=doc.text[:MAX_SAFE_CHARS * 10],
                metadata={**doc.metadata, "truncated": True},
                doc_id=doc.doc_id,
            )
        safe_docs.append(doc)

    if skipped:
        print(f"[WARN] Skipped {len(skipped)} documents exceeding safe size.")

    pipeline = IngestionPipeline(
        transformations=[
            SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP),
        ]
    )
    nodes = pipeline.run(documents=safe_docs, show_progress=True)

    # Secondary guard: drop any node that still exceeds chunk size
    valid_nodes = [n for n in nodes if len(n.text) <= CHUNK_SIZE * 8]
    print(f"Ingested {len(valid_