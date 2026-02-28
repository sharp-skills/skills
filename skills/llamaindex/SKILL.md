---
name: llamaindex
description: Work with llamaindex — integrate, configure, and automate. Use when asked to set up llamaindex, use llamaindex API, integrate llamaindex into a project, troubleshoot llamaindex errors, or build llamaindex automation.
license: Apache-2.0
compatibility:
- python >= 3.9
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [llamaindex, python, pip]
---

# Llamaindex Skill

## Quick Start

```bash
npm install llamaindex
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('llamaindex');
```

## When to Use
Use this skill when asked to:
- Set up llamaindex
- Integrate llamaindex API
- Configure llamaindex authentication
- Troubleshoot llamaindex errors
- Build automation with llamaindex

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
- Docs: https://llamaindex.com/docs
- GitHub: https://github.com/llamaindex
