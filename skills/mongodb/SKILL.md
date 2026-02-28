---
name: mongodb
description: "Provides production-grade MongoDB patterns for Node.js applications using the official mongodb@7 driver. Use when asked to: connect to a MongoDB replica set, configure write concern or read preference, design indexes for high-cardinality queries, tune connection pool settings, enforce schema validation at the database level, handle replica set failover, diagnose connection pool exhaustion, or configure operation timeouts for production workloads."
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: database
  tags: [mongodb, replica-set, indexing, connection-pool, schema-validation, write-concern, node.js]
---

# MongoDB Skill

## Quick Start

```bash
npm install mongodb@7
```

```javascript
// Source: official — https://www.mongodb.com/docs/drivers/node/current/quick-start/
import { MongoClient, ServerApiVersion } from 'mongodb';

const client = new MongoClient('mongodb+srv://user:pass@cluster0.example.mongodb.net/', {
  serverApi: { version: ServerApiVersion.v1, strict: true, deprecationErrors: true },
  maxPoolSize: 10,
});

await client.connect();
const db = client.db('mydb');
const col = db.collection('items');
await col.insertOne({ name: 'widget', price: 9.99, createdAt: new Date() });
const doc = await col.findOne({ name: 'widget' });
console.log(doc);
await client.close();
```

## When to Use

Use this skill when asked to:
- Connect an application to a MongoDB replica set with failover handling
- Configure write concern (`w`, `j`, `wtimeoutMS`) to balance durability and latency
- Design a compound or partial index for high-cardinality query patterns
- Tune `maxPoolSize`, `minPoolSize`, `waitQueueTimeoutMS`, and `connectTimeoutMS`
- Enforce document structure using MongoDB's built-in JSON Schema validation
- Handle or simulate replica set primary stepdown during deploys
- Diagnose and resolve connection pool exhaustion in production
- Set per-operation timeouts using `timeoutMS` (CSOT, driver v7+)

## Core Patterns

### Pattern 1: Replica Set Connection with Failover Tuning (Source: official)

Connect with full replica set URI, tune heartbeat and election timeouts, and set a write concern appropriate for strong durability.

```javascript
// Source: official — https://www.mongodb.com/docs/drivers/node/current/fundamentals/connection/connect/
import { MongoClient } from 'mongodb';

const client = new MongoClient(
  'mongodb://host1:27017,host2:27017,host3:27017/?replicaSet=rs0',
  {
    // Connection pool
    maxPoolSize: 50,
    minPoolSize: 5,
    maxIdleTimeMS: 60_000,

    // Timeout tuning
    connectTimeoutMS: 10_000,   // initial TCP connect
    socketTimeoutMS: 45_000,    // idle socket before close
    serverSelectionTimeoutMS: 15_000, // give up finding a primary

    // Heartbeat — how fast the driver detects a stepdown
    heartbeatFrequencyMS: 2_000,

    // Write concern — majority + journal for strong durability
    writeConcern: { w: 'majority', j: true, wtimeoutMS: 5_000 },

    // Read from nearest replica (analytics) or primary (transactional)
    readPreference: 'primaryPreferred',
  }
);

process.on('SIGINT', async () => { await client.close(); process.exit(0); });
export default client;
```

### Pattern 2: Compound Index Design for High-Cardinality Queries (Source: official)

Follow the ESR (Equality → Sort → Range) rule when ordering compound index keys. This minimises the number of documents the query engine must examine before sort and range filtering.

```javascript
// Source: official — https://www.mongodb.com/docs/manual/core/index-compound/
//
// Query shape we are optimising:
//   db.events.find({ tenantId: 'acme', status: 'open' })
//            .sort({ createdAt: -1 })
//            .limit(25)
//
// ESR ordering: tenantId (equality) → createdAt (sort) → status (range/equality)

const db = client.db('mydb');
const events = db.collection('events');

// Create compound index — ESR order
await events.createIndex(
  { tenantId: 1, createdAt: -1, status: 1 },
  {
    name: 'tenant_created_status',
    background: true,   // non-blocking on older servers; ignored on 4.4+ (rolling build)
  }
);

// Sparse partial index for a low-selectivity flag field
// Only indexes documents where deletedAt exists — saves space for soft-delete patterns
await events.createIndex(
  { deletedAt: 1 },
  {
    name: 'soft_delete_sparse',
    partialFilterExpression: { deletedAt: { $exists: true } },
  }
);

// Verify index is used (run in mongo shell or via explain())
const explanation = await events
  .find({ tenantId: 'acme', status: 'open' })
  .sort({ createdAt: -1 })
  .limit(25)
  .explain('executionStats');

console.log(explanation.queryPlanner.winningPlan);
```

