---
name: elasticsearch
description: "Connects to Elasticsearch clusters and performs full-text search, document indexing, querying, and cluster management. Use when asked to: search documents in Elasticsearch, index or bulk-insert records, build bool/must/should queries, configure index mappings and settings, handle cluster health and shard issues, delete or update documents by query, list all indices on a cluster, fix read-only index errors from disk watermark exceeded."
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: database
  tags: [elasticsearch, search, indexing, full-text-search, python, rest-api]
trace_id: a56db427f6f6
generated_at: '2026-02-28T22:43:24'
generator: sharpskill-v1.0 (legacy)
---

# Elasticsearch Skill

## Quick Start

```bash
pip install elasticsearch
```

```python
from elasticsearch import Elasticsearch

# Connect to local or cloud cluster
es = Elasticsearch("http://localhost:9200")
# For Elastic Cloud:
# es = Elasticsearch("https://<id>.es.io:9243", api_key="<key>")

# Verify connection
info = es.info()
print(info["version"]["number"])

# Index a document
es.index(index="products", id="1", document={"name": "Widget", "price": 9.99})

# Search
resp = es.search(index="products", query={"match": {"name": "widget"}})
print(resp["hits"]["hits"])
```

## When to Use

Use this skill when asked to:
- Search or query documents in an Elasticsearch index
- Index, bulk-insert, or upsert documents into Elasticsearch
- Build bool queries with must, should, must_not, and filter clauses
- Configure index mappings, settings, or analyzers
- Check cluster health, shard allocation, or node status
- List, create, or delete Elasticsearch indices
- Update or delete documents by query
- Fix read-only index errors or disk watermark issues
- Paginate large result sets with search_after or scroll API
- Aggregate data with terms, range, or date_histogram aggregations

## Core Patterns

### Pattern 1: Index Mappings and Settings (Source: official)

Define field types explicitly before indexing to control how text is analyzed and stored.

```python
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

mapping = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1
    },
    "mappings": {
        "properties": {
            "title":       {"type": "text"},
            "price":       {"type": "float"},
            "category":    {"type": "keyword"},  # exact match, no analysis
            "created_at":  {"type": "date"},
            "description": {"type": "text", "analyzer": "english"}
        }
    }
}

es.indices.create(index="products", body=mapping, ignore=400)  # 400 = already exists
```

### Pattern 2: Bool Query — Combining must, should, filter (Source: official)

`must` = AND (scores), `filter` = AND (no scoring, cached), `should` = OR, `must_not` = NOT.

```python
resp = es.search(
    index="products",
    query={
        "bool": {
            "must": [
                {"match": {"title": "wireless headphones"}}
            ],
            "filter": [
                {"term":  {"category": "electronics"}},
                {"range": {"price": {"gte": 20, "lte": 200}}}
            ],
            "should": [
                {"term": {"in_stock": True}}
            ],
            "must_not": [
                {"term": {"discontinued": True}}
            ]
        }
    },
    size=10
)

for hit in resp["hits"]["hits"]:
    print(hit["_score"], hit["_source"])
```

### Pattern 3: Bulk Indexing (Source: official)

Use the `helpers.bulk` utility for high-throughput ingestion — single-doc `index()` in a loop is ~10× slower.

```python
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

es = Elasticsearch("http://localhost:9200")

def generate_docs(records):
    for rec in records:
        yield {
            "_index": "products",
            "_id":    rec["id"],
            "_source": rec
        }

records = [
    {"id": "1", "name": "Widget A", "price": 9.99,  "category": "tools"},
    {"id": "2", "name": "Widget B", "price": 14.99, "category": "tools"},
]

success, failed = bulk(es, generate_docs(records), raise_on_error=False)
print(f"Indexed: {success}, Failed: {len(failed)}")
```

### Pattern 4: Return Specific Fields Only (Source: official)

Avoid fetching large `_source` blobs — use `_source_includes` or `fields`.

```python
resp = es.search(
    index="products",
    query={"match_all": {}},
    source_includes=["name", "price"],   # only these fields returned
    size=20
)
# Or use stored fields:
# fields=["name", "price"], _source=False
```

### Pattern 5: Aggregations (Source: official)

