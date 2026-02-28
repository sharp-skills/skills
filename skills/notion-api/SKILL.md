---
name: notion-api
description: Work with notion-api — integrate, configure, and automate. Use when asked to set up notion-api, use notion-api API, integrate notion-api into a project, troubleshoot notion-api errors, or build notion-api automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [notion-api, javascript, nodejs, npm]
---

# Notion-Api Skill

## Quick Start

```bash
pip install notion-api
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('notion-api');
```

## When to Use
Use this skill when asked to:
- Set up notion-api
- Integrate notion-api API
- Configure notion-api authentication
- Troubleshoot notion-api errors
- Build automation with notion-api

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
- Docs: https://notion-api.com/docs
- GitHub: https://github.com/notion-api
