---
name: redis
description: "Production-grade Redis client patterns for Node.js and Python. Use when asked to: configure Redis connection pools, handle pool exhaustion, set up Redis Cluster with sharding, avoid hot key bottlenecks, configure memory eviction policies to prevent OOM, harden Redis with TLS and ACL authentication, pipeline or batch commands for throughput, implement cache-aside or write-through patterns with TTL management."
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: database
  tags: [redis, caching, connection-pool, cluster, eviction, tls, acl, node-redis, redis-py]
trace_id: 3dead6815258
generated_at: '2026-02-28T22:43:31'
generator: sharpskill-v1.0 (legacy)
---

# Redis Skill

## Quick Start

```bash
# Node.js
npm install redis

# Python
pip install "redis[hiredis]"
```

```typescript
// Node.js — minimal verified connection (node-redis@5)
import { createClient } from 'redis';

const client = await createClient({ url: 'redis://localhost:6379' })
  .on('error', (err) => console.error('Redis error:', err))
  .connect();

await client.set('hello', 'world', { EX: 60 });
const val = await client.get('hello');
console.log(val); // 'world'
await client.quit();
```

```python
# Python — minimal verified connection (redis-py@7)
import redis

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
r.set('hello', 'world', ex=60)
print(r.get('hello'))  # 'world'
```

## When to Use

Use this skill when asked to:
- Configure or tune Redis connection pool size and handle exhaustion errors
- Set up Redis Cluster mode with hash slot sharding
- Diagnose or resolve hot key problems causing latency spikes
- Choose or change memory eviction policies (`maxmemory-policy`) to prevent OOM kills
- Secure Redis with TLS encryption and ACL-based user authentication
- Pipeline multiple commands to reduce round-trip latency
- Implement distributed locks, rate limiting, or session storage on Redis
- Monitor Redis memory usage, keyspace hits/misses, and connected clients

---

## Core Patterns

### Pattern 1: Connection Pool Sizing and Exhaustion Handling (Source: official)

Node-redis uses a socket pool internally. The `socket` options control reconnect behavior; for explicit pool limits use a pooled client factory or limit concurrency at the application layer. Redis-py exposes `ConnectionPool` directly.

```typescript
// Node.js — bounded concurrency with a single multiplexed client
// node-redis pipelines commands over one connection by default.
// For CPU-bound parallelism, create a dedicated pool wrapper.
import { createClient } from 'redis';
import Bottleneck from 'bottleneck'; // npm install bottleneck

const client = await createClient({
  url: 'redis://localhost:6379',
  socket: {
    reconnectStrategy: (retries) => {
      if (retries > 10) return new Error('Max reconnect attempts reached');
      return Math.min(retries * 100, 3000); // exponential backoff, max 3 s
    },
    connectTimeout: 5000,
  },
})
  .on('error', (err) => console.error('Pool error:', err))
  .connect();

// Limit in-flight commands to avoid overwhelming the server
const limiter = new Bottleneck({ maxConcurrent: 50, minTime: 0 });
const safeGet = (key: string) => limiter.schedule(() => client.get(key));
```

```python
# Python — explicit ConnectionPool with max_connections cap
# Source: https://redis.readthedocs.io/en/stable/connections.html
import redis

pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    db=0,
    max_connections=20,          # hard cap; raises ConnectionError when exhausted
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
)
r = redis.Redis(connection_pool=pool)

# Detect pool exhaustion
from redis.exceptions import ConnectionError as RedisConnectionError
try:
    val = r.get('key')
except RedisConnectionError as exc:
    print(f'Pool exhausted or unreachable: {exc}')
    # Back off and retry or return cached/fallback value
```

---

### Pattern 2: Redis Cluster — Sharding and Hot Key Mitigation (Source: official)

```typescript
// Node.js — RedisCluster client (node-redis@5)
// Source: https://github.com/redis/node-redis/blob/master/docs/clustering.md
import { createCluster } from 'redis';

const cluster = await createCluster({
  rootNodes: [
    { url: 'redis://node1:6379' },
    { url: 'redis://node2:6379' },
    { url: 'redis://node3:6379' },
  ],
  defaults: {
    socket: { reconnectStrategy: (r) => Math.min(r * 150, 5000) },
  },
  useReplicas: true, // route read commands to replicas
}).connect();

// Hash tags force co-location: {user}.profile and {user}.sessions
// land on the same slot — use sparingly to avoid hot slots.
await cluster.set('{user:42}.profile', JSON.stringify({ name: 'Alice' }));
await cluster.set('{user:42}.sessions', '3');

// Hot key mitigation: fan out reads across local in-process cache
import NodeCache from 'node-cache'; // npm install node-cache
const localCache = new NodeCache({ stdTTL: 1 }); // 1-second local TTL

async function getWithLocalFallback(key: string): Promise<string | null> {
  const hit = localCache.get<string>(key);
  if (hit !== undefined) return hit;
  const val = await cluster.get(key);
  if (val !== null) localCache.set(key, val);
  return val;
}
```

