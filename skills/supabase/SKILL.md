---
name: supabase-production
description: "Production-depth Supabase patterns covering connection pooling with PgBouncer, RLS policy performance tuning, JWT expiry and token refresh races, zero-downtime database migrations, and index alignment for Row Level Security. Use when asked to: set up Supabase connection pooling, configure PgBouncer for high concurrency, write performant RLS policies, handle token refresh edge cases, run database migrations without downtime, debug slow queries caused by RLS, manage JWT expiry in production, optimize Supabase for scale."
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: database
  tags: [supabase, postgresql, pgbouncer, rls, jwt, migrations, connection-pooling, production]
---

# Supabase Production Skill

## Quick Start

```bash
# Install CLI
npm i supabase --save-dev

# Initialize project and link to remote
npx supabase init
npx supabase login
npx supabase link --project-ref YOUR_PROJECT_REF

# Pull remote schema into local migrations
npx supabase db pull
```

```ts
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!,
  { auth: { autoRefreshToken: true, persistSession: true } }
)
```

## When to Use

Use this skill when asked to:
- Set up or tune connection pooling with PgBouncer in Supabase
- Configure pool modes (transaction vs session) for serverless workloads
- Write RLS policies that don't cause full table scans
- Add indexes that align with Row Level Security filter columns
- Handle JWT expiration, silent refresh failures, or token refresh race conditions
- Run schema migrations in production without downtime or locking
- Debug slow PostgREST queries traced back to RLS policy overhead
- Manage Supabase auth session state in SSR or edge environments
- Troubleshoot SASL signature mismatch or auth provider rate limiting
- Scale Supabase beyond free-tier defaults for production traffic

---

## Core Patterns

### Pattern 1: Connection Pooling — PgBouncer Mode Selection (Source: official)

Supabase exposes two connection strings: **direct** (`port 5432`) and **pooled** (`port 6543`).  
Use the **pooled (transaction mode)** string for serverless functions and short-lived clients.  
Use the **direct** string only for migrations and long-lived processes that need session-level features (e.g., `SET LOCAL`, `LISTEN/NOTIFY`, prepared statements).

```ts
// For serverless (Vercel, Netlify, Edge) — transaction mode pooler
// Connection string: postgresql://postgres:[password]@[host]:6543/postgres?pgbouncer=true
const supabaseServerless = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  {
    db: {
      schema: 'public',
    },
    global: {
      headers: { 'x-connection-encrypted': 'true' },
    },
  }
)

// For migrations (direct connection — bypasses pgbouncer)
// DATABASE_URL=postgresql://postgres:[password]@[host]:5432/postgres
// Use this in supabase/config.toml or migration scripts only
```

```toml
# supabase/config.toml — explicit pool size for local dev parity
[db]
port = 54322
pool_size = 15          # match your prod pgbouncer default_pool_size

[db.pooler]
enabled = true
port = 54329
pool_mode = "transaction"   # "session" | "transaction" | "statement"
default_pool_size = 15
max_client_conn = 100
```

**Key rules:**
- `transaction` mode: cannot use `SET`, `PREPARE`, `LISTEN`, advisory locks — safe for most CRUD
- `session` mode: full Postgres feature parity but fewer concurrent connections
- Always append `?pgbouncer=true` to the pooled URL to disable prepared statements in the driver

---

### Pattern 2: RLS Policy Performance — Index Alignment (Source: official)

RLS policies are evaluated as `WHERE` clause additions on every query. Without supporting indexes, every authenticated read becomes a sequential scan.

```sql
-- BAD: policy references auth.uid() but no index on user_id
CREATE POLICY "users_own_rows" ON documents
  FOR SELECT USING (user_id = auth.uid());

-- The planner cannot use a partial index across auth.uid() dynamically,
-- but a standard B-tree index on the filter column is essential.

-- GOOD: add B-tree index on the RLS filter column
CREATE INDEX CONCURRENTLY idx_documents_user_id
  ON documents (user_id);

-- For tenant-partitioned tables, composite index with tenant first
CREATE INDEX CONCURRENTLY idx_messages_tenant_user
  ON messages (tenant_id, user_id);

-- Verify the policy + index are aligned with EXPLAIN ANALYZE
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM documents WHERE true;
-- Look for "Index Scan using idx_documents_user_id" not "Seq Scan"
```

```sql
-- Security definer function avoids repeated auth schema lookups
-- Wrap auth.uid() in a stable function to help the planner cache the value
CREATE OR REPLACE FUNCTION current_user_id()
RETURNS uuid
LANGUAGE sql STABLE
AS $$
  SELECT auth.uid();
$$;

CREATE POLICY "users_own_rows_v2" ON documents
  FOR SELECT USING (user_id = current_user_id());
```

