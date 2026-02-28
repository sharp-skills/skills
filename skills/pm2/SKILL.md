---
name: pm2
description: Work with pm2 — integrate, configure, and automate. Use when asked to set up pm2, use pm2 API, integrate pm2 into a project, troubleshoot pm2 errors, or build pm2 automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [pm2, api, automation, integration]
---

# Pm2 Skill

## Quick Start

```bash
pip install pm2
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('pm2');
```

## When to Use
Use this skill when asked to:
- Set up pm2
- Integrate pm2 API
- Configure pm2 authentication
- Troubleshoot pm2 errors
- Build automation with pm2

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
- Docs: https://pm2.com/docs
- GitHub: https://github.com/pm2
