---
name: rate-limiter-flexible
description: Work with rate-limiter-flexible — integrate, configure, and automate. Use when asked to set up rate-limiter-flexible, use rate-limiter-flexible API, integrate rate-limiter-flexible into a project, troubleshoot rate-limiter-flexible errors, or build rate-limiter-flexible automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [rate-limiter-flexible, javascript, nodejs, npm]
---

# Rate-Limiter-Flexible Skill

## Quick Start

```bash
npm install rate-limiter-flexible
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('rate-limiter-flexible');
```

## When to Use
Use this skill when asked to:
- Set up rate-limiter-flexible
- Integrate rate-limiter-flexible API
- Configure rate-limiter-flexible authentication
- Troubleshoot rate-limiter-flexible errors
- Build automation with rate-limiter-flexible

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
- Docs: https://rate-limiter-flexible.com/docs
- GitHub: https://github.com/rate-limiter-flexible
