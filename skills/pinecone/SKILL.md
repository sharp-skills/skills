---
name: pinecone
description: "Production-grade vector database skill for Pinecone. Use when asked to: store and query embeddings in Pinecone, build semantic search with vector similarity, implement RAG retrieval pipelines, isolate tenant data with namespace partitioning, handle rate limits with exponential backoff, scale pod-based indexes for high throughput, debug dimension mismatch errors on upsert, or plan capacity for production vector workloads."
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: database
  tags: [pinecone, vector-database, embeddings, semantic-search, rag, multi-tenant, production]
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
    name="my-index",
    dimension=1536,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)

index = pc.Index("my-index")
index.upsert(vectors=[{"id": "vec1", "values": [0.1] * 1536, "metadata": {"text": "hello"}}])
result = index.query(vector=[0.1] * 1536, top_k=5, include_metadata=True)
```

## When to Use

Use this skill when asked to:
- Store, query, or delete high-dimensional embeddings in a vector database
- Build semantic search or similarity search over text, images, or audio
- Implement RAG (Retrieval-Augmented Generation) retrieval pipelines
- Isolate tenant data using namespace partitioning in a shared index
- Handle Pinecone rate limit (429) errors with retry logic
- Scale pod-based indexes and plan capacity for production workloads
- Debug vector dimension mismatch errors during upsert or query
- Migrate from pinecone-client to the pinecone package (v5.1.0+ rename)
- Batch upsert large embedding datasets efficiently
- Filter query results using metadata predicates

## Core Patterns

### Pattern 1: Namespace Isolation for Multi-Tenant Security (Source: official)

Each tenant writes and reads exclusively within its own namespace. Vectors in namespace `tenant-A` are never returned in queries scoped to `tenant-B`, providing logical data isolation within a single index without provisioning separate indexes.

```python
from pinecone import Pinecone

pc = Pinecone()
index = pc.Index("shared-index")

# Write tenant data into isolated namespace
index.upsert(
    vectors=[
        {"id": "doc-1", "values": [0.2] * 1536, "metadata": {"source": "contract.pdf"}},
        {"id": "doc-2", "values": [0.4] * 1536, "metadata": {"source": "invoice.pdf"}},
    ],
    namespace="tenant-acme"
)

# Query is strictly scoped — tenant-acme cannot see tenant-globex data
results = index.query(
    vector=[0.2] * 1536,
    top_k=10,
    namespace="tenant-acme",
    include_metadata=True
)

# Delete all vectors for a tenant (e.g., GDPR right-to-erasure)
index.delete(delete_all=True, namespace="tenant-acme")
```

### Pattern 2: Batch Upsert with Chunking (Source: official)

Pinecone recommends upserting in batches of 100 vectors. Sending all vectors in a single request causes timeouts for large datasets and risks hitting request-size limits.

```python
from pinecone import Pinecone
from itertools import islice

pc = Pinecone()
index = pc.Index("my-index")

def chunked(iterable, size):
    it = iter(iterable)
    while True:
        batch = list(islice(it, size))
        if not batch:
            break
        yield batch

# Simulate a large vector dataset
all_vectors = [
    {"id": f"vec-{i}", "values": [float(i % 10) / 10] * 1536, "metadata": {"seq": i}}
    for i in range(10_000)
]

for batch in chunked(all_vectors, 100):
    index.upsert(vectors=batch, namespace="production")

print(f"Upserted {len(all_vectors)} vectors in batches of 100")
```

### Pattern 3: Exponential Backoff for Rate Limit Errors (Source: official + community)

Pinecone returns HTTP 429 on rate limit and HTTP 503 on transient unavailability. A bare retry loop without backoff hammers the endpoint and prolongs throttling. Use jittered exponential backoff capped at a sensible ceiling.

```python
import time
import random
from pinecone import Pinecone
from pinecone.exceptions import PineconeApiException

pc = Pinecone()
index = pc.Index("my-index")

def upsert_with_backoff(vectors, namespace, max_retries=6, base_delay=1.0, max_delay=60.0):
    """
    Upsert with jittered exponential backoff.
    Retries on 429 (rate limit) and 503 (transient).
    # Source: community / # Tested: SharpSkill
    """
    for attempt in range(max_retries):
        try:
            return index.upsert(vectors=vectors, namespace=namespace)
        except PineconeApiException as e:
            status = e.status
            if status in (429, 503) and attempt < max_retries - 1:
                delay = min(max_delay, base_delay * (2 ** attempt))
                jitter = random.uniform(0, delay * 0.2)
                wait = delay + jitter
                print(f"HTTP {status} on attempt {attempt + 1}. Retrying in {wait:.2f}s...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Max retries exceeded")

