---
name: cloudflare-workers
description: "Build, deploy, and harden Cloudflare Workers for production. Use when asked to: create a Cloudflare Worker with routing, add rate limiting to a Worker, implement retry logic with exponential backoff in a Worker, handle errors and classify failures in a Worker, set up KV storage or Durable Objects, proxy requests through Cloudflare Workers, monitor Worker performance and log errors, make Workers idempotent and safe to retry."
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: devops
  tags: [cloudflare-workers, hono, edge-computing, rate-limiting, retry, idempotency, kv-storage, production]
---

# Cloudflare Workers Skill

## Quick Start

```bash
npm create cloudflare@latest my-worker
cd my-worker
npm run dev
```

```typescript
// src/index.ts — minimal Worker with typed env bindings
export interface Env {
  MY_KV: KVNamespace;
  API_SECRET: string;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname === '/health') {
      return Response.json({ status: 'ok', ts: Date.now() });
    }
    return new Response('Not Found', { status: 404 });
  },
};
```

## When to Use

Use this skill when asked to:
- Create or scaffold a new Cloudflare Worker from scratch
- Add request routing to a Worker (multi-path, wildcard, path params)
- Implement rate limiting or throttling at the edge
- Add retry logic with exponential backoff for upstream calls
- Classify and handle errors (4xx vs 5xx, transient vs permanent)
- Cache or store data with Workers KV or Durable Objects
- Set up structured logging and production monitoring for Workers
- Make Worker endpoints idempotent and safe for client retries

## Core Patterns

### Pattern 1: Production Router with Hono (Source: official)

Hono is the recommended framework for multi-route Workers. It uses `RegExpRouter` for zero-linear-scan matching and runs natively on the Workers runtime with no polyfills needed.

```typescript
// src/index.ts
import { Hono } from 'hono';
import { logger } from 'hono/logger';
import { secureHeaders } from 'hono/secure-headers';

export interface Env {
  KV: KVNamespace;
  RATE_LIMIT_KV: KVNamespace;
  API_SECRET: string;
}

const app = new Hono<{ Bindings: Env }>();

// Global middleware — executes on every request
app.use('*', logger());
app.use('*', secureHeaders());

// Auth guard middleware
app.use('/api/*', async (c, next) => {
  const token = c.req.header('Authorization')?.replace('Bearer ', '');
  if (token !== c.env.API_SECRET) {
    return c.json({ error: 'Unauthorized' }, 401);
  }
  await next();
});

app.get('/api/items/:id', async (c) => {
  const id = c.req.param('id');
  const value = await c.env.KV.get(`item:${id}`, 'json');
  if (!value) return c.json({ error: 'Not found' }, 404);
  return c.json(value);
});

app.onError((err, c) => {
  console.error({ path: c.req.path, error: err.message, stack: err.stack });
  return c.json({ error: 'Internal Server Error' }, 500);
});

app.notFound((c) => c.json({ error: 'Route not found' }, 404));

export default app;
```

### Pattern 2: Idempotent Writes with KV Deduplication (Source: official)

Use an idempotency key (client-supplied or derived from content hash) stored in KV to prevent duplicate side effects when clients retry POST requests.

```typescript
// Source: Cloudflare Workers KV docs — https://developers.cloudflare.com/kv/
import { Hono } from 'hono';

export interface Env {
  IDEMPOTENCY_KV: KVNamespace;
  ORDERS_KV: KVNamespace;
}

const app = new Hono<{ Bindings: Env }>();

const IDEMPOTENCY_TTL_SECONDS = 86400; // 24 hours

app.post('/api/orders', async (c) => {
  const idempotencyKey = c.req.header('Idempotency-Key');
  if (!idempotencyKey) {
    return c.json({ error: 'Idempotency-Key header required' }, 400);
  }

  // Check for a cached response from a prior identical request
  const cached = await c.env.IDEMPOTENCY_KV.get(
    `idem:${idempotencyKey}`,
    'json'
  ) as { status: number; body: unknown } | null;

  if (cached) {
    // Return exactly the same response — safe to retry
    return c.json(cached.body, cached.status as 200);
  }

  // Process the new request
  const body = await c.req.json();
  const orderId = crypto.randomUUID();
  const order = { id: orderId, ...body, createdAt: Date.now() };

  await c.env.ORDERS_KV.put(`order:${orderId}`, JSON.stringify(order));

  const responsePayload = { id: orderId, status: 'created' };

  // Persist response so retries get the same answer
  await c.env.IDEMPOTENCY_KV.put(
    `idem:${idempotencyKey}`,
    JSON.stringify({ status: 200, body: responsePayload }),
    { expirationTtl: IDEMPOTENCY_TTL_SECONDS }
  );

  return c.json(responsePayload, 200);
});

export default app;
```

