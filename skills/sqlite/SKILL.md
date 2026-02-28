---
name: sqlite
description: "Production-depth SQLite operations for Node.js: connection pool lifecycle, WAL journaling, concurrent write locking, database corruption detection and recovery, page fragmentation and VACUUM strategies, and migration management. Use when asked to: set up SQLite with Node.js, handle SQLite SQLITE_BUSY or locked database errors, configure WAL mode for concurrency, detect or repair a corrupt SQLite database, tune VACUUM and auto-vacuum settings, manage connection pool sizing, run SQL-based migrations, or optimize INSERT throughput under write contention."
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: database
  tags: [sqlite, node, typescript, wal, corruption, vacuum, migrations, concurrency, pooling]
---

# SQLite Skill

## Quick Start

```bash
npm install sqlite sqlite3
```

```typescript
import sqlite3 from 'sqlite3'
import { open } from 'sqlite'

const db = await open({
  filename: './app.db',
  driver: sqlite3.Database,
})

await db.run('PRAGMA journal_mode = WAL')
await db.run('PRAGMA foreign_keys = ON')
await db.run('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)')
await db.run('INSERT INTO users (name) VALUES (?)', ['Alice'])
const user = await db.get<{ id: number; name: string }>('SELECT * FROM users WHERE id = ?', [1])
console.log(user) // { id: 1, name: 'Alice' }
await db.close()
```

## When to Use

Use this skill when asked to:
- Set up or migrate an SQLite database in a Node.js / TypeScript project
- Fix `SQLITE_BUSY`, `database is locked`, or write timeout errors
- Enable WAL mode or configure journaling for concurrent readers and writers
- Detect, verify integrity of, or recover a corrupted SQLite database file
- Tune `VACUUM`, `auto_vacuum`, or page fragmentation for storage efficiency
- Size and manage a connection pool for SQLite in a long-running server process
- Run SQL-based schema migrations with rollback support
- Maximize INSERT throughput under high write contention

## Core Patterns

### Pattern 1: WAL Mode + Busy Timeout for Concurrent Access (Source: official)

SQLite's default rollback journal allows only one writer at a time and blocks all reads during a write. WAL (Write-Ahead Logging) mode allows concurrent readers alongside one writer and dramatically reduces `SQLITE_BUSY` frequency.

```typescript
import sqlite3 from 'sqlite3'
import { open, Database } from 'sqlite'

async function openDb(path: string): Promise<Database> {
  const db = await open({ filename: path, driver: sqlite3.Database })

  // WAL mode: readers do not block writer, writer does not block readers
  await db.run('PRAGMA journal_mode = WAL')

  // How long (ms) the driver retries before throwing SQLITE_BUSY
  // Set higher (5000+) in multi-process environments
  await db.run('PRAGMA busy_timeout = 5000')

  // Synchronous=NORMAL is safe with WAL and faster than FULL
  await db.run('PRAGMA synchronous = NORMAL')

  // Tune cache size (negative = KiB). 64 MiB shown here.
  await db.run('PRAGMA cache_size = -65536')

  // Enforce foreign key constraints (disabled by default in SQLite)
  await db.run('PRAGMA foreign_keys = ON')

  return db
}
```

