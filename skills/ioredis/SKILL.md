---
name: ioredis
description: Work with ioredis — integrate, configure, and automate. Use when asked to set up ioredis, use ioredis API, integrate ioredis into a project, troubleshoot ioredis errors, or build ioredis automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [ioredis]
---

# Ioredis Skill

## Quick Start

```bash
npm install ioredis
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('ioredis');
```

## When to Use
Use this skill when asked to:
- Set up ioredis
- Integrate ioredis API
- Configure ioredis authentication
- Troubleshoot ioredis errors
- Build automation with ioredis

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
- Docs: https://ioredis.com/docs
- GitHub: https://github.com/ioredis
