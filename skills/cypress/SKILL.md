---
name: cypress
description: Work with cypress — integrate, configure, and automate. Use when asked to set up cypress, use cypress API, integrate cypress into a project, troubleshoot cypress errors, or build cypress automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [cypress, api, automation, integration, testing, qa]
---

# Cypress Skill

## Quick Start

```bash
npm install cypress
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('cypress');
```

## When to Use
Use this skill when asked to:
- Set up cypress
- Integrate cypress API
- Configure cypress authentication
- Troubleshoot cypress errors
- Build automation with cypress

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
- Docs: https://cypress.com/docs
- GitHub: https://github.com/cypress
