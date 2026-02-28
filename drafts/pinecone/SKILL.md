---
name: pinecone
description: "Production Pinecone vector database client for Python. Handles upsert, query, and index management with retry logic, namespace isolation, API key rotation, and dimension mismatch guards. Use when user asks to: store embeddings in Pinecone, query similar vectors, build a RAG pipeline with Pinecone, manage Pinecone indexes, upsert vectors with metadata, filter vector search results, handle Pinecone API errors, or rotate Pinecone API keys in production."
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: database
  tags: [pinecone, vector-database, embeddings, rag, semantic-search, ai]
---

# Pinecone Skill

## Quick Start

```bash
pip install pinecone
export PINECONE_API_KEY="your-api-key"
```

```python
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone()  # reads PINECONE_API_KEY from env

pc.create_index(
    name="prod-embeddings",
    dimension=1536,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
)

index = pc.Index("prod-embeddings")
index.upsert(vectors=[{"id": "doc-1", "values": [0.1] * 1536, "metadata": {"text": "hello"}}])
results = index.query(vector=[0.1] * 1536, top_k=5, include_metadata=True)
```

## When to Use

Use this skill when asked to:
- Store or upsert embeddings into Pinecone
- Query Pinecone for nearest-neighbor or semantic search results
- Build a RAG pipeline backed by Pinecone vector storage
- Create, describe, or delete Pinecone serverless or pod indexes
- Isolate tenant data using Pinecone namespaces
- Filter vector search by metadata fields
- Handle Pinecone API errors with retry and backoff
- Rotate or manage Pinecone API keys without downtime
- Validate embedding dimensions before upsert
- Implement multi-tenant vector search with namespace isolation

## Core Patterns

### Pattern 1: Retry with Exponential Backoff (Source: official)

Pinecone's API returns `429 Too Many Requests` and transient `503` errors under load. Wrap all data-plane calls in a retry loop before going to production.

```python
import time
import random
from pinecone import Pinecone
from pinecone.exceptions import PineconeException

def upsert_with_backoff(index, vectors, namespace="", max_retries=5):
    """Upsert vectors with exponential backoff on transient errors."""
    for attempt in range(max_retries):
        try:
            return index.upsert(vectors=vectors, namespace=namespace)
        except PineconeException as exc:
            # Retry on rate-limit (429) and server errors (5xx)
            if attempt == max_retries - 1:
                raise
            wait = (2 ** attempt) + random.uniform(0, 1)
            print(f"Attempt {attempt + 1} failed: {exc}. Retrying in {wait:.2f}s")
            time.sleep(wait)

pc = Pinecone()
index = pc.Index("prod-embeddings")

batch = [{"id": f"doc-{i}", "values": [0.1] * 1536} for i in range(100)]
upsert_with_backoff(index, batch, namespace="tenant-acme")
```

### Pattern 2: Namespace Isolation for Multi-Tenant Data (Source: official)

Namespaces partition vectors within a single index. Each tenant's vectors are invisible to other tenants' queries without any application-level filtering.

```python
from pinecone import Pinecone

pc = Pinecone()
index = pc.Index("prod-embeddings")

TENANT_NS = {
    "acme":  "tenant-acme",
    "globex": "tenant-globex",
}

def upsert_for_tenant(tenant_id: str, vectors: list[dict]):
    ns = TENANT_NS.get(tenant_id)
    if ns is None:
        raise ValueError(f"Unknown tenant: {tenant_id}")
    index.upsert(vectors=vectors, namespace=ns)

def query_for_tenant(tenant_id: str, query_vector: list[float], top_k: int = 5):
    ns = TENANT_NS.get(tenant_id)
    if ns is None:
        raise ValueError(f"Unknown tenant: {tenant_id}")
    return index.query(
        vector=query_vector,
        top_k=top_k,
        namespace=ns,
        include_metadata=True,
    )

upsert_for_tenant("acme", [{"id": "doc-1", "values": [0.2] * 1536, "metadata": {"src": "acme"}}])
results = query_for_tenant("acme", [0.2] * 1536)
print(results["matches"])
```

### Pattern 3: Vector Dimension Mismatch Guard (Source: official + community)

Upserting vectors whose dimension differs from the index dimension raises a hard API error. Validate dimensions client-side before any network call.

