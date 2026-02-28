---
name: zustand
description: Work with zustand — integrate, configure, and automate. Use when asked to set up zustand, use zustand API, integrate zustand into a project, troubleshoot zustand errors, or build zustand automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [zustand, api, automation, integration]
---

# Zustand Skill

## Quick Start

```bash
npm install zustand
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('zustand');
```

## When to Use
Use this skill when asked to:
- Set up zustand
- Integrate zustand API
- Configure zustand authentication
- Troubleshoot zustand errors
- Build automation with zustand

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
- Docs: https://zustand.com/docs
- GitHub: https://github.com/zustand
