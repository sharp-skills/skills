---
name: vitest
description: Work with vitest — integrate, configure, and automate. Use when asked to set up vitest, use vitest API, integrate vitest into a project, troubleshoot vitest errors, or build vitest automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [vitest]
---

# Vitest Skill

## Quick Start

```bash
pip install vitest
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('vitest');
```

## When to Use
Use this skill when asked to:
- Set up vitest
- Integrate vitest API
- Configure vitest authentication
- Troubleshoot vitest errors
- Build automation with vitest

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
- Docs: https://vitest.com/docs
- GitHub: https://github.com/vitest