```python
from pinecone import Pinecone

pc = Pinecone()
index = pc.Index("prod-embeddings")

INDEX_DIMENSION = 1536  # must match index creation spec

class DimensionMismatchError(ValueError):
    pass

def safe_upsert(index, vectors: list[dict], namespace: str = ""):
    for vec in vectors:
        dim = len(vec["values"])
        if dim != INDEX_DIMENSION:
            raise DimensionMismatchError(
                f"Vector '{vec['id']}' has dimension {dim}, "
                f"expected {INDEX_DIMENSION}."
            )
    return index.upsert(vectors=vectors, namespace=namespace)

# Will raise DimensionMismatchError before touching the API
try:
    safe_upsert(index, [{"id": "bad-vec", "values": [0.1] * 512}])
except DimensionMismatchError as e:
    print(f"Blocked bad upsert: {e}")
```

### Pattern 4: API Key Rotation Without Downtime (Source: official)

Keep the active key in a secret manager (AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault). Re-instantiate the client on rotation without restarting the process.

```python
import os
import boto3
from pinecone import Pinecone

def get_api_key_from_secrets_manager(secret_name: str) -> str:
    """Fetch the current Pinecone API key from AWS Secrets Manager."""
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_name)
    return response["SecretString"]

class RotatingPineconeClient:
    """Pinecone client that re-reads its key on each rotation signal."""

    def __init__(self, secret_name: str, index_name: str):
        self._secret_name = secret_name
        self._index_name = index_name
        self._refresh()

    def _refresh(self):
        key = get_api_key_from_secrets_manager(self._secret_name)
        self._pc = Pinecone(api_key=key)
        self._index = self._pc.Index(self._index_name)

    def rotate(self):
        """Call this after rotating the secret in Secrets Manager."""
        self._refresh()
        print("Pinecone client re-initialised with new API key.")

    @property
    def index(self):
        return self._index

client = RotatingPineconeClient("prod/pinecone/api-key", "prod-embeddings")
client.index.upsert(vectors=[{"id": "doc-1", "values": [0.1] * 1536}])

# Later, after key rotation:
# client.rotate()
```

### Pattern 5: Batched Upsert for Large Datasets (Source: official)

Pinecone recommends batches of 100 vectors (≤2 MB per request). Larger payloads are rejected with `400 Bad Request`.

```python
from itertools import islice
from pinecone import Pinecone

def chunked(iterable, size):
    it = iter(iterable)
    while True:
        batch = list(islice(it, size))
        if not batch:
            break
        yield batch

pc = Pinecone()
index = pc.Index("prod-embeddings")

all_vectors = [
    {"id": f"doc-{i}", "values": [float(i % 10) / 10] * 1536}
    for i in range(10_000)
]

for batch in chunked(all_vectors, 100):
    index.upsert(vectors=batch, namespace="bulk-load")

print("Bulk upsert complete.")
```

### Pattern 6: Metadata Filtering on Query (Source: official)

Pinecone supports structured metadata filters using a MongoDB-style query syntax. Filters run server-side and reduce the candidate set before ANN scoring.

```python
from pinecone import Pinecone

pc = Pinecone()
index = pc.Index("prod-embeddings")

query_vec = [0.3] * 1536

results = index.query(
    vector=query_vec,
    top_k=10,
    namespace="tenant-acme",
    include_metadata=True,
    filter={
        "category": {"$in": ["finance", "legal"]},
        "year":     {"$gte": 2022},
        "archived": {"$eq": False},
    },
)

for match in results["matches"]:
    print(match["id"], match["score"], match["metadata"])
```

### Pattern 7: Error Handling — Catching Specific Exceptions (Source: community)

Production code must distinguish between retryable errors (rate limit, server fault) and terminal errors (auth failure, bad request) to avoid infinite retry loops.

```python
# Source: community / # Tested: SharpSkill
import time
from pinecone import Pinecone
from pinecone.exceptions import PineconeException, UnauthorizedException

pc = Pinecone()
index = pc.Index("prod-embeddings")

def robust_query(vector, top_k=5, retries=3):
    for attempt in range(retries):
        try:
            return index.query(vector=vector, top_k=top_k, include_metadata=True)
        except UnauthorizedException:
            # Terminal — wrong or expired key; do not retry
            raise RuntimeError("Pinecone auth failed. Check PINECONE_API_KEY.")
        except PineconeException as exc:
            status = getattr(exc, "status", None)
            if status and 400 <= status < 500 and status != 429:
                # Bad request — retrying won't help
                raise
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise

result = robust_query([0.1] * 1536)
print(result["matches"])
```

