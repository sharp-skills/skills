---
name: nextjs
description: Work with nextjs — integrate, configure, and automate. Use when asked to set up nextjs, use nextjs API, integrate nextjs into a project, troubleshoot nextjs errors, or build nextjs automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [nextjs]
---

# Nextjs Skill

## Quick Start

```bash
npm install nextjs
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('nextjs');
```

## When to Use
Use this skill when asked to:
- Set up nextjs
- Integrate nextjs API
- Configure nextjs authentication
- Troubleshoot nextjs errors
- Build automation with nextjs

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
- Docs: https://nextjs.com/docs
- GitHub: https://github.com/nextjs
