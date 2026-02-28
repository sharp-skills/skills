---
name: express
description: >-
  Build Node.js web servers and REST APIs with Express.js. Use when asked to:
  create an Express server, add REST API routes, set up Express middleware,
  handle authentication with Express, build CRUD API, add error handling to
  Express, set up CORS, implement rate limiting, use Express with TypeScript.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.1.0
  category: development
  tags: [express, nodejs, javascript, rest-api, http, middleware, backend]
trace_id: 7701899b0867
generated_at: '2026-02-28T22:43:25'
generator: sharpskill-v1.0 (legacy)
---

# Express.js

Express is the de facto standard Node.js web framework — minimal, fast, flexible.
Use for REST APIs, web servers, and backend services.

## Installation

```bash
npm install express
npm install -D @types/express
```

## Basic Server

```javascript
// app.js
const express = require('express');
const app = express();

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// 404
app.use((req, res) => res.status(404).json({ error: 'Not found' }));

// Error handler (must be last, 4 args)
app.use((err, req, res, next) => {
  res.status(err.status || 500).json({ error: err.message || 'Internal error' });
});

module.exports = app;
```

```javascript
// index.js
const app = require('./app');
app.listen(process.env.PORT || 3000, () => console.log('Server started'));
```

## REST Router

```javascript
// routes/users.js
const router = require('express').Router();
let users = [{ id: 1, name: 'Alice', email: 'alice@example.com' }];
let nextId = 2;

router.get('/',      (req, res) => res.json(users));
router.get('/:id',   (req, res, next) => {
  const user = users.find(u => u.id === +req.params.id);
  if (!user) return next({ status: 404, message: 'User not found' });
  res.json(user);
});
router.post('/',     (req, res, next) => {
  const { name, email } = req.body;
  if (!name || !email) return next({ status: 400, message: 'name and email required' });
  const user = { id: nextId++, name, email };
  users.push(user);
  res.status(201).json(user);
});
router.put('/:id',   (req, res, next) => {
  const i = users.findIndex(u => u.id === +req.params.id);
  if (i === -1) return next({ status: 404, message: 'User not found' });
  users[i] = { ...users[i], ...req.body, id: users[i].id };
  res.json(users[i]);
});
router.delete('/:id',(req, res, next) => {
  const i = users.findIndex(u => u.id === +req.params.id);
  if (i === -1) return next({ status: 404, message: 'User not found' });
  users.splice(i, 1);
  res.status(204).send();
});

module.exports = router;
```

```javascript
// In app.js
app.use('/api/users', require('./routes/users'));
```

## Auth Middleware

```javascript
// middleware/auth.js
const jwt = require('jsonwebtoken');

function authenticate(req, res, next) {
  const auth = req.headers.authorization;
  if (!auth?.startsWith('Bearer ')) return res.status(401).json({ error: 'Missing token' });
  try {
    req.user = jwt.verify(auth.slice(7), process.env.JWT_SECRET);
    next();
  } catch {
    res.status(401).json({ error: 'Invalid token' });
  }
}

module.exports = { authenticate };
```

## CORS + Rate Limiting + Helmet

```bash
npm install cors express-rate-limit helmet
```

```javascript
const cors      = require('cors');
const rateLimit = require('express-rate-limit');
const helmet    = require('helmet');

app.use(helmet());
app.use(cors({ origin: process.env.ALLOWED_ORIGINS?.split(','), credentials: true }));
app.use('/api/', rateLimit({ windowMs: 15 * 60 * 1000, max: 100 }));
```

## Examples

**Example 1: File upload**
User: "Add file upload to my Express API"

```bash
npm install multer
```

```javascript
const multer = require('multer');
const upload = multer({ dest: 'uploads/', limits: { fileSize: 5 * 1024 * 1024 } });

router.post('/upload', upload.single('file'), (req, res) => {
  res.json({ filename: req.file.filename, size: req.file.size });
});
```

**Example 2: Async route with error forwarding**
User: "Handle async errors in Express routes"

```javascript
router.get('/users/:id', async (req, res, next) => {
  try {
    const user = await db.users.findById(req.params.id);
    if (!user) return next({ status: 404, message: 'Not found' });
    res.json(user);
  } catch (err) {
    next(err);
  }
});
```

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `Cannot GET /path` | Route not registered | Check `app.use()` order and path prefix |
| Body is `undefined` | Missing `express.json()` | Add before routes |
| CORS errors | Missing CORS headers | Add `cors()` before routes |
| Error handler not called | Missing `next(err)` | Use `next(err)` not `throw` in async routes |

## Pre-Deploy Checklist

- [ ] All async routes use `try/catch` + `next(err)`
- [ ] `helmet()` middleware enabled
- [ ] Rate limiting on public endpoints
- [ ] CORS `origin` restricted (not `*`)
- [ ] `process.env.PORT` used (not hardcoded)
- [ ] Health check at `/health`
