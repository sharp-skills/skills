---
name: redis-streams
description: Work with redis-streams — integrate, configure, and automate. Use when asked to set up redis-streams, use redis-streams API, integrate redis-streams into a project, troubleshoot redis-streams errors, or build redis-streams automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [redis-streams]
---

# Redis-Streams Skill

## Quick Start

```bash
pip install redis-streams
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('redis-streams');
```

## When to Use
Use this skill when asked to:
- Set up redis-streams
- Integrate redis-streams API
- Configure redis-streams authentication
- Troubleshoot redis-streams errors
- Build automation with redis-streams

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
- Docs: https://redis-streams.com/docs
- GitHub: https://github.com/redis-streams
