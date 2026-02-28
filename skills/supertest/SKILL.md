---
name: supertest
description: Work with supertest — integrate, configure, and automate. Use when asked to set up supertest, use supertest API, integrate supertest into a project, troubleshoot supertest errors, or build supertest automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [supertest]
---

# Supertest Skill

## Quick Start

```bash
pip install supertest
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('supertest');
```

## When to Use
Use this skill when asked to:
- Set up supertest
- Integrate supertest API
- Configure supertest authentication
- Troubleshoot supertest errors
- Build automation with supertest

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
- Docs: https://supertest.com/docs
- GitHub: https://github.com/supertest