```python
# Python — RedisCluster with replica reads
# Source: https://redis.readthedocs.io/en/stable/clustering.html
from redis.cluster import RedisCluster, ClusterNode

startup_nodes = [
    ClusterNode('node1', 6379),
    ClusterNode('node2', 6379),
    ClusterNode('node3', 6379),
]
rc = RedisCluster(
    startup_nodes=startup_nodes,
    decode_responses=True,
    read_from_replicas=True,   # distribute reads; stale data possible
    skip_full_coverage_check=False,
)

# Hot key: detect via OBJECT FREQ (LFU policy must be active)
freq = rc.object('freq', 'hot:leaderboard')
print(f'Access frequency estimate: {freq}')

# Mitigation: key sharding — append random suffix, read any shard
import random
SHARDS = 8
def set_sharded(base_key: str, value: str, ex: int = 300):
    for i in range(SHARDS):
        rc.set(f'{base_key}:{i}', value, ex=ex)

def get_sharded(base_key: str) -> str | None:
    shard = random.randint(0, SHARDS - 1)
    return rc.get(f'{base_key}:{shard}')
```

---

### Pattern 3: Memory Eviction Policies and OOM Prevention (Source: official)

```bash
# Redis server — set maxmemory and policy (redis.conf or CONFIG SET)
# Source: https://redis.io/docs/latest/develop/reference/eviction/

# Cap memory at 2 GB; evict LFU-least-used volatile keys first
CONFIG SET maxmemory 2gb
CONFIG SET maxmemory-policy allkeys-lfu

# Verify active config (no restart needed)
CONFIG GET maxmemory
CONFIG GET maxmemory-policy

# Policy cheat-sheet:
#   noeviction        — return error on write when full (default, dangerous in prod)
#   allkeys-lru       — evict any key by LRU (general-purpose cache)
#   volatile-lru      — evict only keys with TTL by LRU
#   allkeys-lfu       — evict any key by LFU (Redis >= 4, skewed access patterns)
#   volatile-ttl      — evict soonest-to-expire key first
#   allkeys-random    — random eviction (rarely appropriate)
```

```python
# Python — runtime detection and alerting before OOM
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)
info = r.info('memory')

used_mb   = info['used_memory'] / 1_048_576
maxmem_mb = info['maxmemory'] / 1_048_576 if info['maxmemory'] else None

if maxmem_mb and (used_mb / maxmem_mb) > 0.85:
    print(f'WARNING: Redis memory at {used_mb:.0f}/{maxmem_mb:.0f} MB '
          f'({100*used_mb/maxmem_mb:.1f}%) — consider scaling or eviction tuning')

# Enforce TTLs on every write to prevent key accumulation
r.set('session:abc', '{"uid":1}', ex=3600)   # always set ex= or px=
r.expire('legacy:key', 86400)                 # backfill TTL on existing keys
```

---

### Pattern 4: TLS Encryption and ACL Authentication Hardening (Source: official)

```typescript
// Node.js — TLS + ACL credentials
// Source: https://github.com/redis/node-redis/blob/master/docs/client-configuration.md
import { createClient } from 'redis';
import { readFileSync } from 'fs';

const client = await createClient({
  url: 'rediss://app-user:s3cr3t@redis.prod.internal:6380', // rediss:// = TLS
  socket: {
    tls: true,
    ca:   readFileSync('/etc/ssl/redis/ca.crt'),
    cert: readFileSync('/etc/ssl/redis/client.crt'),  // mutual TLS (optional)
    key:  readFileSync('/etc/ssl/redis/client.key'),
    rejectUnauthorized: true,  // never set false in production
  },
})
  .on('error', (err) => console.error('Secure client error:', err))
  .connect();
```

```bash
# Redis server — create ACL user with minimum privilege
# Source: https://redis.io/docs/latest/operate/oss_and_stack/management/security/acl/

# Allow app-user to read/write only cache:* keys, no admin commands
ACL SETUSER app-user on >s3cr3t ~cache:* &* +get +set +del +expire +ttl -@admin -@dangerous

# Read-only replica consumer
ACL SETUSER reader on >r3adonly ~reports:* &* +get +hgetall +lrange -@write -@admin

# Persist ACL rules to file (add to redis.conf)
# aclfile /etc/redis/users.acl

# Verify
ACL WHOAMI
ACL LIST
```

