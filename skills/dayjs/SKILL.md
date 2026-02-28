---
name: dayjs
description: Work with dayjs — integrate, configure, and automate. Use when asked to set up dayjs, use dayjs API, integrate dayjs into a project, troubleshoot dayjs errors, or build dayjs automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [dayjs, api, automation, integration]
---

# Dayjs Skill

## Quick Start

```bash
npm install dayjs
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('dayjs');
```

## When to Use
Use this skill when asked to:
- Set up dayjs
- Integrate dayjs API
- Configure dayjs authentication
- Troubleshoot dayjs errors
- Build automation with dayjs

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
- Docs: https://dayjs.com/docs
- GitHub: https://github.com/dayjs
