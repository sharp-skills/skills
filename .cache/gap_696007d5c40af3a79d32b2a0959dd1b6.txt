---
name: hono
description: >-
  Assists with building APIs and web applications using Hono, an ultrafast web framework
  that runs on Cloudflare Workers, Deno, Bun, Vercel, AWS Lambda, and Node.js. Use when
  creating edge-first APIs, configuring middleware, or setting up type-safe RPC clients.
  Trigger words: hono, edge framework, web framework, hono routing, hono middleware.
license: Apache-2.0
compatibility: "Runs on Cloudflare Workers, Deno, Bun, Node.js, AWS Lambda, Vercel"
metadata:
  author: terminal-skills
  version: "1.0.0"
  category: development
  tags: ["hono", "web-framework", "edge", "api", "typescript"]
---

# Hono

## Overview

Hono is a lightweight, ultrafast web framework built on Web Standards that runs across multiple runtimes including Cloudflare Workers, Deno, Bun, and Node.js. It provides expressive routing, a rich middleware ecosystem, and type-safe RPC capabilities for building performant APIs and web applications.

## Instructions

- When creating a new API, set up routing with `app.get()`, `app.post()`, etc., and organize routes into modular sub-routers using `app.route()`.
- When adding middleware, use built-in options like `cors()`, `logger()`, `secureHeaders()` globally with `app.use("*", ...)` and scope auth middleware to protected paths.
- When handling requests, use the Context API: `c.req.param()` for path params, `c.req.query()` for query strings, `c.req.json()` for body parsing, and `c.json()` for responses.
- When validating input, integrate `@hono/zod-validator` with `zValidator("json", schema)` for request body, query, and param validation with type inference.
- When building type-safe clients, use Hono's RPC mode with `hc<AppType>(baseUrl)` to generate a typed HTTP client from route definitions without code generation.
- When deploying to Cloudflare Workers, type environment bindings with `new Hono<{ Bindings: Env }>()` and use `c.executionCtx.waitUntil()` for background tasks.
- When rendering HTML, use Hono's built-in JSX runtime (`hono/jsx`) for lightweight server-side rendering without React.
- When writing tests, call `app.request("/path")` directly to test routes as pure functions without an HTTP server.

## Examples

### Example 1: Build a REST API with validation

**User request:** "Create a Hono API with user CRUD endpoints and Zod validation"

**Actions:**
1. Initialize Hono app with typed environment bindings
2. Define Zod schemas for user creation and update payloads
3. Create route handlers with `zValidator("json", schema)` middleware
4. Group routes with `app.route("/api/users", userRouter)`

**Output:** A type-safe REST API with validated inputs and proper HTTP status codes.

### Example 2: Deploy a multi-runtime API

**User request:** "Set up a Hono API that works on both Cloudflare Workers and Node.js"

**Actions:**
1. Create shared Hono app with routes and middleware
2. Configure Cloudflare Workers entry with `export default app`
3. Add Node.js entry using `@hono/node-server` adapter
4. Set up environment-specific binding types

**Output:** A portable API deployable to multiple runtimes with shared route logic.

## Guidelines

- Use `new Hono<{ Bindings: Env }>()` to type environment bindings on Cloudflare.
- Group related routes into separate files and merge with `app.route()`.
- Apply global middleware with `app.use("*", middleware)` and scope auth to protected paths.
- Use `@hono/zod-validator` for all user input; never trust raw request data.
- Return proper HTTP status codes: 201 for creation, 204 for deletion, 4xx for client errors.
- Prefer Hono's RPC mode over manual fetch calls for internal service communication.
