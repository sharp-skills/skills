---
name: hono
description: Hono is a lightweight, blazing fast web framework for the Edge, compatible
  with Cloudflare Workers, Deno, Bun, and Node.js. Use this skill when building high-performance
  APIs, serverless functions, or web applications on edge runtimes; asked to create
  a fast backend; need to deploy to Cloudflare Workers; want to use Bun or Deno for
  web development; or require a minimal API framework.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags:
  - hono
  - web-framework
  - edge
  - cloudflare-workers
  - bun
  - deno
  - node
  - api-development
---

# Hono Skill

## Quick Start
Install Hono and a platform adapter (e.g., `@hono/node-server` for Node.js, or use built-in support for Bun/Deno/Cloudflare Workers).

```bash
npm install hono @hono/node-server # For Node.js
# or bun add hono
# or deno add hono
```

Minimal "Hello World" application:
```typescript
// src/index.ts
import { Hono } from 'hono'
import { serve } from '@hono/node-server' // For Node.js runtime

const app = new Hono()

app.get('/', (c) => {
  return c.text('Hello Hono from the Edge!')
})

app.get('/api/status', (c) => {
  return c.json({ status: 'healthy', timestamp: new Date().toISOString() })
})

// For Node.js, start the server
const port = 3000
console.log(`Server running on http://localhost:${port}`)
serve({
  fetch: app.fetch,
  port
})
```

## When to Use
Use this skill when asked to:
- Create a fast, lightweight API or web application for edge runtimes.
- Develop serverless functions for platforms like Cloudflare Workers or Firebase Functions.
- Build a backend using Bun, Deno, or Node.js with minimal overhead.
- Implement high-performance routing and middleware.
- Need a framework optimized for low-latency responses.
- Integrate with modern JavaScript tooling and TypeScript.
- Set up API endpoints with robust error handling.
- Handle request validation and JSON responses efficiently.
- Deploy a web service to various JavaScript runtimes without significant code changes.

## Core Patterns

### Pattern 1: Routing, Middleware, and Request Parsing (Source: official)
Hono's routing is expressive, and middleware can be easily chained. This example demonstrates basic routing, a logger middleware, and parsing a JSON request body.

```typescript
// src/app.ts
import { Hono } from 'hono'
import { logger } from 'hono/logger'
import { z } from 'zod' // For robust input validation
import { zValidator } from '@hono/zod-validator'

const app = new Hono()

// Global middleware for logging requests
app.use('*', logger())

// Define a schema for the incoming request body
const userSchema = z.object({
  name: z.string().min(3),
  email: z.string().email(),
  age: z.number().int().positive().optional(),
})

// POST endpoint with request body validation
app.post(
  '/api/users',
  zValidator('json', userSchema, (result, c) => {
    if (!result.success) {
      return c.json({ error: 'Invalid data', issues: result.error.issues }, 400)
    }
  }),
  async (c) => {
    const data = c.req.valid('json')
    // In a real application, save 'data' to a database
    console.log('Received user data:', data)
    return c.json({ message: 'User created successfully', user: data }, 201)
  }
)

// GET endpoint with path parameters
app.get('/api/users/:id', (c) => {
  const id = c.req.param('id')
  // In a real application, fetch user by ID from a database
  if (id === '123') {
    return c.json({ id: '123', name: 'Alice', email: 'alice@example.com' })
  }
  return c.json({ error: 'User not found' }, 404)
})

export default app // Export for use with platform adapters
```

### Pattern 2: Robust Error Handling and Classification (Source: community / GitHub Issues)
Implementing a global error handler is crucial for production applications. This pattern shows how to catch unhandled exceptions, classify them, and return consistent error responses, addressing common issues like `Response body object should not be disturbed or locked`.

```typescript
// src/error-handler.ts
import { Hono, Context } from 'hono'
import { HTTPException } from 'hono/http-exception'

const app = new Hono()

// Custom error handler for all routes
app.onError((err, c) => {
  if (err instanceof HTTPException) {
    // Handle Hono's built-in HTTP exceptions
    console.error(`HTTP Exception: ${err.status}