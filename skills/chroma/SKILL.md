---
name: chroma
description: "Chroma is the open-source AI-native vector database for building LLM-powered search and retrieval applications. Use when asked to: store and query embeddings for semantic search, build a RAG (retrieval-augmented generation) pipeline, add vector search to an AI app, persist and reload a vector index, filter documents by metadata in a vector store, integrate ChromaDB with LangChain or LlamaIndex, create or manage document collections with embeddings, or switch from in-memory to persistent/client-server Chroma storage."
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: ai
  tags: [chroma, chromadb, vector-database, embeddings, semantic-search, rag, llm, langchain]
trace_id: 92d9493537e9
generated_at: '2026-02-28T22:43:21'
generator: sharpskill-v1.0 (legacy)
---

# Chroma Skill

## Quick Start

```bash
pip install chromadb
# JavaScript: npm install chromadb
# Client-server mode: chroma run --path /chroma_db_path
```

```python
import chromadb

# In-memory client (prototyping)
client = chromadb.Client()

# Persistent client (recommended for production)
client = chromadb.PersistentClient(path="./chroma_db")

# Create or retrieve a collection
collection = client.get_or_create_collection("my-documents")

# Add documents (Chroma handles embedding automatically)
collection.add(
    documents=["The sky is blue", "Roses are red"],
    metadatas=[{"source": "poem"}, {"source": "poem"}],
    ids=["doc1", "doc2"],
)

# Query by natural language
results = collection.query(query_texts=["What color is the sky?"], n_results=1)
print(results)
```

## When to Use
Use this skill when asked to:
- Store document embeddings in a local or hosted vector database
- Build a RAG (retrieval-augmented generation) pipeline with LLMs
- Perform semantic / similarity search over documents
- Persist a vector index to disk and reload it across sessions
- Filter query results by metadata fields (e.g., source, date, category)
- Integrate a vector store with LangChain, LlamaIndex, or OpenAI
- Upsert, update, or delete documents in an embedding collection
- Run Chroma as a client-server service (Docker or `chroma run`)

## Core Patterns

### Pattern 1: Persistent Client with Custom Embeddings (Source: official)
Use when you need disk persistence and supply your own embedding vectors.

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("custom-embeddings")

# Provide pre-computed embeddings (e.g., from OpenAI)
collection.add(
    embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
    documents=["Document A", "Document B"],
    metadatas=[{"author": "alice"}, {"author": "bob"}],
    ids=["id1", "id2"],
)

# Query with a pre-computed embedding vector
results = collection.query(
    query_embeddings=[[0.1, 0.2, 0.3]],
    n_results=2,
    where={"author": "alice"},      # metadata filter
)
print(results["documents"])
```

### Pattern 2: Client-Server Mode (Source: official)
Run Chroma as a standalone server for multi-process or multi-container access.

```bash
# Start the server
chroma run --path ./chroma_db --port 8000
```

```python
import chromadb

# Connect from any process / container
client = chromadb.HttpClient(host="localhost", port=8000)

collection = client.get_or_create_collection("shared-collection")
collection.upsert(
    documents=["Hello world"],
    ids=["doc1"],
)

results = collection.query(query_texts=["greetings"], n_results=1)
print(results)
```

### Pattern 3: LangChain Integration (Source: official)
Use Chroma as the vector store backend in a LangChain retrieval chain.

```python
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

embeddings = OpenAIEmbeddings()

# Build and persist the vector store
vectorstore = Chroma.from_texts(
    texts=["Document text here", "Another document"],
    embedding=embeddings,
    persist_directory="./chroma_db",
    collection_name="langchain-docs",
)

# Reload from disk (separate session)
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
    collection_name="langchain-docs",   # must match original name
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
docs = retriever.invoke("What is the main topic?")
print(docs)
```

### Pattern 4: Metadata Filtering and where_document (Source: official)
Narrow query results with metadata filters and document substring search.

```python
# Metadata equality filter
results = collection.query(
    query_texts=["machine learning"],
    n_results=5,
    where={"source": "arxiv"},                       # exact match
    # where={"year": {"$gte": 2023}},                # comparison operators
    # where={"$and": [{"source":"arxiv"}, {"year":{"$gte":2023}}]},
    where_document={"$contains": "neural network"},  # document substring
)
```

### Pattern 5: Error Handling — Too Many Open Files (Source: community)
Long-running services (e.g., Django, FastAPI) must reuse the client singleton to avoid exhausting OS file descriptors.

```python
# Source: community / # Tested: SharpSkill
# BAD — creates a new client (and new file handles) on every request
def bad_query(query_text):
    client = chromadb.PersistentClient(path="./chroma_db")   # leaks handles
    collection = client.get_collection("docs")
    return collection.query(query_texts=[query_text], n_results=3)

# GOOD — module-level singleton reused across all requests
import chromadb
_client = chromadb.PersistentClient(path="./chroma_db")
_collection = _client.get_or_create_collection("docs")

def good_query(query_text):
    return _collection.query(query_texts=[query_text], n_results=3)
```

### Pattern 6: Recovering a Persisted Index After Restart (Source: community)
A common mistake is querying a different collection name than was used during ingestion, returning empty results.

```python
# Source: community / # Tested: SharpSkill

# --- Ingestion session ---
client = chromadb.PersistentClient(path="./chroma_db")
col = client.get_or_create_collection("my-rag-collection")   # note the name
col.add(documents=["fact one", "fact two"], ids=["f1", "f2"])

