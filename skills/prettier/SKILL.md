---
name: prettier
description: Work with prettier — integrate, configure, and automate. Use when asked to set up prettier, use prettier API, integrate prettier into a project, troubleshoot prettier errors, or build prettier automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [prettier]
---

# Prettier Skill

## Quick Start

```bash
pip install prettier
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('prettier');
```

## When to Use
Use this skill when asked to:
- Set up prettier
- Integrate prettier API
- Configure prettier authentication
- Troubleshoot prettier errors
- Build automation with prettier

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
- Docs: https://prettier.com/docs
- GitHub: https://github.com/prettier
