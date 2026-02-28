/**
 * Hono — executable skill module
 * Auto-extracted by SharpSkill v2.6.0 from SKILL.md
 *
 * import { createClient } from './index';
 */

import { Hono } from 'hono'
import { serve } from '@hono/node-server' // For Node.js runtime
import { logger } from 'hono/logger'
import { z } from 'zod' // For robust input validation
import { zValidator } from '@hono/zod-validator'
export default app // Export for use with platform adapters

// ── Core Implementation ──────────────────────────────────────

// src/index.ts

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

// src/app.ts

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
