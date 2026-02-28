---
name: sentry
description: Work with sentry — integrate, configure, and automate. Use when asked to set up sentry, use sentry API, integrate sentry into a project, troubleshoot sentry errors, or build sentry automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [sentry]
---

# Sentry Skill

## Quick Start

```bash
pip install sentry
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('sentry');
```

## When to Use
Use this skill when asked to:
- Set up sentry
- Integrate sentry API
- Configure sentry authentication
- Troubleshoot sentry errors
- Build automation with sentry

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
- Docs: https://sentry.com/docs
- GitHub: https://github.com/sentry
