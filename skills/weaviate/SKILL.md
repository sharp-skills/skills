---
name: weaviate
description: "Production-grade vector database operations with Weaviate. Use when asked to: connect to Weaviate with API key authentication, rotate API keys without downtime, import large datasets in batches, handle batch import failures and partial errors, configure shard replication for high availability, recover from node failures, tune memory and resource limits, monitor heap pressure and OOM conditions, set up multi-tenancy, or debug stuck backups and crash-loop restarts."
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: database
  tags: [weaviate, vector-database, semantic-search, rag, embeddings, production, replication]
---

# Weaviate Skill

## Quick Start

```bash
pip install -U weaviate-client
docker run -d -p 8080:8080 -p 50051:50051 \
  -e AUTHENTICATION_APIKEY_ENABLED=true \
  -e AUTHENTICATION_APIKEY_ALLOWED_KEYS=my-secret-key \
  -e AUTHENTICATION_APIKEY_USERS=admin \
  -e AUTHORIZATION_ADMINLIST_ENABLED=true \
  -e AUTHORIZATION_ADMINLIST_USERS=admin \
  cr.weaviate.io/semitechnologies/weaviate:1.36.0
```

```python
import weaviate
from weaviate.auth import AuthApiKey

client = weaviate.connect_to_local(
    auth_credentials=AuthApiKey("my-secret-key"),
    headers={"X-OpenAI-Api-Key": "sk-..."}  # optional: module API keys
)
assert client.is_ready()
client.close()
```

## When to Use

Use this skill when asked to:
- Connect to Weaviate Cloud or self-hosted with API key / OIDC auth
- Rotate API keys or credentials without restarting the cluster
- Import millions of objects in batches with error recovery
- Handle partial batch failures without losing successfully imported objects
- Configure replication factor and consistency levels for HA
- Recover data after a node goes down or a shard becomes unavailable
- Tune `LIMIT_RESOURCES`, heap size, and vector cache under memory pressure
- Debug stuck or never-completing backups
- Set up multi-tenancy with tenant isolation
- Monitor and resolve BM25 / inverted-index tokenization gaps

## Core Patterns

### Pattern 1: Authenticated Client with Key Rotation (Source: official)

API keys are passed at connection time. To rotate a key without downtime, add the new key to `AUTHENTICATION_APIKEY_ALLOWED_KEYS` (comma-separated list), deploy the new key to all consumers, then remove the old key in a follow-up deployment. No restart required when using environment variable hot-reload or Kubernetes secret rollout.

```python
import weaviate
from weaviate.auth import AuthApiKey

# Primary connection — always use context manager to guarantee close()
with weaviate.connect_to_weaviate_cloud(
    cluster_url="https://<cluster>.weaviate.network",
    auth_credentials=AuthApiKey("NEW_KEY"),
    # Pass external module keys as headers, not embedded in config
    headers={
        "X-OpenAI-Api-Key": "sk-...",
        "X-Cohere-Api-Key": "...",
    },
    additional_config=weaviate.config.AdditionalConfig(
        timeout=weaviate.config.Timeout(init=30, query=60, insert=120)
    ),
) as client:
    assert client.is_ready(), "Weaviate not ready — check cluster URL and key"
    print(client.get_meta())
```

```yaml
# docker-compose: zero-downtime key rotation
environment:
  AUTHENTICATION_APIKEY_ENABLED: "true"
  # Add new key alongside old key; remove old key after clients migrate
  AUTHENTICATION_APIKEY_ALLOWED_KEYS: "old-key-abc,new-key-xyz"
  AUTHENTICATION_APIKEY_USERS: "svc-account,svc-account"
```

### Pattern 2: Resilient Batch Import with Partial-Failure Handling (Source: official)

`insert_many()` returns a `BatchObjectReturn` object. Errors are per-object — a partial failure does NOT raise an exception by default. You must inspect `.has_errors` and `.errors` to detect and retry failed objects.

