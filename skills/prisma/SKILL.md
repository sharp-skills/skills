---
name: prisma-production-depth
description: "Production-depth Prisma ORM patterns for Node.js/TypeScript backends. Use when asked to: configure connection pool sizing, handle pool exhaustion errors, set query timeouts, cancel slow queries, detect and fix N+1 query problems, implement Prisma Client singleton for serverless/Lambda, tune Prisma for high-concurrency APIs, or debug 'Too many connections' and timeout errors in production Prisma apps."
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: database
  tags: [prisma, orm, postgresql, connection-pool, serverless, n-plus-one, typescript, performance]
trace_id: 199064ad6672
generated_at: '2026-02-28T22:43:30'
generator: sharpskill-v1.0 (legacy)
---

# Prisma Production Depth Skill

## Quick Start

```bash
npm install prisma @prisma/client
npx prisma init
npx prisma migrate dev --name init
```

```typescript
// lib/prisma.ts — singleton for long-running servers
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient({
  log: ['error', 'warn'],
})

export default prisma
```

## When to Use

Use this skill when asked to:
- Configure or tune Prisma connection pool size for production
- Debug "Too many connections" or pool exhaustion errors
- Set query timeouts or cancel long-running Prisma queries
- Detect, diagnose, or fix N+1 query problems in Prisma
- Implement Prisma Client singleton pattern for serverless (Lambda, Vercel, Cloudflare Workers)
- Optimize Prisma performance for high-concurrency REST or GraphQL APIs
- Handle `PrismaClientKnownRequestError` and `PrismaClientInitializationError` in production
- Prevent database connection leaks in Next.js or serverless environments
- Configure Prisma logging and query metrics for observability
- Batch or paginate large Prisma result sets efficiently

## Core Patterns

### Pattern 1: Connection Pool Sizing (Source: official)

Prisma uses a built-in connection pool managed by the query engine. The default pool size is `num_physical_cpus * 2 + 1`. For production, set it explicitly via the `connection_limit` URL parameter or `datasource` configuration.

```typescript
// prisma.config.ts — explicit pool sizing
import { defineConfig, env } from 'prisma/config'

export default defineConfig({
  datasource: {
    // connection_limit sets pool max; pool_timeout sets wait time (seconds)
    // connect_timeout sets initial connection timeout (seconds)
    url: `${env('DATABASE_URL')}?connection_limit=10&pool_timeout=15&connect_timeout=10`,
  },
})
```

```typescript
// Alternative: PrismaClient datasource override at runtime
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient({
  datasources: {
    db: {
      url: `${process.env.DATABASE_URL}?connection_limit=10&pool_timeout=15`,
    },
  },
})
```

**Pool sizing formula for production:**
- Long-running server (Express, Fastify): `connection_limit = (DB max_connections / num_app_instances) - headroom`
- Serverless: `connection_limit=1` per function instance; use PgBouncer or Prisma Accelerate for pooling

### Pattern 2: Prisma Client Singleton for Serverless (Source: official)

Each serverless invocation risks creating a new `PrismaClient` instance, exhausting database connections rapidly. The global singleton pattern reuses the client across hot reloads in development and across invocations in the same container in production.

```typescript
// lib/prisma.ts — production singleton (Next.js / Vercel / Lambda)
import { PrismaClient } from '@prisma/client'

declare global {
  // Prevent multiple instances in development hot reload
  // eslint-disable-next-line no-var
  var __prisma: PrismaClient | undefined
}

function createPrismaClient(): PrismaClient {
  return new PrismaClient({
    log:
      process.env.NODE_ENV === 'development'
        ? ['query', 'warn', 'error']
        : ['error'],
    datasources: {
      db: {
        // connection_limit=1 is critical for serverless to avoid pool exhaustion
        url: `${process.env.DATABASE_URL}?connection_limit=1&pool_timeout=10`,
      },
    },
  })
}

// In production: no global caching needed — container reuse handles it
// In development: global prevents hot-reload from spawning new clients
const prisma: PrismaClient =
  process.env.NODE_ENV === 'production'
    ? createPrismaClient()
    : (globalThis.__prisma ?? (globalThis.__prisma = createPrismaClient()))

export default prisma
```

```typescript
// Next.js API route usage — never instantiate PrismaClient inline
// ❌ WRONG — creates new client on every request
export async function GET() {
  const client = new PrismaClient() // leaks connections
  return Response.json(await client.user.findMany())
}

// ✅ CORRECT — reuse singleton
import prisma from '@/lib/prisma'
export async function GET() {
  return Response.json(await prisma.user.findMany())
}
```