> **Why busy_timeout matters:** Without it, the first `SQLITE_BUSY` is thrown immediately. With a timeout, SQLite spins internally and retries, hiding transient contention from application code. Source: [SQLite PRAGMA docs](https://www.sqlite.org/pragma.html#pragma_busy_timeout)

### Pattern 2: Connection Pool Lifecycle Management (Source: official + community)

SQLite is not thread-safe in `SQLITE_THREADSAFE=0` builds and has no native connection pool. For Node.js servers, maintain a **small, bounded pool** of pre-warmed connections—each with WAL PRAGMAs already applied—and never share a connection across concurrent async operations.

```typescript
// Source: community / Tested: SharpSkill
import sqlite3 from 'sqlite3'
import { open, Database } from 'sqlite'

class SqlitePool {
  private pool: Database[] = []
  private inUse = new Set<Database>()
  private queue: Array<(db: Database) => void> = []

  constructor(
    private readonly path: string,
    private readonly size: number = 4, // 1-4 is typical; SQLite serialises writes anyway
  ) {}

  async initialize(): Promise<void> {
    for (let i = 0; i < this.size; i++) {
      const db = await open({ filename: this.path, driver: sqlite3.Database })
      await db.run('PRAGMA journal_mode = WAL')
      await db.run('PRAGMA busy_timeout = 5000')
      await db.run('PRAGMA foreign_keys = ON')
      this.pool.push(db)
    }
  }

  acquire(): Promise<Database> {
    const available = this.pool.find((db) => !this.inUse.has(db))
    if (available) {
      this.inUse.add(available)
      return Promise.resolve(available)
    }
    // Queue caller until a connection is released
    return new Promise((resolve) => this.queue.push(resolve))
  }

  release(db: Database): void {
    this.inUse.delete(db)
    const next = this.queue.shift()
    if (next) {
      this.inUse.add(db)
      next(db)
    }
  }

  async withConnection<T>(fn: (db: Database) => Promise<T>): Promise<T> {
    const db = await this.acquire()
    try {
      return await fn(db)
    } finally {
      this.release(db)
    }
  }

  async closeAll(): Promise<void> {
    await Promise.all(this.pool.map((db) => db.close()))
    this.pool = []
  }
}

// Usage
const pool = new SqlitePool('./app.db', 4)
await pool.initialize()

const result = await pool.withConnection(async (db) => {
  return db.all('SELECT * FROM users')
})

// On process exit:
process.on('SIGTERM', async () => { await pool.closeAll(); process.exit(0) })
```

**Pool sizing rule of thumb:** SQLite serialises all writers at the OS level; pool size > 1 benefits read-heavy workloads only. For write-heavy apps, use a pool size of **1** to eliminate all intra-process lock contention.

### Pattern 3: Batched Writes Inside an Explicit Transaction (Source: official)

Each `INSERT` without a wrapping transaction auto-commits, triggering an fsync per row. Wrapping bulk inserts in a single transaction is the single biggest INSERT throughput lever available.

```typescript
async function bulkInsert(db: Database, rows: { name: string; value: number }[]): Promise<void> {
  await db.run('BEGIN')
  try {
    const stmt = await db.prepare('INSERT INTO metrics (name, value) VALUES (?, ?)')
    for (const row of rows) {
      await stmt.run(row.name, row.value)
    }
    await stmt.finalize()
    await db.run('COMMIT')
  } catch (err) {
    await db.run('ROLLBACK')
    throw err
  }
}
```

Benchmarks show committing every 10,000 rows rather than every row can increase throughput by **50–100×**. Source: [SO: Improve INSERT-per-second performance of SQLite](https://stackoverflow.com/q/1711631)

### Pattern 4: SQL-Based Migrations with Rollback (Source: official)

```typescript
import path from 'path'

async function runMigrations(db: Database): Promise<void> {
  await db.migrate({
    migrationsPath: path.join(__dirname, 'migrations'),
    // Optional: table name to track applied migrations
    tableName: 'migrations',
  })
}
```

Migration file naming convention (must match): `001-initial.sql`, `002-add-index.sql`, etc.

```sql
-- 001-initial.sql
-- Up
CREATE TABLE IF NOT EXISTS orders (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  total   REAL    NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Down
DROP TABLE IF EXISTS orders;
```

`db.migrate()` runs each file exactly once and records it in the migrations table. Down migrations are never run automatically—execute them explicitly for rollback.

### Pattern 5: Corruption Detection and Recovery (Source: official + community)

```typescript
// Source: community / Tested: SharpSkill
import { execSync } from 'child_process'
import fs from 'fs'

/**
 * Run SQLite's built-in integrity checker.
 * Returns true if database is healthy, false if corrupt.
 */
async function checkIntegrity(db: Database): Promise<boolean> {
  // integrity_check is thorough but slow on large DBs; use quick_check for routine monitoring
  const rows = await db.all<{ integrity_check: string }[]>('PRAGMA integrity_check')
  const allOk = rows.every((r) => r.integrity_check === 'ok')
  if (!allOk) {
    console.error('Integrity failures:', rows.map((r) => r.integrity_check))
  }
  return allOk
}

/**
 * Recover a corrupt database using SQLite's .dump + reimport technique.
 * Works when the database is partially readable.
 */
async function recoverDatabase(corruptPath: string, recoveredPath: string): Promise<void> {
  // sqlite3 CLI must be installed on the host
  // The .recover command (SQLite >= 3.29.0) is more thorough than .dump for corrupted files
  const dumpCmd = `sqlite3 "${corruptPath}" ".recover" | sqlite3 "${recoveredPath}"`
  execSync(dumpCmd, { stdio: 'pipe' })
  console.log(`Recovery written to ${recoveredPath}. Verify before replacing original.`)
}

/**
 * Rotate: backup healthy DB before potentially destructive operations.
 */
function backupDatabase(sourcePath: string, backupPath: string): void {
  fs.copyFileSync(sourcePath, backupPath) // copyFileSync is atomic on most OS implementations
}
```

**Recovery decision tree:**
1. Run `PRAGMA integrity_check` → if `ok`, no action needed.
2. If errors, attempt `.recover` (SQLite ≥ 3.29) to extract maximum data into a new file.
3. If `.recover` fails, fall back to `.dump` and re-import—this skips unreadable pages.
4. Always restore from backup if one exists before attempting recovery.

Source: [SQLite PRAGMA integrity_check docs](https://www.sqlite.org/pragma.html#pragma_integrity_check), [SQLite .recover command](https://www.sqlite.org/cli.html#recover)

### Pattern 6: VACUUM and Fragmentation Management (Source: official)

SQLite reclaims deleted pages as free-list pages but does not return them to the OS until `VACUUM` is run. High churn tables (frequent deletes/updates) accumulate fragmentation.

```typescript
/**
 * Determine how fragmented the database is before deciding to VACUUM.
 * A ratio > 0.1 (10% free pages) is a reasonable vacuum trigger.
 */
async function getFragmentationRatio(db: Database): Promise<number> {
  const { page_count } = await db.get<{ page_count: number }>('PRAGMA page_count')
  const { freelist_count } = await db.get<{ freelist_count: number }>('PRAGMA freelist_count')
  return freelist_count / page_count
}

/**
 * VACUUM rebuilds the entire database file into a new file and replaces it.
 * Requires free disk space equal to the database size. Blocks ALL access during run.
 * Schedule during maintenance windows only.
 */
async function runVacuum(db: Database): Promise<void> {
  console.time('VACUUM')
  await db.run('VACUUM')
  console.timeEnd('VACUUM')
}

/**
 * VACUUM INTO writes the defragmented database to a new path without touching
 * the live file—safe to run on a live database (SQLite >= 3.27.0).
 */
async function vacuumInto(db: Database, outputPath: string): Promise<void> {
  await db.run(`VACUUM INTO '${outputPath}'`)
}

/**
 * auto_vacuum = INCREMENTAL enables page-level reclamation without full VACUUM.
 * Must be set BEFORE the database is created (or after VACUUM to switch modes).
 * Use incremental_vacuum(N) to reclaim N free pages on demand.
 */
async function configureAutoVacuum(db: Database): Promise<void> {
  await db.run('PRAGMA auto_vacuum = INCREMENTAL')
  // Reclaim up to 100 pages at a time during low-traffic periods
  await db.run('PRAGMA incremental_vacuum(100)')
}
```

**VACUUM impact summary:**

| Mode | Disk space needed | Live access blocked | Best for |
|---|---|---|---| 
| `VACUUM` | ~100% of DB size | Yes (full duration) | Maintenance windows |
| `VACUUM INTO` | ~100% of DB size | No | Online compaction to backup file |
| `auto_vacuum = FULL` | Minimal | Brief per-transaction | Small, low-churn DBs |
| `auto_vacuum = INCREMENTAL` | Minimal | Brief per invocation | Large or high-churn DBs |

Source: [SQLite VACUUM docs](https://www.sqlite.org/lang_vacuum.html), [SQLite auto_vacuum PRAGMA](https://www.sqlite.org/pragma.html#pragma_auto_vacuum)

### Pattern 7: Error Handling and Retry on SQLITE_BUSY (Source: community)

```typescript
// Source: community / Tested: SharpSkill

const SQLITE_BUSY = 'SQLITE_BUSY'
const SQLITE_LOCKED = 'SQLITE_LOCKED'

interface SqliteError extends Error {
  code?: string
}

async function withRetry<T>(
  fn: () => Promise<T>,
  maxAttempts = 5,
  baseDelayMs = 100,
): Promise<T> {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn()
    } catch (err) {
      const sqlErr = err as SqliteError
      const isRetryable = sqlErr.code === SQLITE_BUSY || sqlErr.code === SQLITE_LOCKED
      if (!isRetryable || attempt === maxAttempts) throw err
      // Exponential backoff with jitter
      const delay = baseDelayMs * 2 ** (attempt - 1) + Math.random() * 50
      await new Promise((res) => setTimeout(res, delay))
    }
  }
  throw new Error('unreachable')
}

// Usage
const rows = await withRetry(() => db.all('SELECT * FROM orders WHERE status = ?', ['pending']))
```

## Production Notes

1. **WAL checkpoint accumulation causes read slowdown.** WAL files grow unbounded if `wal_autocheckpoint` is disabled or the checkpoint never runs. Accumulated WAL files are re-read on every connection open. Fix: leave `wal_autocheckpoint` at its default (1000 pages) or trigger `PRAGMA wal_checkpoint(TRUNCATE)` during low-traffic periods. Source: [SQLite WAL docs](https://www.sqlite.org/wal.html)

2. **`SQLITE_BUSY` from multi-process access cannot be fully eliminated without `busy_timeout`.** When multiple OS processes open the same WAL file, the kernel-level lock can be held longer than Node.js's event loop tick. Without `busy_timeout`, every contention event surfaces as a thrown error. Set `PRAGMA busy_timeout = 5000` on every connection. Source: SO question on Android concurrency (high-vote community