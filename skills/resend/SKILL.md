---
name: resend
description: Work with resend — integrate, configure, and automate. Use when asked to set up resend, use resend API, integrate resend into a project, troubleshoot resend errors, or build resend automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [resend, api, automation, integration]
---

# Resend Skill

## Quick Start

```bash
pip install resend
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('resend');
```

## When to Use
Use this skill when asked to:
- Set up resend
- Integrate resend API
- Configure resend authentication
- Troubleshoot resend errors
- Build automation with resend

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
- Docs: https://resend.com/docs
- GitHub: https://github.com/resend