### Pattern 3: Query Timeout Configuration and Cancellation (Source: official)

Prisma does not have a built-in global query timeout in the client config, but timeouts are controllable at the transaction level and via database-level statement timeouts.

```typescript
// Method 1: Transaction-level timeout (Prisma 4.7+)
// `timeout` aborts the transaction if it runs longer than N milliseconds
const result = await prisma.$transaction(
  async (tx) => {
    const user = await tx.user.findUniqueOrThrow({ where: { id: 1 } })
    const posts = await tx.post.findMany({ where: { authorId: user.id } })
    return { user, posts }
  },
  {
    maxWait: 5000,  // ms to wait for a connection from pool before error
    timeout: 10000, // ms before the transaction itself is cancelled
  }
)
```

```typescript
// Method 2: PostgreSQL statement_timeout via $executeRaw (per-session)
// Apply before queries that must not run long
async function withStatementTimeout<T>(
  prisma: PrismaClient,
  timeoutMs: number,
  fn: () => Promise<T>
): Promise<T> {
  await prisma.$executeRawUnsafe(`SET LOCAL statement_timeout = ${timeoutMs}`)
  return fn()
}

// Method 3: AbortController wrapper for external timeout control
async function queryWithTimeout<T>(
  queryFn: () => Promise<T>,
  timeoutMs: number
): Promise<T> {
  const timeout = new Promise<never>((_, reject) =>
    setTimeout(() => reject(new Error(`Query timed out after ${timeoutMs}ms`)), timeoutMs)
  )
  return Promise.race([queryFn(), timeout])
}

// Usage
const users = await queryWithTimeout(
  () => prisma.user.findMany({ where: { active: true } }),
  5000
)
```

### Pattern 4: N+1 Query Detection and Prevention (Source: official)

N+1 occurs when fetching a list then querying relations in a loop. Prisma solves this with `include`, `select`, and the dataloader-based `findMany` batching.

```typescript
// ❌ N+1 PATTERN — 1 query for posts + N queries for authors
const posts = await prisma.post.findMany()
for (const post of posts) {
  // Each iteration fires a separate SELECT — N+1 problem
  const author = await prisma.user.findUnique({ where: { id: post.authorId } })
  console.log(post.title, author?.name)
}

// ✅ FIX 1: include — JOIN in a single query
const postsWithAuthors = await prisma.post.findMany({
  include: {
    author: {
      select: { id: true, name: true, email: true }, // select only needed fields
    },
  },
})

// ✅ FIX 2: select with nested — avoids overfetching
const postsSlim = await prisma.post.findMany({
  select: {
    id: true,
    title: true,
    author: {
      select: { name: true },
    },
  },
})

// ✅ FIX 3: $transaction batching for independent queries
const [users, posts, tags] = await prisma.$transaction([
  prisma.user.findMany(),
  prisma.post.findMany({ where: { published: true } }),
  prisma.tag.findMany(),
])
```

```typescript
// Detecting N+1 with Prisma query logging
// Enable 'query' log level and watch for repeated queries with different IDs
const prisma = new PrismaClient({
  log: [
    { level: 'query', emit: 'event' },
    { level: 'warn', emit: 'stdout' },
  ],
})

// Count distinct query patterns to surface N+1 in development
const queryCounts = new Map<string, number>()
prisma.$on('query', (e) => {
  // Normalize query by stripping literal values — detects repeated structure
  const normalized = e.query.replace(/\d+/g, '?').replace(/'[^']*'/g, '?')
  queryCounts.set(normalized, (queryCounts.get(normalized) ?? 0) + 1)
  if ((queryCounts.get(normalized) ?? 0) > 5) {
    console.warn(`[N+1 CANDIDATE] Query fired >5 times:\n${e.query}`)
  }
})
```

### Pattern 5: Pool Exhaustion Handling (Source: official + community)

Pool exhaustion manifests as `PrismaClientKnownRequestError` with code `P2024` ("Timed out fetching a new connection from the connection pool").

```typescript
import { PrismaClient, Prisma } from '@prisma/client'

// Source: community / Tested: SharpSkill
async function resilientQuery<T>(
  fn: () => Promise<T>,
  retries = 3,
  delayMs = 500
): Promise<T> {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      return await fn()
    } catch (err) {
      if (
        err instanceof Prisma.PrismaClientKnownRequestError &&
        err.code === 'P2024' &&
        attempt < retries
      ) {
        // P2024: pool_timeout exceeded — back off and retry
        console.warn(`[Prisma] Pool exhausted, retry ${attempt}/${retries}`)
        await new Promise((r) => setTimeout(r, delayMs * attempt))
        continue
      }
      throw err // non-retriable or retries exhausted
    }
  }
  throw new Error('Unreachable')
}

// Usage
const user = await resilientQuery(() =>
  prisma.user.findUniqueOrThrow({ where: { id: userId } })
)
```

