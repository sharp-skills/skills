---
name: winston
description: Work with winston — integrate, configure, and automate. Use when asked to set up winston, use winston API, integrate winston into a project, troubleshoot winston errors, or build winston automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [winston, api, automation, integration]
---

# Winston Skill

## Quick Start

```bash
pip install winston
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('winston');
```

## When to Use
Use this skill when asked to:
- Set up winston
- Integrate winston API
- Configure winston authentication
- Troubleshoot winston errors
- Build automation with winston

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
- Docs: https://winston.com/docs
- GitHub: https://github.com/winston
