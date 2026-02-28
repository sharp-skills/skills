---
name: postgresql
description: "Production-depth PostgreSQL operations skill covering connection pooling with PgBouncer, VACUUM and table bloat management, replication lag monitoring, table partitioning strategies, and failover handling. Use when asked to: configure PgBouncer connection pooling, manage autovacuum and bloat, set up streaming replication, monitor replication lag, partition large tables, handle primary failover, tune PostgreSQL for production, or diagnose slow queries and index bloat."
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: database
  tags: [postgresql, pgbouncer, replication, partitioning, vacuum, production, devops]
---

# PostgreSQL Production Skill

## Quick Start

```bash
# Install PostgreSQL 16 on Ubuntu/Debian (official apt method)
sudo apt install -y postgresql-common
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh
sudo apt install -y postgresql-16

# Connect and verify
sudo -u postgres psql -c "SELECT version();"

# Create a production role + database with least privilege
sudo -u postgres psql <<'SQL'
CREATE ROLE appuser WITH LOGIN PASSWORD 'strongpassword';
CREATE DATABASE appdb OWNER appuser;
GRANT CONNECT ON DATABASE appdb TO appuser;
SQL
```

## When to Use

Use this skill when asked to:
- Configure PgBouncer connection pooling for high-concurrency workloads
- Manage autovacuum, manual VACUUM, and table bloat
- Set up streaming replication between primary and standby
- Monitor replication lag and trigger failover with pg_ctl or Patroni
- Partition large tables by range, list, or hash
- Tune `postgresql.conf` for production memory and I/O
- Diagnose and fix index bloat with `pg_stat_user_indexes`
- Handle `too many connections` errors at scale
- Identify long-running queries and lock contention
- Implement logical replication for zero-downtime migrations

---

## Core Patterns

### Pattern 1: PgBouncer Connection Pooling (Source: official)

PgBouncer sits between the application and PostgreSQL, multiplexing thousands of client connections into a small pool. Use **transaction mode** for stateless apps; **session mode** if you use `SET LOCAL`, advisory locks, or prepared statements.

```ini
# /etc/pgbouncer/pgbouncer.ini — production-grade config
[databases]
appdb = host=127.0.0.1 port=5432 dbname=appdb

[pgbouncer]
listen_addr         = 0.0.0.0
listen_port         = 6432
auth_type           = scram-sha-256
auth_file           = /etc/pgbouncer/userlist.txt

# Transaction pooling — safest for stateless web apps
pool_mode           = transaction

# Max server connections PgBouncer opens to Postgres
max_client_conn     = 5000
default_pool_size   = 25        # per database+user pair
reserve_pool_size   = 5
reserve_pool_timeout = 3

# Prevent idle connections accumulating on Postgres side
server_idle_timeout = 600
client_idle_timeout = 0

# TLS to Postgres
server_tls_sslmode  = require
log_connections     = 0         # disable in prod to reduce I/O
log_disconnections  = 0
```

```bash
# userlist.txt — use md5 or scram hashes, never plaintext
# Generate hash: psql -c "SELECT concat('md5', md5('password' || 'appuser'));"
echo '"appuser" "md5<hash>"' > /etc/pgbouncer/userlist.txt

# Start and verify pool stats
pgbouncer -d /etc/pgbouncer/pgbouncer.ini
psql -p 6432 -U pgbouncer pgbouncer -c "SHOW POOLS;"
```

```sql
-- Validate from Postgres side: connections should be small
SELECT count(*), state, wait_event_type
FROM pg_stat_activity
WHERE datname = 'appdb'
GROUP BY state, wait_event_type;
```

---

### Pattern 2: VACUUM and Bloat Management (Source: official)

Dead tuples accumulate from UPDATE/DELETE and block index-only scans. Autovacuum defaults are conservative — production tables need explicit tuning per-table.

```sql
-- Identify bloated tables (requires pgstattuple or estimation query)
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    n_dead_tup,
    n_live_tup,
    ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_pct,
    last_autovacuum,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE n_dead_tup > 10000
ORDER BY dead_pct DESC;

-- Identify bloated indexes
SELECT
    schemaname,
    relname AS tablename,
    indexrelname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC
LIMIT 20;
```

