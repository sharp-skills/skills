---
name: algolia
description: "Integrate Algolia search into web and mobile apps using the official JavaScript or Python SDK. Use when asked to: add search to an app, index records in Algolia, implement instant search, configure search filters or facets, optimize search relevance, handle Algolia webhooks, or migrate search to Algolia."
license: Apache-2.0
compatibility:
  - node >= 16
  - python >= 3.8
metadata:
  author: SharpSkills
  version: 1.1.0
  category: development
  tags: [algolia, search, full-text-search, javascript, python, indexing, facets]
---

# Algolia

Algolia is a hosted search and discovery API — sub-10ms response times, typo-tolerance, and faceted filtering out of the box. Use for e-commerce search, documentation search, and any app needing fast, relevant results.

## Installation

**JavaScript / Node.js**
```bash
npm install algoliasearch
```

**Python**
```bash
pip install algoliasearch
```

## Quick Start

```javascript
import { algoliasearch } from 'algoliasearch';

const client = algoliasearch('YourAppID', 'YourSearchOnlyAPIKey');

// Search
const { hits } = await client.search({
  requests: [{ indexName: 'products', query: 'iphone' }]
});
console.log(hits);
```

## When to Use
- "Add search to my app" / "integrate Algolia"
- "Index my products / articles / users in Algolia"
- "Implement instant search with filters"
- "Configure faceted search / search filters"
- "Fix Algolia relevance / ranking"
- "Migrate from Elasticsearch to Algolia"

## Core Patterns

### Pattern 1: Index Records (Upsert)

```javascript
import { algoliasearch } from 'algoliasearch';

const client = algoliasearch(process.env.ALGOLIA_APP_ID, process.env.ALGOLIA_ADMIN_KEY);

// saveObjects requires objectID on each record
const records = [
  { objectID: 'prod-1', name: 'iPhone 15', brand: 'Apple', price: 999, category: 'phones' },
  { objectID: 'prod-2', name: 'Galaxy S24', brand: 'Samsung', price: 799, category: 'phones' },
];

const { taskID } = await client.saveObjects({ indexName: 'products', objects: records });

// Wait for indexing to complete (important before searching in tests)
await client.waitForTask({ indexName: 'products', taskID });
console.log('Indexed:', records.length, 'records');
```

### Pattern 2: Search with Filters and Pagination

```javascript
import { algoliasearch } from 'algoliasearch';

const client = algoliasearch(process.env.ALGOLIA_APP_ID, process.env.ALGOLIA_SEARCH_KEY);

const results = await client.search({
  requests: [{
    indexName: 'products',
    query: 'phone',
    filters: 'price < 900 AND category:phones',
    facets: ['brand', 'category'],
    attributesToRetrieve: ['name', 'brand', 'price'],
    hitsPerPage: 20,
    page: 0,
  }]
});

const { hits, nbHits, facets, page, nbPages } = results.results[0];
console.log(`Found ${nbHits} results, page ${page + 1}/${nbPages}`);
```

### Pattern 3: Configure Index Settings

```javascript
import { algoliasearch } from 'algoliasearch';

const client = algoliasearch(process.env.ALGOLIA_APP_ID, process.env.ALGOLIA_ADMIN_KEY);

await client.setSettings({
  indexName: 'products',
  indexSettings: {
    searchableAttributes: ['name', 'brand', 'description'],
    attributesForFaceting: ['filterOnly(price)', 'brand', 'category'],
    customRanking: ['desc(popularity)', 'asc(price)'],
    typoTolerance: true,
    ignorePlurals: true,
    removeStopWords: true,
  }
});
```

### Pattern 4: Batch Delete by Filter

```javascript
import { algoliasearch } from 'algoliasearch';

const client = algoliasearch(process.env.ALGOLIA_APP_ID, process.env.ALGOLIA_ADMIN_KEY);

// Delete all records matching a filter
const { taskID } = await client.deleteBy({
  indexName: 'products',
  deleteByParams: { filters: 'category:discontinued' }
});

await client.waitForTask({ indexName: 'products', taskID });
```

### Pattern 5: Python — Index and Search

```python
from algoliasearch.search.client import SearchClientSync

client = SearchClientSync("YourAppID", "YourAdminKey")

# Index records
client.save_objects(
    index_name="articles",
    objects=[
        {"objectID": "art-1", "title": "Getting Started", "tags": ["beginner"]},
        {"objectID": "art-2", "title": "Advanced Patterns", "tags": ["advanced"]},
    ]
)

# Search
results = client.search(
    search_method_params={
        "requests": [{"indexName": "articles", "query": "getting started"}]
    }
)
print(results.results[0].hits)
```

## Production Notes

1. **Never expose Admin API key in frontend** — use the Search-Only API key (`search-only-*`) in client-side code. Admin key has write access to all indices.
2. **`objectID` is mandatory** — Without it Algolia auto-generates random IDs on each save, causing duplicate records on re-index.
3. **`waitForTask` in scripts, not in request handlers** — Indexing is async. In background scripts call `waitForTask`; in API handlers return immediately and let Algolia sync asynchronously.
4. **Set `attributesForFaceting` before faceting** — Querying facets on an attribute not listed in `attributesForFaceting` returns empty `facets` silently.

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `Invalid Application-ID or API Key` | Wrong key type (e.g. search key used for write) | Use Admin key for indexing, Search-Only key for queries |
| Facets always empty `{}` | Attribute not in `attributesForFaceting` | Add attribute to index settings and re-index |
| Duplicate records on re-index | Missing `objectID` on records | Always set a stable `objectID` from your DB primary key |
| Search returns stale results | Indexing not awaited in tests | Call `waitForTask` after `saveObjects` in test setup |
| `Index does not exist` on first search | Index auto-creates on first write, not on first read | Write at least one record before querying |

## Pre-Deploy Checklist
- [ ] `ALGOLIA_APP_ID` and `ALGOLIA_ADMIN_KEY` in server-side env only
- [ ] `ALGOLIA_SEARCH_KEY` (search-only) used in frontend/client code
- [ ] `objectID` set on all records (matches your DB primary key)
- [ ] `searchableAttributes` configured (not all fields are searchable by default)
- [ ] `attributesForFaceting` set for all filter/facet fields
- [ ] `customRanking` tuned for your use case (popularity, recency, etc.)
- [ ] Index quota checked (free plan: 10k records)

## Resources
- Docs: https://www.algolia.com/doc/
- JS SDK v5: https://github.com/algolia/algoliasearch-client-javascript
- Python SDK: https://github.com/algolia/algoliasearch-client-python
- Dashboard: https://dashboard.algolia.com