```python
from weaviate.classes.config import Configure, DataType, Property
from weaviate.util import generate_uuid5
import time

def batch_import_with_retry(client, collection_name: str, objects: list, max_retries: int = 3):
    """
    Import objects in chunks, retrying only failed objects.
    Returns (success_count, final_failures).
    """
    collection = client.collections.get(collection_name)
    CHUNK_SIZE = 200  # keep well under default 100 MB gRPC message limit
    success_count = 0
    final_failures = []

    for i in range(0, len(objects), CHUNK_SIZE):
        chunk = objects[i : i + CHUNK_SIZE]
        attempts = 0
        pending = chunk

        while attempts < max_retries and pending:
            result = collection.data.insert_many(pending)
            success_count += len(pending) - len(result.errors)

            if not result.has_errors:
                break

            # Extract only the failed objects for retry
            failed_indices = list(result.errors.keys())
            print(f"Chunk {i//CHUNK_SIZE}: {len(failed_indices)} failures on attempt {attempts+1}")
            for idx, err in result.errors.items():
                print(f"  Object index {idx}: {err.message}")

            pending = [pending[idx] for idx in failed_indices]
            attempts += 1
            time.sleep(2 ** attempts)  # exponential back-off

        if pending and attempts == max_retries:
            final_failures.extend(pending)

    return success_count, final_failures


# Usage
with weaviate.connect_to_local(auth_credentials=AuthApiKey("my-secret-key")) as client:
    objects = [
        weaviate.classes.data.DataObject(
            properties={"content": f"Document {n}"},
            uuid=generate_uuid5(f"doc-{n}"),
        )
        for n in range(10_000)
    ]
    ok, failed = batch_import_with_retry(client, "Article", objects)
    print(f"Imported {ok}, failed permanently: {len(failed)}")
```

### Pattern 3: Replication and Node-Failure Recovery (Source: official)

Set `replication_config` at collection-creation time. You cannot change the replication factor on an existing collection without re-creating it. Use `ConsistencyLevel.QUORUM` for writes and reads in HA clusters.

```python
from weaviate.classes.config import Configure, ReplicationConfig
from weaviate.classes.query import QueryReference
import weaviate.classes as wvc

with weaviate.connect_to_local() as client:
    # Create collection with replication factor = 3 (requires 3-node cluster)
    client.collections.create(
        name="Article",
        replication_config=wvc.config.Configure.replication(factor=3),
        properties=[
            wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
        ],
        vector_config=Configure.Vectors.text2vec_model2vec(),
    )

    articles = client.collections.get("Article")

    # Write with QUORUM consistency — survives single-node failure
    articles.data.insert(
        properties={"content": "HA write example"},
        consistency_level=wvc.data.ConsistencyLevel.QUORUM,
    )

    # Read repair: after node recovery, trigger repair via REST
    # GET /v1/objects/{className}/{id}?consistency_level=ALL
    # Weaviate will reconcile divergent replicas automatically
```

```bash
# Check node/shard status after a failure
curl -s http://localhost:8080/v1/nodes | jq '.nodes[] | {name, status, shards}'

# Force re-index a specific shard (Weaviate 1.18+)
curl -X POST http://localhost:8080/v1/schema/{ClassName}/shards/{shardName} \
  -H "Authorization: Bearer my-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"status":"READY"}'
```

### Pattern 4: Memory Pressure and Resource Limit Tuning (Source: official)

Weaviate's HNSW vector index holds the entire graph in memory. Under pressure the process will OOM-kill before any graceful degradation. Set explicit limits and monitor heap via the `/v1/nodes` endpoint.

```yaml
# docker-compose: production resource configuration
services:
  weaviate:
    image: cr.weaviate.io/semitechnologies/weaviate:1.36.0
    environment:
      # Hard cap on Go runtime heap (bytes); set to ~70% of container memory
      LIMIT_RESOURCES: "true"
      GOMEMLIMIT: "6GiB"          # Go 1.19+ soft memory limit
      GOMAXPROCS: "4"              # match CPU quota
      # Vector cache: objects to keep hot; 1 object ≈ dim*4 bytes
      # e.g. 1M objects × 1536 dims × 4 bytes ≈ 6 GB
      QUERY_MAXIMUM_RESULTS: "10000"
      # Persistence: flush memtable before it grows too large
      PERSISTENCE_LSM_ACCESS_STRATEGY: "mmap"
      PERSISTENCE_DATA_PATH: "/var/lib/weaviate"
    mem_limit: "8g"
    mem_reservation: "4g"
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: "4"
```

```python
# Monitor heap and shard health programmatically
import requests

def check_memory_pressure(host="http://localhost:8080", api_key="my-secret-key"):
    resp = requests.get(
        f"{host}/v1/nodes",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    resp.raise_for_status()
    for node in resp.json()["nodes"]:
        stats = node.get("stats", {})
        print(f"Node {node['name']}: status={node['status']}, "
              f"objectCount={stats.get('objectCount', 'N/A')}, "
              f"shardCount={stats.get('shardCount', 'N/A')}")
```

### Pattern 5: Stuck Backup Recovery (Source: community)

Backups that remain in `STARTED` state indefinitely indicate a coordinating node crash mid-operation. The backup lock is stored in the data volume. Manual intervention is required.

