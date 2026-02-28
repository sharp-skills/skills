---
name: turso
description: Work with turso — integrate, configure, and automate. Use when asked to set up turso, use turso API, integrate turso into a project, troubleshoot turso errors, or build turso automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [turso]
---

# Turso Skill

## Quick Start

```bash
npm install turso
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('turso');
```

## When to Use
Use this skill when asked to:
- Set up turso
- Integrate turso API
- Configure turso authentication
- Troubleshoot turso errors
- Build automation with turso

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
- Docs: https://turso.com/docs
- GitHub: https://github.com/turso
