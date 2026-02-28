---
name: upstash
description: >-
  Assists with building serverless applications using Upstash Redis, QStash, Workflow, and Vector.
  Use when adding caching, rate limiting, message queues, durable workflows, or vector search
  to edge and serverless applications. Trigger words: upstash, serverless redis, rate limiting,
  qstash, upstash workflow, upstash vector.
license: Apache-2.0
compatibility: "Works in all serverless and edge runtimes via HTTP-based APIs"
metadata:
  author: terminal-skills
  version: "1.0.0"
  category: data-ai
  tags: ["upstash", "redis", "serverless", "rate-limiting", "message-queue"]
---

# Upstash

## Overview

Upstash provides serverless Redis, message queues (QStash), durable workflows, and vector databases via HTTP-based APIs that work in edge runtimes where TCP connections are unavailable. It offers pay-per-request pricing with scale-to-zero, making it ideal for Cloudflare Workers, Vercel Edge Functions, and Deno Deploy.

## Instructions

- When setting up Redis, use `Redis.fromEnv()` to read connection credentials from environment variables, and use `pipeline()` for batching 3+ commands into a single HTTP request.
- When implementing rate limiting, use `@upstash/ratelimit` with the appropriate algorithm (fixed window, sliding window, or token bucket) and custom identifiers (IP, API key, user ID).
- When adding caching, use `@upstash/cache` with stale-while-revalidate patterns and set explicit TTLs on all cached data to prevent unbounded growth.
- When building async task processing, use QStash (`@upstash/qstash`) to publish messages to URL endpoints with automatic retries, exponential backoff, and dead letter queues.
- When creating multi-step workflows, use `@upstash/workflow` to break long tasks into resumable steps that can span multiple serverless invocations, with `context.sleep()` for delays.
- When adding AI/RAG features, use `@upstash/vector` for serverless vector storage with metadata filtering and namespace support for multi-tenant applications.
- When configuring for global read performance, enable Redis read replicas in multiple regions; writes always go to the primary region.

## Examples

### Example 1: Add rate limiting to an API

**User request:** "Implement rate limiting for my API endpoints on Vercel Edge"

**Actions:**
1. Install `@upstash/ratelimit` and `@upstash/redis`
2. Create a rate limiter with sliding window algorithm (e.g., 10 requests per 10 seconds)
3. Identify requests by IP address or API key
4. Return 429 status with retry-after header when limit is exceeded

**Output:** Production-ready rate limiting that works across edge locations with consistent enforcement.

### Example 2: Build a durable email workflow

**User request:** "Create a multi-step onboarding email sequence using serverless functions"

**Actions:**
1. Define workflow steps with `@upstash/workflow` for each email in the sequence
2. Use `context.sleep("wait-24h", 86400)` between emails without holding compute
3. Add conditional logic for user engagement tracking between steps
4. Configure automatic retries on step failure

**Output:** A durable workflow that sends timed emails across days, surviving serverless timeouts and restarts.

## Guidelines

- Always use `Redis.fromEnv()`; never hardcode connection URLs in source code.
- Use `pipeline()` when executing 3+ Redis commands to reduce HTTP round trips.
- Set explicit TTLs on all cached data; unbounded caches grow until they hit memory limits.
- Use `@upstash/ratelimit` over hand-rolled rate limiting; it handles race conditions and multi-region consistency.
- Prefer QStash over direct HTTP calls for async tasks; it handles retries, timeouts, and dead letters.
- Use `@upstash/workflow` for multi-step tasks that exceed serverless time limits.
- Enable read replicas for read-heavy workloads; writes go to the primary region.