```sql
-- Tune autovacuum aggressively for a high-churn table
ALTER TABLE orders SET (
    autovacuum_vacuum_scale_factor    = 0.01,  -- trigger at 1% dead tuples
    autovacuum_analyze_scale_factor   = 0.005,
    autovacuum_vacuum_cost_delay      = 2,     -- ms; lower = faster vacuum
    autovacuum_vacuum_threshold       = 100
);

-- For a table that cannot afford autovacuum pauses, run manually
-- during low-traffic windows:
VACUUM (VERBOSE, ANALYZE, PARALLEL 4) orders;

-- VACUUM FULL reclaims disk space but takes AccessExclusiveLock.
-- Use pg_repack (extension) for online bloat removal instead:
-- pg_repack -d appdb -t orders
```

```sql
-- Monitor autovacuum workers in flight
SELECT pid, datname, relid::regclass, phase, heap_blks_scanned,
       heap_blks_total, index_vacuum_count, num_dead_tuples
FROM pg_stat_progress_vacuum;
```

---

### Pattern 3: Streaming Replication Setup (Source: official)

```bash
# On PRIMARY — postgresql.conf
wal_level           = replica
max_wal_senders     = 5
wal_keep_size       = 1024          # MB; retain WAL for slow standbys
hot_standby         = on
synchronous_commit  = on            # set to 'remote_apply' for zero data loss

# Create replication role
psql -U postgres -c "CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'rep_secret';"

# pg_hba.conf — allow standby to connect
echo "host replication replicator <standby_ip>/32 scram-sha-256" >> /etc/postgresql/16/main/pg_hba.conf
pg_ctlcluster 16 main reload
```

```bash
# On STANDBY — initial base backup
pg_basebackup \
  -h <primary_ip> -U replicator \
  -D /var/lib/postgresql/16/main \
  -P -R -Xs -C -S standby1_slot    # -R writes standby.signal + postgresql.auto.conf
                                    # -C creates replication slot

# Verify standby started and is streaming
psql -U postgres -c "SELECT * FROM pg_stat_replication;"
# Look for: state = 'streaming', sent_lsn ≈ write_lsn ≈ flush_lsn ≈ replay_lsn
```

---

### Pattern 4: Replication Lag Monitoring and Failover (Source: official)

```sql
-- On PRIMARY: measure lag in bytes and time
SELECT
    application_name,
    client_addr,
    state,
    sent_lsn,
    write_lsn,
    flush_lsn,
    replay_lsn,
    (sent_lsn - replay_lsn)               AS lag_bytes,
    write_lag,
    flush_lag,
    replay_lag
FROM pg_stat_replication
ORDER BY replay_lag DESC NULLS LAST;

-- On STANDBY: check local lag
SELECT now() - pg_last_xact_replay_timestamp() AS replication_lag;
SELECT pg_is_in_recovery();   -- must return true on standby
```

```bash
# Manual failover with pg_ctl (no orchestration layer)
# 1. Confirm primary is truly down — avoid split-brain
ssh primary "pg_ctlcluster 16 main status" || true

# 2. Promote standby
pg_ctlcluster 16 main promote
# OR: touch /var/lib/postgresql/16/main/promote.signal

# 3. Verify promotion
psql -U postgres -c "SELECT pg_is_in_recovery();"  -- must return false

# Patroni-based failover (preferred for automated HA)
patronictl -c /etc/patroni/config.yml failover <cluster_name> \
  --master <old_primary> --candidate <standby_name> --force
```

```bash
# Replication slot — prevent WAL deletion before standby catches up
-- WARNING: unmonitored slots cause disk exhaustion if standby falls behind
SELECT slot_name, active, pg_size_pretty(
    pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)
) AS retained_wal
FROM pg_replication_slots;

-- Drop a stuck slot to free WAL (only after confirming standby is gone)
SELECT pg_drop_replication_slot('standby1_slot');
```

---

### Pattern 5: Declarative Table Partitioning (Source: official)

```sql
-- Range partitioning by date — partition pruning eliminates irrelevant partitions
CREATE TABLE events (
    id          BIGSERIAL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_id     BIGINT,
    event_type  TEXT,
    payload     JSONB
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE events_2025_01 PARTITION OF events
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE events_2025_02 PARTITION OF events
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Default partition catches out-of-range inserts (avoids errors)
CREATE TABLE events_default PARTITION OF events DEFAULT;

-- Indexes are created per-partition; create on parent and Postgres propagates
CREATE INDEX ON events (created_at, user_id);

-- Verify pruning with EXPLAIN
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM events
WHERE created_at BETWEEN '2025-01-15' AND '2025-01-20';
-- Look for: "Partitions selected: 1" in output
```

