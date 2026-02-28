---
name: memcached
description: Work with memcached — integrate, configure, and automate. Use when asked to set up memcached, use memcached API, integrate memcached into a project, troubleshoot memcached errors, or build memcached automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [memcached]
---

# Memcached Skill

## Quick Start

```bash
npm install memcached
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('memcached');
```

## When to Use
Use this skill when asked to:
- Set up memcached
- Integrate memcached API
- Configure memcached authentication
- Troubleshoot memcached errors
- Build automation with memcached

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
- Docs: https://memcached.com/docs
- GitHub: https://github.com/memcached