### Pattern 3: Connection Pool Exhaustion Guard + CSOT (Source: official)

Driver v7 introduces Client-Side Operations Timeout (`timeoutMS`) as a single deadline that covers server selection, connection checkout, and execution. Use it to bound every operation so pool exhaustion cannot cause indefinite hangs.

```javascript
// Source: official — https://www.mongodb.com/docs/drivers/node/current/fundamentals/csot/
import { MongoClient, MongoOperationTimeoutError } from 'mongodb';

const client = new MongoClient(uri, {
  maxPoolSize: 50,
  waitQueueTimeoutMS: 5_000,  // max wait for a connection from the pool
  timeoutMS: 8_000,           // CSOT: single deadline for the full operation (driver v7+)
});

const col = client.db('mydb').collection('orders');

async function findOrder(id) {
  try {
    // Per-operation override — shorter deadline for user-facing reads
    return await col.findOne(
      { _id: id },
      { timeoutMS: 3_000 }
    );
  } catch (err) {
    if (err instanceof MongoOperationTimeoutError) {
      // Surface a 503 so load balancers can retry on another instance
      throw Object.assign(new Error('DB timeout — try again'), { status: 503 });
    }
    throw err;
  }
}

// Pool health probe — expose via /healthz
async function isPoolHealthy() {
  try {
    await client.db('admin').command({ ping: 1 }, { timeoutMS: 2_000 });
    return true;
  } catch {
    return false;
  }
}
```

### Pattern 4: Database-Level JSON Schema Validation (Source: official)

Enforce required fields, types, and value ranges directly in MongoDB so invalid documents are rejected before they reach application code.

```javascript
// Source: official — https://www.mongodb.com/docs/manual/core/schema-validation/
const db = client.db('mydb');

await db.createCollection('products', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      title: 'Product schema',
      required: ['sku', 'price', 'stock', 'createdAt'],
      additionalProperties: false,
      properties: {
        _id:       { bsonType: 'objectId' },
        sku:       { bsonType: 'string',  minLength: 3, maxLength: 64 },
        name:      { bsonType: 'string' },
        price:     { bsonType: 'decimal', minimum: 0 },
        stock:     { bsonType: 'int',     minimum: 0 },
        tags:      { bsonType: 'array',   items: { bsonType: 'string' } },
        createdAt: { bsonType: 'date' },
      },
    },
  },
  validationLevel: 'strict',   // enforce on inserts AND updates
  validationAction: 'error',   // reject invalid documents outright (use 'warn' during migration)
});

// To update the validator on an existing collection:
await db.command({
  collMod: 'products',
  validator: { $jsonSchema: { /* updated schema */ } },
  validationLevel: 'moderate', // only validates documents that already matched the old schema
});

// Catch validation errors distinctly
try {
  await db.collection('products').insertOne({ sku: 'X', price: -1, stock: 0, createdAt: new Date() });
} catch (err) {
  if (err.code === 121) {
    console.error('Document failed schema validation:', err.errInfo?.details);
  }
}
```

### Pattern 5: Replica Set Failover Handling + Retryable Writes (Source: official)

Retryable writes (enabled by default in driver v4+) automatically retry once on a network error or primary stepdown. For operations that are not automatically retried (multi-document transactions, bulk writes beyond a single batch), implement explicit retry logic.

```javascript
// Source: official — https://www.mongodb.com/docs/manual/core/retryable-writes/
// # Source: community / # Tested: SharpSkill

import { MongoClient, MongoServerError } from 'mongodb';

// retryWrites: true is the default — shown explicitly for clarity
const client = new MongoClient(uri, { retryWrites: true, retryReads: true });

const RETRYABLE_CODES = new Set([
  91,   // ShutdownInProgress
  189,  // PrimarySteppedDown
  10107, // NotWritablePrimary
  11600, // InterruptedAtShutdown
]);

async function withRetry(fn, { attempts = 3, delayMs = 200 } = {}) {
  for (let i = 0; i < attempts; i++) {
    try {
      return await fn();
    } catch (err) {
      const retryable =
        err instanceof MongoServerError && RETRYABLE_CODES.has(err.code);
      if (!retryable || i === attempts - 1) throw err;
      await new Promise(r => setTimeout(r, delayMs * 2 ** i)); // exponential back-off
    }
  }
}

// Usage — safe for transactions and multi-step writes
const session = client.startSession();
await withRetry(() =>
  session.withTransaction(async () => {
    const orders = client.db('mydb').collection('orders');
    const inventory = client.db('mydb').collection('inventory');
    await orders.insertOne({ item: 'widget', qty: 2 }, { session });
    await inventory.updateOne({ sku: 'widget' }, { $inc: { stock: -2 } }, { session });
  })
);
session.endSession();
```

