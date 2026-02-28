---
name: hono
description: Work with hono — integrate, configure, and automate. Use when asked to set up hono, use hono API, integrate hono into a project, troubleshoot hono errors, or build hono automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [hono]
---

# Hono Skill

## Quick Start

```bash
npm install hono
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('hono');
```

## When to Use
Use this skill when asked to:
- Set up hono
- Integrate hono API
- Configure hono authentication
- Troubleshoot hono errors
- Build automation with hono

## Core Patterns

### Pattern 1: Basic Usage (Source: official)
```javascript
// TODO: Set ANTHROPIC_API_KEY for AI-generated patterns from official docs
```

## Production Notes

Set `ANTHROPIC_API_KEY` in `.env` for AI-generated production notes from real GitHub Issues data.

## Failure Modes
| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| Auth error | Invalid API key | Check environment variable |
| Timeout | Network issue | Add retry with backoff |

## Pre-Deploy Checklist
- [ ] API key set in production environment
- [ ] Error handling on all API calls
- [ ] Rate limiting / retry logic added

## Resources
- Docs: https://hono.com/docs
- GitHub: https://github.com/hono
