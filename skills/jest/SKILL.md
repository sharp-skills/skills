---
name: jest
description: Work with jest — integrate, configure, and automate. Use when asked to set up jest, use jest API, integrate jest into a project, troubleshoot jest errors, or build jest automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [jest]
---

# Jest Skill

## Quick Start

```bash
pip install jest
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('jest');
```

## When to Use
Use this skill when asked to:
- Set up jest
- Integrate jest API
- Configure jest authentication
- Troubleshoot jest errors
- Build automation with jest

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
- Docs: https://jest.com/docs
- GitHub: https://github.com/jest
