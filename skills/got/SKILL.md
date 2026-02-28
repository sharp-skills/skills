---
name: got
description: Work with got — integrate, configure, and automate. Use when asked to set up got, use got API, integrate got into a project, troubleshoot got errors, or build got automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [got, api, automation, integration]
---

# Got Skill

## Quick Start

```bash
pip install got
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('got');
```

## When to Use
Use this skill when asked to:
- Set up got
- Integrate got API
- Configure got authentication
- Troubleshoot got errors
- Build automation with got

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
- Docs: https://got.com/docs
- GitHub: https://github.com/got
