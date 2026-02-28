---
name: eslint
description: Work with eslint — integrate, configure, and automate. Use when asked to set up eslint, use eslint API, integrate eslint into a project, troubleshoot eslint errors, or build eslint automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [eslint, api, automation, integration]
---

# Eslint Skill

## Quick Start

```bash
npm install eslint
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('eslint');
```

## When to Use
Use this skill when asked to:
- Set up eslint
- Integrate eslint API
- Configure eslint authentication
- Troubleshoot eslint errors
- Build automation with eslint

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
- Docs: https://eslint.com/docs
- GitHub: https://github.com/eslint