## Production Notes

**1. Upsert batch size limit causes silent truncation (Source: GitHub Issues / community reports)**
Sending more than ~2 MB per upsert request silently drops vectors or returns a `400`. Always chunk at ≤100 vectors. Use the `chunked()` helper in Pattern 5. Monitor `upserted_count` in the response to verify the expected number was accepted.

**2. Namespace queries never cross namespaces — missing results look like a search bug (Source: community)**
If a query returns 0 matches despite data existing in the index, the most common cause is a namespace mismatch. The default namespace is the empty string `""`. Always pass `namespace` explicitly on both upsert and query. Log the namespace used in every call during debugging.

**3. Index readiness race condition on create (Source: official docs + community)**
`pc.create_index()` returns before the index is ready to accept data. Immediately upsert after create often returns `503`. Poll `pc.describe_index(name).status.ready` before issuing data-plane calls.

```python
import time
from pinecone import Pinecone

pc = Pinecone()
pc.create_index(name="new-index", dimension=1536, metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"))

while not pc.describe_index("new-index").status.ready:
    time.sleep(2)
print("Index ready.")
```

**4. Metadata filter fields must be indexed at collection time (Source: official docs)**
Filtering on a metadata key that was not present during upsert returns wrong or empty results — not an error. Enforce a metadata schema in your application layer and validate before upsert. There is no server-side schema enforcement.

**5. gRPC transport improves throughput but requires separate install (Source: official docs)**
`pinecone[grpc]` enables the `GRPCIndex` client which gives 2–3× higher upsert throughput for bulk loads. Switch back to REST for environments where gRPC port 443 is firewalled. Do not mix REST and gRPC clients in the same process without testing.

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|------------|-----|
| `400 Bad Request` on upsert | Batch exceeds 2 MB or vector count > 100 | Chunk to ≤100 vectors per request |
| Query returns 0 matches despite existing data | Namespace mismatch (empty string vs named) | Always pass `namespace=` explicitly on upsert and query |
| `PineconeException: dimension mismatch` | Embedding model output size ≠ index dimension | Validate `len(vec["values"]) == INDEX_DIMENSION` before upsert |
| `503` immediately after `create_index` | Index not yet ready to serve traffic | Poll `describe_index().status.ready` before first data call |
| `401 Unauthorized` after key rotation | Old API key cached in client instance | Re-instantiate `Pinecone(api_key=new_key)` after rotation |
| Metadata filter returns unexpected results | Filtering on key absent in some vectors | Ensure all upserted vectors carry a consistent metadata schema |

## Pre-Deploy Checklist

- [ ] `PINECONE_API_KEY` stored in a secrets manager, never hardcoded or committed to source control
- [ ] Index dimension verified to match your embedding model output (e.g., `text-embedding-3-small` → 1536)
- [ ] All upsert calls chunked to ≤100 vectors per request
- [ ] `namespace=` parameter set explicitly on every upsert and query (no implicit default)
- [ ] Index readiness polling in place before first upsert after creation
- [ ] Retry logic with exponential backoff wrapping all data-plane calls (`upsert`, `query`, `fetch`, `delete`)
- [ ] Metadata schema validated client-side before upsert to prevent silent filter mismatches
- [ ] `pinecone[grpc]` evaluated for bulk-load pipelines; gRPC port 443 confirmed open in target environment

## Troubleshooting

**Error: `PineconeException: Vector dimension X does not match the dimension of the index Y`**
Cause: The embedding you generated has a different length than the dimension specified when the index was created.
Fix: Check your embedding model's output dimension. Re-create the index with the correct dimension, or use a model that matches the existing index. Add the `safe_upsert()` guard from Pattern 3.

**Error: `401 Unauthorized` / `Forbidden - a valid x-pinecone-api-key header must be sent`**
Cause: Invalid, expired, or incorrectly scoped API key.
Fix: Verify `PINECONE_API_KEY` in your environment. Confirm the key has the correct permissions (read/write) for the target index in the Pinecone console. After rotation, re-instantiate the client.

**Error: Query returns 0 results despite vectors being upserted**
Cause: Namespace mismatch — vectors upserted to `"tenant-acme"` will not appear in a query against `""`.
Fix: Log `namespace` on every call. Ensure upsert