### Pattern 6: Error Handling for Common Driver Errors (Source: community)

Stack Overflow and GitHub Issues show that developers frequently conflate `MongoNetworkError`, `MongoServerError`, and `MongoBulkWriteError`, causing silent data loss when bulk errors are swallowed.

```javascript
// # Source: community / # Tested: SharpSkill
// Ref: SO "MongoDB bulk write error handling" + driver GitHub Issues #3444

import {
  MongoClient,
  MongoNetworkError,
  MongoServerError,
  MongoBulkWriteError,
  MongoOperationTimeoutError,
} from 'mongodb';

async function safeBulkInsert(collection, docs) {
  try {
    const result = await collection.insertMany(docs, { ordered: false });
    return { inserted: result.insertedCount, errors: [] };
  } catch (err) {
    if (err instanceof MongoBulkWriteError) {
      // Partial success — some docs were inserted
      const inserted = err.result?.insertedCount ?? 0;
      const writeErrors = err.writeErrors ?? [];
      const duplicates = writeErrors.filter(e => e.code === 11000);
      // Log non-duplicate errors; silently skip duplicates (idempotent upsert pattern)
      const hard = writeErrors.filter(e => e.code !== 11000);
      if (hard.length) console.error('Hard bulk write errors:', hard);
      return { inserted, errors: duplicates.map(e => e.err.op) };
    }
    if (err instanceof MongoOperationTimeoutError) {
      throw Object.assign(err, { retryable: true });
    }
    if (err instanceof MongoNetworkError) {
      // Network partition — propagate with retryable flag
      throw Object.assign(err, { retryable: true });
    }
    if (err instanceof MongoServerError && err.code === 121) {
      throw Object.assign(err, { message: `Schema validation failed: ${JSON.stringify(err.errInfo?.details)}` });
    }
    throw err; // unknown — rethrow
  }
}
```

## Production Notes

**1. Pool exhaustion is silent until requests time out**
`maxPoolSize` defaults to 100 but most applications should set it to `(CPU cores × 2) + available_disk_spindles` or tune empirically. Under load, exhausted pools surface as `MongoServerSelectionError: connection pool cleared` not as an obvious "pool full" error. Fix: set `waitQueueTimeoutMS: 5000`, expose `client.topology.s.pool` metrics to your APM, and alert when wait queue depth > 10.
Source: GitHub Issues mongodb/node-mongodb-native #3459

**2. `heartbeatFrequencyMS` controls perceived failover time**
Default is 10 000 ms. During a replica set election (typically 10–30 s), the driver waits one full heartbeat cycle before it detects the new primary. Lowering to 2 000 ms cuts detection latency dramatically at the cost of slightly more network traffic. Combine with `serverSelectionTimeoutMS: 15000` so the driver does not give up before the election completes.
Source: MongoDB official docs — Server Monitoring

**3. Write concern `w: 'majority'` adds latency proportional to replication lag**
On geographically distributed replica sets, cross-region secondary acknowledgement can add hundreds of milliseconds. Use `w: 1` for non-critical writes and `w: 'majority'` only for financial or inventory records. Set `wtimeoutMS` to prevent indefinite blocking if a secondary falls behind.
Source: SO #7216284, Reddit r/mongodb

**4. Compound index field order matters more than cardinality alone**
A common mistake is putting the highest-cardinality field first unconditionally. The ESR rule (Equality → Sort → Range) overrides raw cardinality. An index `{ status: 1, userId: 1 }` for a query that equality-matches `userId` and range-filters `status` will always do a collection scan after the index walk. Validate every new index with `.explain('executionStats')` and confirm `totalDocsExamined` ≈ `nReturned`.
Source: MongoDB official docs — Compound Indexes / ESR Rule

**5. `validationAction: 'error'` will break existing application code during schema migrations**
Switch to `validationAction: 'warn'` and `validationLevel: 'moderate'` when adding new required fields to live collections. This logs violations to `mongod.log` without rejecting writes, giving teams a safe window to migrate existing documents. Flip back to `'error'` only after a verification query confirms zero non-conforming documents.
Source: GitHub Issues mongodb/mongo #SERVER-47784

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|------------|-----|
| `MongoServerSelectionError: connection pool cleared` | Pool exhausted; all connections in use when new operation arrives | Increase `maxPoolSize`, set `waitQueueTimeoutMS`, check for connection leaks (missing `await session.endSession()