# Usage
upsert_with_backoff(
    vectors=[{"id": "v1", "values": [0.1] * 1536}],
    namespace="production"
)
```

### Pattern 4: Vector Dimension Mismatch Error Handling (Source: community)

Upserting a vector whose dimension differs from the index's configured dimension raises a hard error. This commonly occurs when switching embedding models (e.g., from `text-embedding-ada-002` at 1536 dims to `text-embedding-3-small` at 1536 or 512 dims depending on truncation settings).

```python
from pinecone import Pinecone
from pinecone.exceptions import PineconeApiException

pc = Pinecone()

def safe_upsert(index_name: str, vectors: list, namespace: str = ""):
    """
    Validates vector dimensions against index spec before upserting.
    Prevents partial-batch failures from dimension mismatches.
    # Source: community / # Tested: SharpSkill
    """
    index = pc.Index(index_name)
    index_info = pc.describe_index(index_name)
    expected_dim = index_info.dimension

    mismatches = [
        v["id"] for v in vectors if len(v["values"]) != expected_dim
    ]
    if mismatches:
        raise ValueError(
            f"Dimension mismatch for vector IDs {mismatches}. "
            f"Index '{index_name}' expects {expected_dim} dims. "
            f"Got {[len(v['values']) for v in vectors if v['id'] in mismatches]}. "
            "Re-embed with the correct model or recreate the index."
        )

    try:
        return index.upsert(vectors=vectors, namespace=namespace)
    except PineconeApiException as e:
        if "dimension" in str(e).lower():
            raise ValueError(
                f"Pinecone rejected upsert due to dimension error: {e}. "
                "Verify your embedding model matches the index dimension."
            ) from e
        raise

# Example: catch mismatch before it hits the API
safe_upsert(
    index_name="my-index",
    vectors=[{"id": "bad-vec", "values": [0.1] * 768}],  # wrong dim
    namespace="production"
)
```

### Pattern 5: Pod Scaling and Capacity Planning (Source: official)

Pod-based indexes require explicit sizing. Under-provisioned pods cause high query latency and failed upserts once capacity is exhausted. Use `describe_index_stats` to monitor fill rate before scaling.

```python
from pinecone import Pinecone, PodSpec

pc = Pinecone()

# Create a production pod index with explicit sizing
# p2 pods: optimized for low-latency query; s1: storage-optimized
pc.create_index(
    name="prod-index",
    dimension=1536,
    metric="cosine",
    spec=PodSpec(
        environment="us-east1-gcp",
        pod_type="p2.x2",    # x2 = 2x base pod resources
        pods=2,              # number of pods
        replicas=2,          # read replicas for query throughput
        shards=1             # shards for write throughput (>1 for >1M vecs/shard)
    )
)

index = pc.Index("prod-index")

# Monitor capacity before deciding to scale
stats = index.describe_index_stats()
total_vectors = stats.total_vector_count
namespaces = stats.namespaces

print(f"Total vectors: {total_vectors}")
for ns, ns_stats in namespaces.items():
    print(f"  Namespace '{ns}': {ns_stats.vector_count} vectors")

# Capacity thresholds (rule of thumb):
# p1.x1 pod  → ~1M vectors at 1536 dims
# p2.x1 pod  → ~1M vectors, faster query
# s1.x1 pod  → ~5M vectors (storage-optimized, slower query)
# Scale pods or shards when approaching 80% fill rate

# Scale up replicas for increased query throughput (no downtime)
# pc.configure_index("prod-index", replicas=4)
```

### Pattern 6: Async Upsert for High-Throughput Pipelines (Source: official)

```python
import asyncio
from pinecone import PineconeAsyncio, ServerlessSpec

async def bulk_ingest(all_vectors: list):
    async with PineconeAsyncio() as pc:
        if not await pc.has_index("async-index"):
            await pc.create_index(
                name="async-index",
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )

        index = pc.Index("async-index")

        # Fan out upsert batches concurrently
        batch_size = 100
        batches = [all_vectors[i:i+batch_size] for i in range(0, len(all_vectors), batch_size)]
        tasks = [index.upsert(vectors=batch, namespace="async-ns") for batch in batches]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
            print(f"Batch errors: {errors}")
        print(f"Ingested {len(all_vectors)} vectors across {len(batches)} concurrent batches")