### Pattern 3: Exponential Backoff with Jitter for Upstream Calls (Source: official)

Workers have a 30-second CPU wall-clock limit per request. Use bounded retries with full jitter to avoid thundering-herd on upstream services.

```typescript
// Retry helper — safe for Cloudflare Workers (no Node.js APIs)
interface RetryOptions {
  maxAttempts?: number;      // default 3
  baseDelayMs?: number;      // default 200
  maxDelayMs?: number;       // default 5000
  retryableStatuses?: number[]; // default [429, 502, 503, 504]
}

class UpstreamError extends Error {
  constructor(
    public readonly status: number,
    public readonly body: string,
    public readonly isTransient: boolean
  ) {
    super(`Upstream ${status}: ${body}`);
    this.name = 'UpstreamError';
  }
}

async function fetchWithRetry(
  url: string,
  init: RequestInit,
  options: RetryOptions = {}
): Promise<Response> {
  const {
    maxAttempts = 3,
    baseDelayMs = 200,
    maxDelayMs = 5000,
    retryableStatuses = [429, 502, 503, 504],
  } = options;

  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const response = await fetch(url, init);

      if (response.ok) return response;

      const isTransient = retryableStatuses.includes(response.status);
      const body = await response.text();

      if (!isTransient || attempt === maxAttempts) {
        throw new UpstreamError(response.status, body, isTransient);
      }

      lastError = new UpstreamError(response.status, body, true);

      // Honour Retry-After header if present (e.g., from rate-limiting proxies)
      const retryAfter = response.headers.get('Retry-After');
      const serverDelay = retryAfter ? parseInt(retryAfter, 10) * 1000 : null;

      // Full jitter: sleep between 0 and cap(base * 2^attempt)
      const exponential = Math.min(baseDelayMs * 2 ** attempt, maxDelayMs);
      const jittered = serverDelay ?? Math.random() * exponential;

      await new Promise((r) => setTimeout(r, jittered));
    } catch (err) {
      if (err instanceof UpstreamError && !err.isTransient) throw err;
      lastError = err as Error;
      if (attempt === maxAttempts) throw lastError;
    }
  }

  throw lastError!;
}

// Usage inside a Worker handler
export default {
  async fetch(request: Request): Promise<Response> {
    try {
      const upstream = await fetchWithRetry(
        'https://api.example.com/data',
        { method: 'GET', headers: { Authorization: 'Bearer token' } },
        { maxAttempts: 3, baseDelayMs: 300 }
      );
      return new Response(upstream.body, { status: 200 });
    } catch (err) {
      if (err instanceof UpstreamError) {
        const status = err.isTransient ? 503 : err.status;
        return Response.json({ error: err.message }, { status });
      }
      return Response.json({ error: 'Unexpected failure' }, { status: 500 });
    }
  },
};
```

### Pattern 4: Token-Bucket Rate Limiting with KV (Source: official)