```typescript
// Graceful shutdown — always disconnect to release pool connections
// Critical for Lambda and containerized apps on SIGTERM
process.on('SIGTERM', async () => {
  console.log('SIGTERM received — disconnecting Prisma')
  await prisma.$disconnect()
  process.exit(0)
})

process.on('SIGINT', async () => {
  await prisma.$disconnect()
  process.exit(0)
})
```

### Pattern 6: Error Handling by Error Code (Source: official)

```typescript
import { Prisma } from '@prisma/client'

async function createUser(email: string, name: string) {
  try {
    return await prisma.user.create({ data: { email, name } })
  } catch (err) {
    if (err instanceof Prisma.PrismaClientKnownRequestError) {
      switch (err.code) {
        case 'P2002':
          // Unique constraint violation — field in err.meta.target
          throw new Error(`Duplicate value for field: ${(err.meta?.target as string[])?.join(', ')}`)
        case 'P2025':
          // Record not found (used in update/delete)
          throw new Error('Record not found')
        case 'P2003':
          // Foreign key constraint failed
          throw new Error(`Foreign key violation: ${err.meta?.field_name}`)
        case 'P2024':
          // Connection pool timeout
          throw new Error('Database overloaded — try again shortly')
        default:
          throw new Error(`Database error ${err.code}: ${err.message}`)
      }
    }
    if (err instanceof Prisma.PrismaClientInitializationError) {
      // Binary not found, DB unreachable, or schema mismatch
      throw new Error(`Prisma init failed: ${err.message}`)
    }
    if (err instanceof Prisma.PrismaClientValidationError) {
      // Invalid query shape — type error in query arguments
      throw new Error(`Invalid query: ${err.message}`)
    }
    throw err
  }
}
```

## Production Notes

**1. `connection_limit=1` is mandatory for serverless — not optional**
In Lambda or Vercel Functions, each warm container holds its own pool. Without `connection_limit=1`, 100 concurrent Lambda instances each open the default pool size (~5), creating 500 connections on a database with `max_connections=100`. Use Prisma Accelerate or PgBouncer in transaction mode as a pooling proxy in front of the database.
Source: Prisma docs (Connection management in serverless environments)

**2. Hot reload in Next.js dev mode creates hundreds of PrismaClient instances**
`next dev` uses module re-evaluation on file save. Without the `globalThis.__prisma` guard, each save spawns a new `PrismaClient` and its associated pool, exhausting `max_connections` within minutes. The global singleton pattern fully prevents this.
Source: SO (multiple threads) / Prisma GitHub Issues

**3. `include` depth beyond 3 levels degrades query planner performance**
Deeply nested `include` chains generate complex JOINs that can cause PostgreSQL query planner regressions. For deep nesting (e.g., `post → comments → author → posts`), break into separate queries and join in application code, or use `$queryRaw` with a hand-written SQL query.
Source: Prisma GitHub Discussions

**4. `findMany` without `take` is a production footgun**
Unbounded `findMany` on large tables fetches all rows into memory. Always apply `take` + `skip` or cursor-based pagination using `cursor` + `take` for stable, index-friendly pagination.
Source: community / Tested: SharpSkill

```typescript
// Cursor-based pagination (preferred for large datasets)
const PAGE_SIZE = 50
async function getPostsPage(cursor?: number) {
  return prisma.post.findMany({
    take: PAGE_SIZE,
    ...(cursor ? { skip: 1, cursor: { id: cursor } } : {}),
    orderBy: { id: 'asc' },
    select: { id: true, title: true, createdAt: true },
  })
}
```

**5. `prisma generate` must run before application start in CI/CD**
The generated `@prisma/client` is tied to the exact schema at generation time. Deploying without running `prisma generate` causes `@prisma/client did not initialize yet` errors at runtime. Add `prisma generate` as a build step, not a postinstall script that may be skipped.
Source: SO (41 votes) / GitHub Issues

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `P2024: Timed out fetching a new connection` | Pool exhausted; too many concurrent requests or `connection_limit` too low | Increase `connection_limit`, add retry with backoff, or add PgBouncer proxy |
| `@prisma/client did not initialize yet` | `prisma generate` not run after schema change or fresh install | Add `prisma generate` to build pipeline before app start |
| `Environment variable not