---
name: plaid
description: Work with plaid — integrate, configure, and automate. Use when asked to set up plaid, use plaid API, integrate plaid into a project, troubleshoot plaid errors, or build plaid automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [plaid, api, automation, integration]
---

# Plaid Skill

## Quick Start

```bash
pip install plaid
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('plaid');
```

## When to Use
Use this skill when asked to:
- Set up plaid
- Integrate plaid API
- Configure plaid authentication
- Troubleshoot plaid errors
- Build automation with plaid

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
- Docs: https://plaid.com/docs
- GitHub: https://github.com/plaid