**Why it matters:** `auth.uid()` is a Postgres function call re-evaluated per row. On a 100k-row table with no index, a single `SELECT` with RLS can take 500ms+. The `STABLE` wrapper allows the planner to call it once per query, and the B-tree index eliminates the seq scan.

---

### Pattern 3: JWT Expiry and Token Refresh Race Conditions (Source: official + community)

In SSR and concurrent-tab scenarios, multiple requests can simultaneously detect token expiry and race to call `refreshSession()`. Only one refresh succeeds; others receive stale tokens or `invalid_refresh_token` errors.

```ts
// Source: community — race-safe refresh using a module-level promise lock
// Tested: SharpSkill

let refreshPromise: Promise<void> | null = null

async function getValidSession(supabase: ReturnType<typeof createClient>) {
  const { data: { session } } = await supabase.auth.getSession()

  if (!session) return null

  const expiresAt = session.expires_at ?? 0
  const nowSec = Math.floor(Date.now() / 1000)
  const bufferSec = 60 // refresh 60s before actual expiry

  if (expiresAt - nowSec > bufferSec) {
    return session // still valid
  }

  // Deduplicate concurrent refresh calls
  if (!refreshPromise) {
    refreshPromise = supabase.auth
      .refreshSession()
      .then(({ error }) => {
        if (error) throw error
      })
      .finally(() => {
        refreshPromise = null
      })
  }

  await refreshPromise
  const { data: { session: refreshed } } = await supabase.auth.getSession()
  return refreshed
}
```

```ts
// Server-side (Next.js App Router / SSR) — use @supabase/ssr package
// Never share a single client instance across requests in SSR
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export function createSupabaseServerClient() {
  const cookieStore = cookies()
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return cookieStore.getAll() },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch {
            // Called from Server Component — cookie writes are no-ops, safe to ignore
          }
        },
      },
    }
  )
}
```

---

### Pattern 4: Zero-Downtime Migrations (Source: official)

Supabase runs on Postgres. Schema changes that acquire `AccessExclusiveLock` (e.g., `ALTER TABLE ADD COLUMN NOT NULL`, `CREATE INDEX` without `CONCURRENTLY`) block all reads and writes.

```sql
-- PHASE 1: Add nullable column first (no lock contention)
ALTER TABLE orders ADD COLUMN fulfilled_at timestamptz;

-- PHASE 2: Backfill in batches to avoid long transactions
DO $$
DECLARE
  batch_size INT := 1000;
  last_id    BIGINT := 0;
  max_id     BIGINT;
BEGIN
  SELECT MAX(id) INTO max_id FROM orders;
  WHILE last_id < max_id LOOP
    UPDATE orders
    SET fulfilled_at = created_at  -- or real backfill logic
    WHERE id > last_id
      AND id <= last_id + batch_size
      AND fulfilled_at IS NULL;
    last_id := last_id + batch_size;
    PERFORM pg_sleep(0.05); -- brief pause between batches
  END LOOP;
END $$;

-- PHASE 3: Add NOT NULL constraint using a CHECK CONSTRAINT (Postgres 12+)
-- This validates without a full table rewrite on Postgres 12+
ALTER TABLE orders
  ADD CONSTRAINT orders_fulfilled_at_not_null
  CHECK (fulfilled_at IS NOT NULL) NOT VALID;

ALTER TABLE orders
  VALIDATE CONSTRAINT orders_fulfilled_at_not_null;
-- VALIDATE acquires ShareUpdateExclusiveLock — reads/writes continue

-- PHASE 4: Drop the check constraint, set NOT NULL (cheap after validate)
ALTER TABLE orders ALTER COLUMN fulfilled_at SET NOT NULL;
ALTER TABLE orders DROP CONSTRAINT orders_fulfilled_at_not_null;
```

```sql
-- Always use CONCURRENTLY for new indexes in production
-- Note: cannot run inside a transaction block
CREATE INDEX CONCURRENTLY idx_orders_fulfilled_at
  ON orders (fulfilled_at)
  WHERE fulfilled_at IS NOT NULL;

-- Supabase migration file: wrap non-concurrent DDL carefully
-- supabase/migrations/20240101000000_add_fulfilled_at.sql
-- Split into separate migration files if phases need to be deployed independently
```

```bash
# Deploy migration to production (direct connection required — not pooler)
DATABASE_URL="postgresql://postgres:[pw]@[host]:5432/postgres" \
  npx supabase db push --include-all
```

---

### Pattern 5: RLS Policy Debugging — Tracing Policy Overhead (Source: community)

