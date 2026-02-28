---
name: mysql
description: "Production-grade MySQL integration for Node.js applications. Use when asked to: connect Node.js to MySQL, set up a connection pool, prevent SQL injection with parameterized queries, handle transaction isolation levels, debug deadlocks, analyze slow queries, tune pool size for high traffic, or recover from connection pool exhaustion."
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: database
  tags: [mysql, node.js, connection-pool, sql-injection, transactions, deadlocks, slow-query]
---

# MySQL Skill

## Quick Start

```bash
npm install mysql
```

```js
// Source: official mysql@2.18.1 README
const mysql = require('mysql');

const pool = mysql.createPool({
  host:            'localhost',
  user:            'app_user',
  password:        process.env.DB_PASSWORD,
  database:        'production_db',
  connectionLimit: 10,          // max concurrent connections
  waitForConnections: true,     // queue requests when pool is full
  queueLimit:      0            // 0 = unlimited queue depth
});

// Always use pool.query — never bare connection.query in production
pool.query('SELECT 1 + 1 AS result', (err, results) => {
  if (err) throw err;
  console.log(results[0].result); // 2
});
```

## When to Use

Use this skill when asked to:
- Connect a Node.js application to a MySQL database
- Set up and tune a connection pool for production traffic
- Prevent SQL injection using parameterized / escaped queries
- Execute transactions with specific isolation levels
- Detect and recover from deadlocks automatically
- Enable and analyze the MySQL slow query log
- Handle `ECONNRESET`, `PROTOCOL_CONNECTION_LOST`, or pool exhaustion errors
- Optimize queries with `EXPLAIN` and index strategy
- Stream large result sets without loading them fully into memory
- Safely handle `INSERT`, `UPDATE`, and `DELETE` with affected-row verification

## Core Patterns

### Pattern 1: Connection Pool Tuning (Source: official)

Pool exhaustion manifests as requests hanging indefinitely. Set `connectionLimit`
based on `(core_count * 2) + effective_spindle_count`. Monitor the `enqueue`
event to detect saturation before timeouts occur.

```js
// Source: official mysql@2.18.1 README — Pool events
const pool = mysql.createPool({
  host:               'localhost',
  user:               'app_user',
  password:           process.env.DB_PASSWORD,
  database:           'production_db',
  connectionLimit:    20,
  acquireTimeout:     10000,   // ms to wait for a connection before error
  waitForConnections: true,
  queueLimit:         100      // reject after 100 queued requests
});

let queueDepth = 0;

pool.on('enqueue', () => {
  queueDepth++;
  console.warn(`Pool saturated — queue depth: ${queueDepth}`);
  // Emit metric to your APM here
});

pool.on('acquire', (connection) => {
  queueDepth = Math.max(0, queueDepth - 1);
  console.log(`Connection ${connection.threadId} acquired`);
});

pool.on('release', (connection) => {
  console.log(`Connection ${connection.threadId} released`);
});

// Graceful shutdown — drain pool before process exit
process.on('SIGTERM', () => {
  pool.end((err) => {
    if (err) console.error('Pool shutdown error:', err);
    process.exit(err ? 1 : 0);
  });
});
```

### Pattern 2: SQL Injection Prevention with Parameterized Queries (Source: official)

Never interpolate user input into query strings. Use `?` placeholders — the driver
escapes values using `mysql.escape()` internally. For dynamic identifiers
(table/column names) use `mysql.escapeId()`.

```js
// Source: official mysql@2.18.1 README — Escaping query values

// ❌ VULNERABLE — never do this
const bad = `SELECT * FROM users WHERE email = '${userInput}'`;

// ✅ SAFE — placeholder escaping
pool.query(
  'SELECT id, name FROM users WHERE email = ? AND active = ?',
  [userInput, true],
  (err, results) => {
    if (err) throw err;
    console.log(results);
  }
);

// ✅ SAFE — object syntax (maps keys to column names automatically)
pool.query(
  'INSERT INTO audit_log SET ?',
  { user_id: 42, action: 'login', ts: new Date() },
  (err, result) => {
    if (err) throw err;
    console.log('Inserted ID:', result.insertId);
  }
);

// ✅ SAFE — dynamic identifier (table/column names from variables)
const column = mysql.escapeId(untrustedColumnName); // e.g. "`username`"
pool.query(
  `SELECT ${column} FROM users WHERE id = ?`,
  [userId],
  (err, results) => { /* ... */ }
);

// Standalone escape for building queries outside the driver
const safeValue = mysql.escape(userInput);
const safeId    = mysql.escapeId(tableName);
```

### Pattern 3: Transactions with Isolation Levels (Source: official)