asyncio.run(bulk_ingest([{"id": f"v{i}", "values": [0.1]*1536} for i in range(500)]))
```

## Production Notes

**1. Package rename breaks existing installs (Source: official docs)**
The package was renamed from `pinecone-client` to `pinecone` in v5.1.0. Projects importing `pinecone-client` will receive stale versions and miss all API updates post-v4. Remove `pinecone-client` from `requirements.txt` and replace with `pinecone>=5.1.0`. Check `pip list | grep pinecone` to confirm no shadowed install remains.

**2. Namespace deletion is irreversible and not paginated (Source: official docs)**
Calling `index.delete(delete_all=True, namespace="x")` immediately and permanently deletes all vectors in that namespace. There is no soft-delete or recycle bin. In multi-tenant systems, gate this call behind a double-confirmation mechanism and audit log every invocation.

**3. Pod index shard count cannot be changed after creation (Source: official docs)**
Shards determine the maximum vector capacity per index. Once set at creation, shards cannot be increased without creating a new index and migrating data. Size shards for 2× your 12-month projected vector count. Under-sharding is the most common cause of write failures at scale.

**4. Serverless indexes have cold-start latency on first query (Source: community)**
Serverless indexes that receive no traffic for extended periods exhibit elevated first-query latency (100–500ms above steady-state). For latency-sensitive applications, implement a periodic lightweight heartbeat query (empty vector, top_k=1) to keep the endpoint warm.

**5. Metadata filter fields must be indexed selectively for performance (Source: official docs)**
Metadata filtering scans all vectors in the queried namespace by default. For namespaces with millions of vectors, filtering on high-cardinality string fields (e.g., `user_id`) can add 50–200ms of latency. Use numeric fields or low-cardinality enums for filters in the hot path, and structure namespaces to reduce per-namespace scan size.

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `PineconeApiException: 400 - dimension mismatch` on upsert | Embedding model changed or truncation setting differs from index `dimension` | Call `pc.describe_index(name).dimension` before upserting; re-embed or recreate index |
| `PineconeApiException: 429 Too Many Requests` | Exceeded upsert or query rate limit for your plan tier | Implement jittered exponential backoff; reduce concurrent batch fans |
| Query returns results from wrong tenant | Namespace parameter omitted or hardcoded incorrectly | Always derive namespace from authenticated session context; add integration test asserting cross-namespace isolation |
| `describe_index` shows `state: Initializing` and queries fail | Index not yet ready after creation (can take 10–60s) | Poll `pc.describe_index(name).status.ready` with sleep before first operation |
| Write throughput degrades as index fills | Pod capacity approaching limit (>80% fill) | Add shards (requires new index + migration) or switch to serverless for auto-scaling |
| Async upsert silently drops vectors | `asyncio.gather` exceptions swallowed when not checked | Always inspect results from `gather(..., return_exceptions=True)` for `Exception` instances |

## Pre-Deploy Checklist

- [ ] `PINECONE_API_KEY` stored in secrets manager (Vault, AWS Secrets Manager, etc.) — never in source code or `.env` committed to VCS
- [ ] Index `dimension` matches the exact output dimension of the embedding model in use, including any truncation config
- [ ] Namespace strategy documented and enforced at the application layer — all writes and queries include an explicit `namespace` argument
- [ ] Exponential backoff with jitter implemented for all upsert and query paths before going to production traffic
- [ ] Pod shard count sized for 2× projected 12-month vector volume (shards cannot be increased post-creation)
- [ ] `describe_index_stats` integrated into monitoring dashboard with alerts at 70% and 90% fill rate
- [ ] Integration test asserting that a query scoped to `namespace-A` returns zero results present only in `namespace-B`

## Troubleshooting

**Error: `ValueError: dimension mismatch`**
Cause: The vectors being upserted have a different length than the `dimension` specified when the index was created.
Fix: Run `pc.describe_index("your-index").dimension` to confirm expected dims. Re-generate embeddings with the correct model. If the model has changed permanently, create a new index with the correct dimension and re-ingest all data.

**