# --- New session (restart) ---
client = chromadb.PersistentClient(path="./chroma_db")

# WRONG — creates a new, empty collection
col = client.get_or_create_collection("my_rag_collection")   # typo: underscore

# RIGHT — use the EXACT same name used during ingestion
col = client.get_or_create_collection("my-rag-collection")
results = col.query(query_texts=["fact"], n_results=2)
print(results["documents"])   # no longer empty
```

## Production Notes

1. **Persisted index returns empty results after restart** — The most common cause is loading a different collection name (typo, case change) than was used during ingestion, or pointing `PersistentClient` at the wrong directory. Always use `client.list_collections()` to verify names. (Source: GitHub Issues)

2. **`OSError: [Errno 24] Too many open files`** — Each `PersistentClient()` call opens HNSW index files. In web frameworks (Django, FastAPI) this exhausts `ulimit` over time. Fix: instantiate the client once at module level and reuse it; or raise `ulimit -n 65536` at the OS level. (Source: GitHub Issues)

3. **`RuntimeError: Cannot return results in a contiguous 2D array`** — Triggered when HNSW parameters `ef` or `M` are set too small relative to the number of results requested. Increase `ef` via `collection_metadata={"hnsw:ef": 200, "hnsw:M": 32}` at collection creation time. (Source: GitHub Issues)

4. **Version migration breaks persisted data** — Upgrading from v0.6.x to v1.0.x changes internal storage schema. Collections created by older clients/servers will raise `chromadb.errors.InternalError` when accessed by newer versions. Always run a full export/re-import when performing major version upgrades. (Source: GitHub Issues)

5. **`Illegal instruction (core dumped)` on ARM / non-AVX CPUs** — `chroma-hnswlib` is compiled with AVX2 SIMD by default. On ARM (e.g., AWS Graviton, Bottlerocket) or older x86 CPUs without AVX2, install from source: `pip install chroma-hnswlib --no-binary chroma-hnswlib`. (Source: GitHub Issues)

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `collection.query()` returns `[]` after restart | Wrong collection name or wrong `persist_directory` path | Verify with `client.list_collections()`; use exact same name and path |
| `OSError: [Errno 24] Too many open files` | New `PersistentClient` created per request, leaking file handles | Use a module-level singleton client; raise OS `ulimit` |
| `chromadb.errors.InternalError` on `collection.get()` | Major version mismatch between client/server and persisted data | Export data before upgrade; re-import with new version |
| `RuntimeError: Cannot return results in contiguous 2D array` | HNSW `ef`/`M` too small for `n_results` requested | Set `hnsw:ef` ≥ `n_results` in `collection_metadata` at creation |
| `Illegal instruction (core dumped)` | AVX2 binary on non-AVX2 CPU (ARM, older x86) | Rebuild `chroma-hnswlib` from source without AVX2 flags |
| Token auth still allows unauthenticated connections | Auth env vars not passed through to Docker container | Explicitly set `CHROMA_SERVER_AUTH_CREDENTIALS` in container env |
| Next.js/ESM import errors with `chromadb` JS client | Package requires ESM (`type: module`) but project uses CJS | Add `"type": "module"` to `package.json` or use `.mjs` extension |

## Pre-Deploy Checklist
- [ ] `PersistentClient` instantiated once as a module-level singleton (not per-request)
- [ ] Collection name is identical between ingestion and query sessions (check with `list_collections()`)
- [ ] `persist_directory` path is an absolute path or reliably resolved relative path
- [ ] HNSW parameters (`hnsw:ef`, `hnsw:M`) tuned for expected collection size and `n_results`
- [ ] OS file descriptor limit raised (`ulimit -n 65536`) for long-running services
- [ ] Client and server versions match; migration plan in place before major upgrades
- [ ] Authentication tokens/headers configured and tested against a fresh unauthenticated request

## Troubleshooting

**Error: `RuntimeError: Cannot open header file`**
Cause: The HNSW index files on disk are corrupt or were written by an incompatible version. Often happens after an interrupted write or a version mismatch.
Fix: Delete the collection directory and re-ingest, or restore from a known-good backup. Run `client.delete_collection("name")` then recreate.

**Error: `chromadb.errors.InternalError: Error executing plan: Error sending backfill request to compactor`**
Cause: Server-side storage schema incompatibility between the version that wrote the data and the version now serving it (e.g., v0.6.x data read by v1.0.x server).
Fix: Export all collections to JSON with the old version before upgrading, then re-import with the new version.

**Error: `Illegal instruction (core dumped)`**
Cause: The pre-built `chroma-hnswlib` wheel uses AVX2 instructions not available on the current CPU (ARM, Bottlerocket, older x86).
Fix:
```bash
pip uninstall chroma-hnswlib
pip install chroma-hnswlib --no-binary chroma-hnswlib
```

**Error: Next.js `To load an ES module, set "type": "module"`**
Cause: `chromadb` JS client ships as ESM; CommonJS Next.js projects reject it.
Fix: Add `"type": "module"` to `package.json`, or dynamically import: `const { ChromaClient } = await import('chromadb');`

## Resources
- Docs: https://docs.trychroma.com/
- GitHub: https://github.com/chroma-core/chroma
- Chroma Cloud: https://trychroma.com/signup
- PyPI: https://pypi.org/project/chromadb/
- npm: https://www.npmjs.com/package/chromadb
- Discord: https://discord.gg/MMeYNTmh3x