Use `pool.getConnection()` to pin a transaction to one connection.
Set isolation level per-transaction to avoid global side effects.

```js
// Source: official mysql@2.18.1 README — Transactions
function transferFunds(fromId, toId, amount, callback) {
  pool.getConnection((err, conn) => {
    if (err) return callback(err);

    // REPEATABLE READ prevents phantom reads during the transfer check
    conn.query('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ', (err) => {
      if (err) { conn.release(); return callback(err); }

      conn.beginTransaction((err) => {
        if (err) { conn.release(); return callback(err); }

        conn.query(
          'UPDATE accounts SET balance = balance - ? WHERE id = ? AND balance >= ?',
          [amount, fromId, amount],
          (err, result) => {
            if (err) return rollback(conn, callback, err);
            if (result.affectedRows === 0) {
              return rollback(conn, callback, new Error('Insufficient funds'));
            }

            conn.query(
              'UPDATE accounts SET balance = balance + ? WHERE id = ?',
              [amount, toId],
              (err) => {
                if (err) return rollback(conn, callback, err);

                conn.commit((err) => {
                  conn.release();
                  if (err) return callback(err);
                  callback(null, { success: true });
                });
              }
            );
          }
        );
      });
    });
  });
}

function rollback(conn, callback, err) {
  conn.rollback(() => {
    conn.release();
    callback(err);
  });
}
```

### Pattern 4: Deadlock Detection and Automatic Retry (Source: community)

MySQL error code `1213` (`ER_LOCK_DEADLOCK`) means the engine chose your
transaction as the deadlock victim. The correct response is an immediate retry
with exponential backoff — not surfacing the error to the user.

```js
// Source: community — MySQL error code reference + SO deadlock patterns
// Tested: SharpSkill

const DEADLOCK_ERROR_CODE = 1213;
const MAX_RETRIES = 3;

function withDeadlockRetry(transactionFn, callback, attempt = 0) {
  transactionFn((err, result) => {
    if (err && err.errno === DEADLOCK_ERROR_CODE && attempt < MAX_RETRIES) {
      const delay = Math.pow(2, attempt) * 50; // 50ms, 100ms, 200ms
      console.warn(`Deadlock detected — retry ${attempt + 1} in ${delay}ms`);
      setTimeout(() => {
        withDeadlockRetry(transactionFn, callback, attempt + 1);
      }, delay);
    } else {
      callback(err, result);
    }
  });
}

// Usage
withDeadlockRetry(
  (done) => transferFunds(1, 2, 100, done),
  (err, result) => {
    if (err) console.error('Transaction failed after retries:', err.message);
    else console.log('Transfer complete:', result);
  }
);
```

### Pattern 5: Slow Query Log Analysis and Index Optimization (Source: community)

Enable the slow query log at runtime (no restart needed in MySQL 5.6+),
then use `EXPLAIN` to identify missing indexes.

```sql
-- Source: community — MySQL 5.6+ dynamic variable support
-- Tested: SharpSkill

-- Enable slow query log at runtime (survives until next restart)
SET GLOBAL slow_query_log      = 'ON';
SET GLOBAL long_query_time     = 1;          -- seconds; use 0.1 in staging
SET GLOBAL log_queries_not_using_indexes = 'ON';
SET GLOBAL slow_query_log_file = '/var/log/mysql/slow.log';

-- Persist across restarts: add to /etc/mysql/mysql.conf.d/mysqld.cnf
-- slow_query_log      = 1
-- long_query_time     = 1
-- log_queries_not_using_indexes = 1

-- Analyze a specific slow query
EXPLAIN SELECT o.id, u.name
FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.status = 'pending'
  AND o.created_at > NOW() - INTERVAL 7 DAY;

-- If type = ALL or type = index → add a composite index
CREATE INDEX idx_orders_status_created
  ON orders (status, created_at);

-- Verify the optimizer uses the new index
EXPLAIN SELECT o.id, u.name
FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.status = 'pending'
  AND o.created_at > NOW() - INTERVAL 7 DAY;
-- Expect: type = range, key = idx_orders_status_created
```

```js
// Stream large result sets — avoids OOM for reports/exports
// Source: official mysql@2.18.1 README — Streaming query rows
const query = pool.query('SELECT * FROM large_events WHERE year = ?', [2024]);

query
  .on('error', (err) => console.error('Stream error:', err))
  .on('fields', (fields) => console.log('Columns:', fields.map(f => f.name)))
  .on('result', (row) => {
    pool.pause(); // back-pressure: stop reading while processing
    processRow(row, () => pool.resume());
  })
  .on('end', () => console.log('Stream complete'));
```

### Pattern 6: Server Disconnect Recovery (Source: official)