```sql
-- Hash partitioning for even distribution (e.g., user_id sharding)
CREATE TABLE user_sessions (
    session_id  UUID DEFAULT gen_random_uuid(),
    user_id     BIGINT NOT NULL,
    data        JSONB
) PARTITION BY HASH (user_id);

CREATE TABLE user_sessions_0 PARTITION OF user_sessions
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE user_sessions_1 PARTITION OF user_sessions
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE user_sessions_2 PARTITION OF user_sessions
    FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE user_sessions_3 PARTITION OF user_sessions
    FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- Attach an existing table as a new partition (zero-downtime migration)
ALTER TABLE events ATTACH PARTITION events_2025_03
    FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');
```

---

### Pattern 6: Production postgresql.conf Tuning (Source: official)

```ini
# Memory — set based on available RAM (example: 32 GB server)
shared_buffers          = 8GB           # 25% of RAM
effective_cache_size    = 24GB          # 75% of RAM (planner hint)
work_mem                = 64MB          # per sort/hash; watch for OOM on parallel queries
maintenance_work_mem    = 2GB           # for VACUUM, CREATE INDEX

# WAL and checkpoints
wal_buffers             = 64MB
checkpoint_completion_target = 0.9
max_wal_size            = 4GB
min_wal_size            = 1GB

# Parallelism
max_worker_processes    = 16
max_parallel_workers_per_gather = 4
max_parallel_workers    = 8

# I/O — use 1 for SSD, keep default (2) for spinning disk
random_page_cost        = 1.1
effective_io_concurrency = 200

# Connections
max_connections         = 100           # keep low; use PgBouncer
superuser_reserved_connections = 3

# Logging for slow-query analysis
log_min_duration_statement = 500        # ms; log queries slower than 500ms
log_lock_waits          = on
log_checkpoints         = on
log_temp_files          = 0
deadlock_timeout        = 1s
```

---

### Pattern 7: Long-Running Query and Lock Monitoring (Source: official)

```sql
-- Find queries running longer than 30 seconds
SELECT pid, now() - query_start AS duration, state, wait_event_type,
       wait_event, left(query, 100) AS query_snippet
FROM pg_stat_activity
WHERE state != 'idle'
  AND query_start < now() - interval '30 seconds'
ORDER BY duration DESC;

-- Find blocking lock chains
SELECT
    blocked.pid                     AS blocked_pid,
    blocked_activity.query          AS blocked_query,
    blocking.pid                    AS blocking_pid,
    blocking_activity.query         AS blocking_query,
    now() - blocked_activity.query_start AS wait_duration
FROM pg_locks blocked
JOIN pg_stat_activity blocked_activity ON blocked.pid = blocked_activity.pid
JOIN pg_locks blocking
    ON blocking.granted = true
   AND blocked.relation = blocking.relation
   AND blocked.pid != blocking.pid
JOIN pg_stat_activity blocking_activity ON blocking.pid = blocking_activity.pid
WHERE NOT blocked.granted;

-- Terminate a specific blocking query safely
SELECT pg_terminate_backend(<blocking_pid>);
-- pg_cancel_backend sends SIGINT (softer — cancels query, keeps connection)
SELECT pg_cancel_backend(<pid>);
```

---

### Pattern 8: Error Handling — SASL / Authentication Failures (Source: community)

Real scenario: `SASL_SIGNATURE_MISMATCH` or `Peer authentication failed` errors block all connections.
<!-- Source: community / GitHub Issues supabase/supabase #51-comment thread -->

```bash
# Peer auth failure: pg_hba.conf uses 'peer' for local socket but app sends password
# Fix: change method to scram-sha-256 for the specific database+role

# /etc/postgresql/16/main/pg_hba.conf
# TYPE  DATABASE  USER     ADDRESS    METHOD
local   appdb     appuser              scram-sha-256   # was: peer
host    appdb     appuser  127.0.0.1/32 scram-sha-256

sudo pg_ctlcluster 16 main reload

# SASL_SIGNATURE_MISMATCH — usually means password was set with md5
# but pg_hba.conf requires scram-sha-256, or vice versa.
# Fix: reset password while server uses correct hash method:
psql -U postgres -c "SET password_encryption = '