```python
resp = es.search(
    index="products",
    size=0,  # no hits, only aggregations
    aggs={
        "by_category": {
            "terms": {"field": "category", "size": 10}
        },
        "avg_price": {
            "avg": {"field": "price"}
        },
        "price_histogram": {
            "histogram": {"field": "price", "interval": 50}
        }
    }
)

for bucket in resp["aggregations"]["by_category"]["buckets"]:
    print(bucket["key"], bucket["doc_count"])

print("Avg price:", resp["aggregations"]["avg_price"]["value"])
```

### Pattern 6: Paginate with search_after (Source: official)

Prefer `search_after` over `from/size` beyond 10 000 hits; avoid scroll for real-time pagination.

```python
# First page — requires a sort with a unique tiebreaker
resp = es.search(
    index="products",
    sort=[{"price": "asc"}, {"_id": "asc"}],
    size=100,
    query={"match_all": {}}
)

hits = resp["hits"]["hits"]
last_sort = hits[-1]["sort"] if hits else None

# Subsequent pages
while last_sort:
    resp = es.search(
        index="products",
        sort=[{"price": "asc"}, {"_id": "asc"}],
        size=100,
        search_after=last_sort,
        query={"match_all": {}}
    )
    hits = resp["hits"]["hits"]
    if not hits:
        break
    last_sort = hits[-1]["sort"]
    for h in hits:
        print(h["_source"])
```

### Pattern 7: Error Handling — Read-Only Index Fix (Source: community)

The most common production emergency: disk hits 95 % watermark, Elasticsearch locks all indices read-only.

```python
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

# Step 1 — lower watermark thresholds (or free disk space first)
es.cluster.put_settings(body={
    "transient": {
        "cluster.routing.allocation.disk.watermark.low":  "90%",
        "cluster.routing.allocation.disk.watermark.high": "95%",
        "cluster.routing.allocation.disk.watermark.flood_stage": "97%"
    }
})

# Step 2 — clear the read-only block on affected index
es.indices.put_settings(
    index="products",  # or "*" for all indices
    body={"index.blocks.read_only_allow_delete": None}
)

# Step 3 — verify
health = es.cluster.health()
print(health["status"])  # should return "green" or "yellow"
```

### Pattern 8: Delete by Query (Source: official)

```python
resp = es.delete_by_query(
    index="products",
    query={
        "range": {
            "created_at": {"lt": "2022-01-01"}
        }
    },
    conflicts="proceed"  # skip version conflicts instead of aborting
)
print(f"Deleted: {resp['deleted']}, Failures: {resp['failures']}")
```

### Pattern 9: List All Indices (Source: community)

```python
# Returns a list of dicts with health, status, index name, doc count, size
indices = es.cat.indices(v=True, format="json", s="index")
for idx in indices:
    print(idx["index"], idx["docs.count"], idx["store.size"])

# Filter by pattern
logs = es.cat.indices(index="logs-*", v=True, format="json")
```

## Production Notes

1. **Mapping explosion on dynamic fields** — By default, Elasticsearch auto-creates mappings for every new field. A single document with 1 000 unknown keys can flood the cluster mapping, causing heap pressure and slow indexing. Fix: set `"dynamic": "strict"` or `"dynamic": false` in your index mapping and explicitly declare all expected fields.
   Source: SO (Solr vs Elasticsearch thread), Elastic docs

2. **`from + size` hard limit of 10 000 hits** — Queries like `from: 9900, size: 200` silently fail with a `query_phase_execution_exception` when the total exceeds `index.max_result_window` (default 10 000). Fix: use `search_after` with a point-in-time (PIT) for deep pagination, or raise `max_result_window` cautiously only for small indices.
   Source: SO (637 votes — "return all records")

3. **Read-only flood-stage block wipes write access cluster-wide** — When any data node's disk exceeds 95 % (flood_stage watermark), Elasticsearch sets `index.blocks.read_only_allow_delete: true` on ALL indices, not just the full node's indices. Applications start throwing `cluster_block_exception [FORBIDDEN/12]`. Fix: free disk → adjust watermarks → clear block (see Pattern 7).
   Source: SO (343 votes)

4. **Deprecated `elasticsearch` npm package (v16.x)** — The npm package `elasticsearch@16.7.3` is no longer maintained. Any new Node.js project must use `@elastic/elasticsearch` instead. The old client does not support Elasticsearch 7.x+ APIs and will produce silent data errors or connection failures.
   Source: Official npm README