```bash
# 1. Check current backup status
curl -s http://localhost:8080/v1/backups/filesystem \
  -H "Authorization: Bearer my-secret-key" | jq '.'

# 2. If status is STARTED and node is healthy, cancel and retry
curl -X DELETE http://localhost:8080/v1/backups/filesystem/my-backup \
  -H "Authorization: Bearer my-secret-key"

# 3. If DELETE is also stuck, find and remove the lock file from the volume
#    Location: <PERSISTENCE_DATA_PATH>/backups/<backup-id>/.backup.lock
docker exec weaviate find /var/lib/weaviate/backups -name "*.lock" -delete

# 4. Restart pod/container — Weaviate will mark abandoned backup as FAILED on startup
docker restart weaviate

# 5. Retry backup with explicit timeout
curl -X POST http://localhost:8080/v1/backups/filesystem \
  -H "Authorization: Bearer my-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my-backup-v2",
    "include": ["Article"],
    "config": {"cpuPercentage": 40}
  }'
```

### Pattern 6: BM25 / Inverted Index Tokenization Fix (Source: community)

BM25 returning zero results is almost always a tokenizer mismatch between index-time and query-time, or a missing `invertedIndexConfig`. Properties without explicit tokenization default to `word` for TEXT but `field` for others.

```python
from weaviate.classes.config import Configure, Property, DataType, Tokenization

with weaviate.connect_to_local() as client:
    client.collections.create(
        name="LegalArticle",
        properties=[
            Property(
                name="body",
                data_type=DataType.TEXT,
                # Must match the tokenizer used at query time
                tokenization=Tokenization.LOWERCASE,  # or WORD, WHITESPACE, FIELD
                index_searchable=True,   # enables BM25 on this property
                index_filterable=True,
            ),
        ],
        inverted_index_config=Configure.inverted_index(
            bm25_b=0.75,
            bm25_k1=1.2,
            stopwords_preset="none",   # important for non-English corpora
        ),
    )

    # BM25 query — property list must match indexed properties
    collection = client.collections.get("LegalArticle")
    results = collection.query.bm25(
        query="contrat obligations",
        query_properties=["body"],  # explicit — avoids silent property mismatch
        limit=10,
    )
    for obj in results.objects:
        print(obj.properties)
```

## Production Notes

**1. Backup deadlock on single-node clusters**
Weaviate acquires an exclusive lock before snapshotting each shard. If the process crashes after acquiring the lock but before releasing it, the backup remains in `STARTED` forever and subsequent backup calls return 409 Conflict. Manual lock-file removal from the persistence volume is required.
Source: GitHub Issues (weaviate/weaviate backup-stuck thread, 27 comments)

**2. Slice bounds panic on corrupt LSM segments**
Upgrading Weaviate (especially across minor versions like 1.11→1.12) can leave partially-written SSTable/LSM segments that cause `panic: runtime error: slice bounds out of range` on startup. The fix is to identify the corrupt segment file from the log path, remove it, and allow Weaviate to rebuild from replicas or re-import. Always snapshot volumes before version upgrades.
Source: GitHub Issues (weaviate/weaviate #3412, 22 comments)

**3. OOM kills under large geo/array imports**
Importing objects with `geoCoordinates` or large array properties at high concurrency triggers `makeslice: len out of range` panics. This is caused by integer overflow in slice pre-allocation under concurrent writes. Mitigation: reduce batch concurrency, set `GOMAXPROCS` explicitly, and upgrade to ≥1.14 where this is patched.
Source: GitHub Issues (weaviate/weaviate geo-crash thread, 17 comments)

**4. BM25 silent zero-result on non-English stopwords**
The default stopwords preset is `en`. Setting `stopwords_preset: "en"` on French, German, or other corpora silently discards common query terms as stopwords, returning zero results. Always set `"none"` and supply a custom list when indexing non-English content.
Source: GitHub Issues (weaviate/weaviate BM25 thread, 27 comments)

**5. AWS Bedrock embedding module env-var sensitivity**
The `text2vec-aws` module requires `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION` set at container start — not passed as headers. Missing or incorrectly named variables cause silent vectorization failures (objects import with zero vectors) rather than an error response. Confirm module is loaded via `GET /v1/meta` before importing.
Source: GitHub Issues (weaviate/weaviate AWS Bedrock thread, 13 comments)

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| Backup stuck in `STARTED` forever | Lock file not released after coordinating node crash | Remove `.backup.lock` from persistence volume, restart node |
| `panic: slice bounds out