---
name: mailgun
description: Work with mailgun — integrate, configure, and automate. Use when asked to set up mailgun, use mailgun API, integrate mailgun into a project, troubleshoot mailgun errors, or build mailgun automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [mailgun]
---

# Mailgun Skill

## Quick Start

```bash
pip install mailgun
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('mailgun');
```

## When to Use
Use this skill when asked to:
- Set up mailgun
- Integrate mailgun API
- Configure mailgun authentication
- Troubleshoot mailgun errors
- Build automation with mailgun

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
- Docs: https://mailgun.com/docs
- GitHub: https://github.com/mailgun