5. **Shard over-allocation degrades performance** — A common mistake is creating too many shards (e.g., one index per day with default 5 shards for 30 days = 150 shards). Each shard is a Lucene instance consuming heap. Elastic recommends ≤ 20 shards per GB of heap. Fix: use index rollover with ILM, target 10–50 GB per shard, and enable `_shrink` for historical indices.
   Source: SO (479 votes — shards and replicas)

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `cluster_block_exception [FORBIDDEN/12/index read-only]` | Disk exceeded 95% flood watermark, index auto-locked | Free disk, adjust watermark settings, clear `index.blocks.read_only_allow_delete` |
| `Result window is too large` / `query_phase_execution_exception` | `from + size > 10 000` (max_result_window limit) | Switch to `search_after` + PIT or raise `index.max_result_window` |
| Bool query returns unexpected documents | Confusing `must` (scored AND) with `filter` (cached AND), or `should` without `minimum_should_match` | Use `filter` for exact matches, set `minimum_should_match: 1` on `should`-only bool queries |
| Indexing suddenly slow after schema change | Dynamic mapping explosion from uncontrolled field creation | Set `dynamic: strict`, define explicit mappings, reindex if needed |
| Connection pool exhaustion in production | Default transport uses too few connections for high-concurrency workloads; old npm client incompatible | Use `@elastic/elasticsearch` (Node.js) or tune `maxsize` in Python `urllib3` connection pool |
| Yellow/red cluster status after node restart | Unassigned replica shards waiting for the node; or shard limit hit | Check `_cluster/allocation/explain`, increase `cluster.max_shards_per_node`, or reduce replica count |

## Pre-Deploy Checklist

- [ ] Explicit index mappings defined with correct field types (`keyword` vs `text`, date formats); `dynamic` set to `strict` or `false`
- [ ] Number of shards chosen based on expected data volume (target 10–50 GB per shard); replicas ≥ 1 for production HA
- [ ] Disk watermark thresholds verified; monitoring/alerting on disk usage above 80 %
- [ ] Authentication configured (API key or username/password); Elasticsearch not exposed publicly without TLS
- [ ] Bulk indexing used for any ingestion > 100 documents; single-doc loops replaced with `helpers.bulk`
- [ ] Index Lifecycle Management (ILM) policy configured for time-series or log indices to control shard growth
- [ ] Client version matches cluster version (e.g., Python client 8.x ↔ ES 8.x); deprecated `elasticsearch` npm package replaced with `@elastic/elasticsearch`

## Troubleshooting

**Error: `cluster_block_exception [FORBIDDEN/12/index read-only / allow delete (api)]`**
Cause: Elasticsearch automatically sets indices to read-only when the disk flood-stage watermark (default 95%) is exceeded.
Fix:
1. Free up disk space or add storage to the data node.
2. Adjust watermarks via `cluster.put_settings` (transient).
3. Clear the block: `es.indices.put_settings(index="*", body={"index.blocks.read_only_allow_delete": None})`.

**Error: `Result window is too large, from + size must be less than or equal to: [10000]`**
Cause: Deep pagination exceeded `index.max_result_window`.
Fix: Use `search_after` with a unique sort field and `_id` tiebreaker. For exports, use the scroll API (not recommended for live user-facing pagination).

**Error: `ConnectionError` / `ConnectionTimeout` on startup**
Cause: Elasticsearch not reachable at the configured host/port, or TLS mismatch.
Fix: Verify the cluster is running (`curl http://localhost:9200`), check `scheme`, `host`, `port` in client config, and ensure certificates are trusted if using HTTPS.

**Symptom: Bool query `should` clauses ignored**
Cause: When `must` or `filter` is also present, `should` becomes optional (zero `minimum_should_match`).
Fix: Add `"minimum_should_match": 1` to the `bool` query to enforce at least one `should` clause matches.

## Resources

- Docs: https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/index.html
- Python Client GitHub: https://github.com/elastic/elasticsearch-py
- New JS Client GitHub: https://github.com/elastic/elasticsearch-js
- Elasticsearch REST API Reference: https://www.elastic.co/guide/en/elasticsearch/reference/current/rest-apis.html
- Migration Guide (JS old → new client): https://www.elastic.co/guide/en/elasticsearch/client/javascript-api/current/breaking-changes.html