```sql
-- Source: community
-- Tested: SharpSkill

-- Step 1: Check which policies exist and their definitions
SELECT schemaname, tablename, policyname, cmd, qual, with_check
FROM pg_policies
WHERE tablename = 'your_table';

-- Step 2: Temporarily set role to test policy as a specific user
SET LOCAL role = authenticated;
SET LOCAL "request.jwt.claims" = '{"sub": "user-uuid-here", "role": "authenticated"}';
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM your_table LIMIT 100;
RESET role;

-- Step 3: Identify seq scans caused by RLS — look for filter conditions post-scan
-- "Rows Removed by Filter" >> 0 with "Seq Scan" = missing index on RLS column

-- Step 4: pg_stat_statements to find consistently slow RLS-heavy queries
SELECT query, mean_exec_time, calls, total_exec_time
FROM pg_stat_statements
WHERE query ILIKE '%your_table%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

### Pattern 6: Error Handling — Auth Race and Storage RLS (Source: community)

Real error from GitHub Issues and SO (35v): `new row violates row-level security policy for table "objects"`

```ts
// Source: community
// Tested: SharpSkill

// Storage uploads fail when: 1) JWT is expired, 2) bucket policy missing INSERT,
// 3) path doesn't match policy pattern

async function uploadWithAuthGuard(
  supabase: ReturnType<typeof createClient>,
  bucket: string,
  path: string,
  file: File
) {
  // Ensure session is fresh before upload
  const { data: { session }, error: sessionError } = await supabase.auth.getSession()
  if (sessionError || !session) {
    throw new Error('No valid session — cannot upload')
  }

  // Refresh proactively if within 2 minutes of expiry
  if ((session.expires_at ?? 0) - Date.now() / 1000 < 120) {
    const { error: refreshError } = await supabase.auth.refreshSession()
    if (refreshError) throw new Error(`Token refresh failed: ${refreshError.message}`)
  }

  const { data, error } = await supabase.storage
    .from(bucket)
    .upload(path, file, { upsert: false })

  if (error?.message.includes('row-level security')) {
    // Diagnostic: log the actual path vs policy expectation
    console.error('RLS mismatch. Upload path:', path)
    console.error('Expected pattern: {user_id}/filename — check storage policy')
    throw error
  }

  return data
}
```

```sql
-- Correct storage RLS policy for user-scoped uploads
CREATE POLICY "user_owns_objects" ON storage.objects
  FOR INSERT WITH CHECK (
    bucket_id = 'photos'
    AND (storage.foldername(name))[1] = auth.uid()::text
  );

CREATE POLICY "user_reads_own_objects" ON storage.objects
  FOR SELECT USING (
    bucket_id = 'photos'
    AND (storage.foldername(name))[1] = auth.uid()::text
  );
```

---

## Production Notes

**1. PgBouncer transaction mode breaks prepared statements**  
Source: GitHub Issues, Supabase Docs  
Prisma, some ORMs, and `pg` driver with `prepare: true` will fail with `prepared statement "s0" already exists` in transaction pool mode. Fix: set `?pgbouncer=true` in your DATABASE_URL (disables prepared statements) or switch to `session` mode for those clients. Prisma requires `directUrl` (port 5432) for migrations and `url` (port 6543 + `?pgbouncer=true`) for queries.

**2. RLS on high-cardinality tables causes invisible performance degradation**  
Source: GitHub Issues (Realtime RLS #44), SO  
Without `CREATE INDEX CONCURRENTLY` on every column referenced in a `USING` or `WITH CHECK` clause, PostgREST queries degrade silently as row count grows. The Supabase dashboard does not surface this as an error — only slow query logs catch it. Enable `pg_stat_statements` extension and monitor `mean_exec_time` weekly.

**3. `SASL_SIGNATURE_MISMATCH` on self-hosted deploys after credential rotation**  
Source: GitHub Issues (51 comments)  
Occurs when `POSTGRES_PASSWORD` in Docker secrets diverges from what PgBouncer has cached. Fix: restart the `supabase-db` and `supabase-pooler` containers together after any credential change. Never rotate passwords with a rolling restart — both must see the new credential simultaneously.

**4. Rate limiting bleeds across auth providers**  
Source: GitHub Issues (67 comments)  
GoTrue applies rate limits at the project level, not per-provider. Having email auth enabled counts against the same bucket as SMS OTP. Under traffic spikes, SMS flows receive 429s even if email is unused. Fix on self-hosted: increase `GOTRUE_RATE_LIMIT_EMAIL_SENT` and `GOTRUE_SMS_MAX_FREQUENCY` in your GoTrue env. On hosted, file a support ticket to raise limits or