```typescript
// Source: Cloudflare Workers KV docs — sliding-window approximation
// https://developers.cloudflare.com/workers/runtime-apis/kv/

export interface Env {
  RATE_LIMIT_KV: KVNamespace;
}

interface RateLimitState {
  tokens: number;
  lastRefillTs: number;
}

async function checkRateLimit(
  kv: KVNamespace,
  key: string,
  limitPerMinute: number
): Promise<{ allowed: boolean; remaining: number; resetIn: number }> {
  const now = Date.now();
  const windowMs = 60_000;
  const refillRate = limitPerMinute / windowMs; // tokens per ms

  const raw = await kv.get<RateLimitState>(`rl:${key}`, 'json');
  const state: RateLimitState = raw ?? { tokens: limitPerMinute, lastRefillTs: now };

  // Refill tokens proportional to elapsed time
  const elapsed = now - state.lastRefillTs;
  const refilled = Math.min(limitPerMinute, state.tokens + elapsed * refillRate);
  const resetIn = Math.ceil((1 - (refilled % 1)) / refillRate);

  if (refilled < 1) {
    return { allowed: false, remaining: 0, resetIn };
  }

  const updated: RateLimitState = { tokens: refilled - 1, lastRefillTs: now };
  // TTL slightly longer than window to avoid stale keys accumulating
  await kv.put(`rl:${key}`, JSON.stringify(updated), { expirationTtl: 120 });

  return { allowed: true, remaining: Math.floor(updated.tokens), resetIn };
}

// Middleware for Hono
import { Hono } from 'hono';
const app = new Hono<{ Bindings: Env }>();

app.use('/api/*', async (c, next) => {
  const ip = c.req.header('CF-Connecting-IP') ?? 'unknown';
  const { allowed, remaining, resetIn } = await checkRateLimit(
    c.env.RATE_LIMIT_KV,
    ip,
    100 // 100 req/min per IP
  );

  c.header('X-RateLimit-Limit', '100');
  c.header('X-RateLimit-Remaining', String(remaining));
  c.header('X-RateLimit-Reset', String(Math.ceil(Date.now() / 1000) + resetIn));

  if (!allowed) {
    return c.json({ error: 'Too Many Requests' }, 429);
  }
  await next();
});

export default app;
```

### Pattern 5: Structured Error Classification and Logging (Source: community)

Real issue pattern: unclassified errors from Hono's `onError` produce inconsistent status codes and no correlation IDs, making production debugging impossible.
Source: GitHub Issues (honojs/hono — multiple error-handling issues)

```typescript
// Source: community / Tested: SharpSkill
// Canonical error taxonomy for Workers

enum ErrorCode {
  VALIDATION    = 'VALIDATION_ERROR',      // 400 — never retry
  UNAUTHORIZED  = 'UNAUTHORIZED',          // 401 — never retry
  NOT_FOUND     = 'NOT_FOUND',             // 404 — never retry
  RATE_LIMITED  = 'RATE_LIMITED',          // 429 — retry with backoff
  UPSTREAM_DOWN = 'UPSTREAM_UNAVAILABLE',  // 503 — retry with backoff
  INTERNAL      = 'INTERNAL_ERROR',        // 500 — investigate
}

interface ErrorResponse {
  error: ErrorCode;
  message: string;
  requestId: string;
  retryable: boolean;
}

function classifyError(err: unknown): { code: ErrorCode; status: number; retryable: boolean } {
  if (err instanceof UpstreamError) {
    return err.isTransient
      ? { code: ErrorCode.UPSTREAM_DOWN, status: 503, retryable: true }
      : { code: ErrorCode.INTERNAL, status: 502, retryable: false };
  }
  if (err instanceof TypeError && (err as TypeError).message.includes('body')) {
    // Disturbed/locked body — common in streaming proxies (see Production Notes)
    return { code: ErrorCode.INTERNAL, status: 500, retryable: false };
  }
  return { code: ErrorCode.INTERNAL, status: 500, retryable: false };
}

import { Hono } from 'hono';
const app = new Hono();

app.onError((err, c) => {
  const requestId = c.req.header('CF-Ray') ?? crypto.randomUUID();
  const { code, status, retryable } = classifyError(err);

  // Structured log — visible in Workers Logs / Logpush
  console.error(JSON.stringify({
    level: 'error',
    requestId,
    code,
    status,
    path: c.req.path,
    method: c.req.method,
    message: err instanceof Error ? err.message : String(err),
    stack: err instanceof Error ? err.stack : undefined,
    retryable,
  }));

  const body: ErrorResponse = {
    error: code,
    message: status < 500 ? (err instanceof Error ? err.message : 'Request error') : 'Internal error',
    requestId,
    retryable,
  };

  return c.json(body, status as 400 | 401 | 404 | 429 | 500 | 502 | 503);
});

export default app;
```

### Pattern 6: Background Tasks with waitUntil (Source: official)

`ctx.waitUntil` keeps the Worker alive after sending the response for fire-and-forget logging, cache warming, or analytics writes. Do NOT `await` inside the main handler.

```typescript
export interface Env {
  ANALYTICS_KV: KVNamespace;
}

async function recordAnalytics(kv: KVNamespace, event: Record<string, unknown>) {
  const key = `evt:${Date.now()}:${crypto.randomUUID()}`;
  await kv.put(key, JSON.stringify(event), { expirationTtl: 7 * 86400 });
}

export default {
  async fetch(request: Request