```js
// Source: official mysql@2.18.1 README — Server disconnects
// Pool handles reconnect automatically; bare connections do not.

function createReconnectingConnection() {
  let connection = mysql.createConnection({
    host:     'localhost',
    user:     'app_user',
    password: process.env.DB_PASSWORD,
    database: 'production_db'
  });

  function handleDisconnect() {
    connection.connect((err) => {
      if (err) {
        console.error('Reconnect failed, retrying in 2s:', err.message);
        setTimeout(handleDisconnect, 2000);
      }
    });

    connection.on('error', (err) => {
      console.error('Connection error:', err.code);
      if (err.code === 'PROTOCOL_CONNECTION_LOST' ||
          err.code === 'ECONNRESET' ||
          err.code === 'ETIMEDOUT') {
        handleDisconnect(); // re-establish
      } else {
        throw err; // surface non-recoverable errors
      }
    });
  }

  handleDisconnect();
  return connection;
}
```

## Production Notes

**1. Pool exhaustion causes silent request hangs (not errors)**
When `queueLimit: 0` (unlimited) and the pool is saturated, new requests queue
forever. Set `queueLimit` to a finite value and `acquireTimeout` so callers
receive a fast error rather than a hanging request. Monitor the `enqueue` event
and alert when queue depth > 10% of `connectionLimit`.
Source: SO, GitHub Issues mysqljs/mysql #1547

**2. `connection.end()` vs `connection.destroy()` in error paths**
`end()` waits for in-flight queries to complete before closing — safe for normal
shutdown. In error handlers, use `destroy()` which immediately terminates the
socket. Failing to destroy on error leaves zombie connections consuming pool slots.
Source: official mysql@2.18.1 README — Terminating connections

**3. Transaction connections must be released even on rollback**
A common leak: calling `rollback()` but forgetting `conn.release()` inside the
callback. Always structure rollback as `conn.rollback(() => { conn.release(); callback(err); })`.
Every code path that calls `pool.getConnection()` must eventually call `conn.release()`.
Source: SO, Reddit r/node

**4. `DATETIME` vs `TIMESTAMP` affects timezone behavior**
`TIMESTAMP` is stored as UTC and converted to `@@session.time_zone` on read —
dangerous if sessions have different timezones. `DATETIME` stores the literal
value with no conversion. For distributed systems, use `DATETIME` with explicit
UTC values, or set `timezone: 'Z'` in the connection options.
Source: SO (3217 votes), MySQL 8.0 Reference Manual

**5. `insertId` is `0` for non-AUTO_INCREMENT tables**
`result.insertId` only reflects the last generated AUTO_INCREMENT value. For
tables with composite or UUID primary keys, query the inserted row explicitly
to get its identifier. Relying on `insertId` for non-integer PKs silently
returns `0`.
Source: official mysql@2.18.1 README — Getting the id of an inserted row

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|------------|-----|
| Requests hang indefinitely under load | Pool exhausted, `queueLimit: 0`, no `acquireTimeout` | Set `acquireTimeout: 10000` and `queueLimit: 50`; alert on `enqueue` events |
| `Error: PROTOCOL_CONNECTION_LOST` | MySQL server closed idle connection (`wait_timeout`) | Use pool (auto-reconnects) or implement reconnect loop on `error` event |
| `Error: ER_LOCK_DEADLOCK (1213)` | Two transactions acquired locks in opposite order | Retry with exponential backoff; reorder queries to acquire locks consistently |
| Timestamps shifted by hours after deploy | `TIMESTAMP` columns affected by session `time_zone` | Set `timezone: 'Z'` in pool options; use `DATETIME` for timezone-agnostic storage |
| Memory spike during large `SELECT` | Full result set buffered in memory before callback | Switch to streaming query with `query.on('result')` and `pool.pause()`/`pool.resume()` |
| `Too many connections` error from MySQL server | `connectionLimit` × app instances > MySQL `max_connections` | Calculate `connectionLimit = floor((max_connections - 10) / instance_count)` |

## Pre-Deploy Checklist

- [ ] `connectionLimit` calculated: `floor((mysql_max_connections - 10) / instance_count)`
- [ ] `acquireTimeout` and `queueLimit` set to finite values — no silent request queuing
- [ ] All user inputs passed via `?` placeholders or `mysql.escape()` — zero string interpolation
- [ ] Every `pool.getConnection()` call has a matching `conn.release()` in all branches including error/rollback
- [ ] `slow_query_log` enabled with `long_query_time ≤ 1` and persisted in `mysqld.cnf`
- [ ] `EXPLAIN` run on every query touching tables > 10k rows — no `type: ALL` in output
- [ ] `timezone: 'Z'` set in pool options if app stores or reads datetime values