```python
# Python — TLS + ACL user authentication
import redis, ssl

r = redis.Redis(
    host='redis.prod.internal',
    port=6380,
    username='app-user',
    password='s3cr3t',
    decode_responses=True,
    ssl=True,
    ssl_ca_certs='/etc/ssl/redis/ca.crt',
    ssl_certfile='/etc/ssl/redis/client.crt',   # mutual TLS
    ssl_keyfile='/etc/ssl/redis/client.key',
    ssl_cert_reqs=ssl.CERT_REQUIRED,            # enforce server cert validation
)
r.ping()  # raises AuthenticationError if credentials are wrong
```

---

### Pattern 5: Pipelining for Throughput (Source: official)

```typescript
// Node.js — pipeline (batches commands, one round-trip)
// Source: https://github.com/redis/node-redis/blob/master/docs/pipelining.md
const pipeline = client.multi();
for (let i = 0; i < 1000; i++) {
  pipeline.set(`key:${i}`, `val:${i}`, { EX: 300 });
}
const results = await pipeline.exec(); // all-or-nothing MULTI/EXEC transaction
// For fire-and-forget batching without MULTI semantics use client.pipeline()
```

```python
# Python — pipeline without MULTI for bulk writes (Source: official redis-py docs)
with r.pipeline(transaction=False) as pipe:   # transaction=False = plain pipeline
    for i in range(1000):
        pipe.set(f'key:{i}', f'val:{i}', ex=300)
    pipe.execute()  # single round-trip for all 1000 commands

# With MULTI/EXEC atomic transaction
with r.pipeline(transaction=True) as pipe:
    while True:
        try:
            pipe.watch('inventory:42')          # optimistic lock
            stock = int(pipe.get('inventory:42') or 0)
            if stock < 1:
                pipe.reset()
                raise ValueError('Out of stock')
            pipe.multi()
            pipe.decr('inventory:42')
            pipe.execute()
            break
        except redis.WatchError:
            continue                            # retry on concurrent modification
```

---

### Pattern 6: Error Handling and Reconnection (Source: community)

```typescript
// Source: community — common pattern for resilient clients
// Tested: SharpSkill
import { createClient, commandOptions } from 'redis';

let isReady = false;
const client = createClient({
  url: process.env.REDIS_URL,
  socket: {
    reconnectStrategy: (retries, cause) => {
      console.warn(`Reconnect attempt ${retries}`, cause?.message);
      if (retries > 20) {
        console.error('Giving up on Redis reconnection');
        return false; // stop reconnecting
      }
      return Math.min(200 * 2 ** retries, 10_000); // cap at 10 s
    },
  },
});

client.on('ready',        () => { isReady = true;  console.log('Redis ready'); });
client.on('end',          () => { isReady = false; console.warn('Redis disconnected'); });
client.on('error',        (e) => console.error('Redis error', e));
client.on('reconnecting', () => console.info('Redis reconnecting…'));

await client.connect();

// Guard all commands behind readiness check
async function safeGet(key: string): Promise<string | null> {
  if (!isReady) return null;  // degrade gracefully, don't throw
  try {
    return await client.get(
      commandOptions({ isolated: true }),  // run on separate connection, won't block pub/sub
      key
    );
  } catch (err) {
    console.error(`safeGet(${key}) failed:`, err);
    return null;
  }
}
```

---

## Production Notes

**1. Pool exhaustion causes `ConnectionError: Too many connections` (Python)**
Exceeding `max_connections` raises `redis.exceptions.ConnectionError` synchronously — not a timeout. The fix is twofold: raise `max_connections` proportional to worker count (`workers × avg_concurrent_queries + 10% headroom`) and add `socket_timeout` so stalled connections are released. Without `socket_timeout`, idle connections from crashed threads stay in the pool indefinitely.
Source: SO (multiple reports) / redis-py GitHub Issues

**2. `noeviction` policy causes write errors under load — not a safe default**
Redis ships with `maxmemory-policy noeviction`. Under memory pressure every write returns `OOM command not allowed when used memory > 'maxmemory'`. This surfaces as application exceptions, not just slow responses. Always explicitly set a policy matching your data access pattern before reaching production.
Source: SO question (693v, "MISCONF Redis is configured to