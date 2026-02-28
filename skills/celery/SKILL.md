---
name: celery
description: Work with celery — integrate, configure, and automate. Use when asked to set up celery, use celery API, integrate celery into a project, troubleshoot celery errors, or build celery automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [celery]
---

# Celery Skill

## Quick Start

```bash
pip install celery
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('celery');
```

## When to Use
Use this skill when asked to:
- Set up celery
- Integrate celery API
- Configure celery authentication
- Troubleshoot celery errors
- Build automation with celery

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
- Docs: https://celery.com/docs
- GitHub: https://github.com/celery
